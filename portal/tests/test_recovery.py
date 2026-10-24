import copy
import json
from pathlib import Path
import tempfile
import threading
import time
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from django.test import SimpleTestCase, override_settings
from portal.store import Store, StateError, validate
from portal.recovery import export_data, import_data
from portal.auth import identity
from .test_telemetry import raw
from portal.telemetry import normalize


class RecoveryTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings_context = override_settings(STATE_DIR=Path(self.tmp.name), SECRET_KEY='synthetic-recovery-key', STATE_KEY_ERROR=False)
        self.settings_context.enable()
        self.addCleanup(self.settings_context.disable)
        self.store = Store()
        self.data = {'owner': None, 'login': {}, 'profiles': {'one': {'id': 'one', 'name': 'Norte', 'connected': False,
            'metadata': {'*1|198.51.100.20': {'alias': 'Alias', 'notes': 'Nota conservada'}},
            'automatic': {'enabled': True, 'interval': 15}, 'history': [normalize(raw(), time.time())]}}}
        self.store.update(lambda d: d.update(copy.deepcopy(self.data)))
        session = self.client.session
        session['desktop'] = identity()
        session.save()
        self.client.cookies['spicyops_portal'] = session.session_key

    def test_corruption_and_truncation_have_recovery_ui_and_no_overwrite(self):
        for content in (b'broken', self.store.path.read_bytes()[:40]):
            self.store.path.write_bytes(content)
            with self.assertRaises(StateError): self.store.update(lambda d: d.clear())
            self.assertEqual(self.store.path.read_bytes(), content)
            response = self.client.get('/')
            self.assertContains(response, 'Respaldos y recuperación')
            self.assertContains(response, 'archivo dañado')
            self.assertEqual(self.store.path.read_bytes(), content)

    def test_portable_wrong_password_incompatible_and_invalid_structure_are_immutable(self):
        content = export_data(self.store.read(), 'una-contraseña-sintética')
        original = self.store.path.read_bytes()
        for candidate, password in ((content, 'otra-contraseña-incorrecta'), (content[:-32], 'una-contraseña-sintética'),
                                    (content.replace(b'PORTABLE-1', b'PORTABLE-2'), 'una-contraseña-sintética')):
            with self.assertRaises(StateError): import_data(candidate, password)
            self.assertEqual(self.store.path.read_bytes(), original)
        for data in ({'format': 2, 'profiles': {}}, {'profiles': []}, {'profiles': {'one': {'id': 'wrong'}}}):
            with self.assertRaises(StateError): self.store.restore(data)
        self.assertEqual(self.store.path.read_bytes(), original)
        self.assertNotIn(b'Nota conservada', content)

    def test_restore_preserves_original_and_all_data_across_keys(self):
        content = export_data(self.store.read(), 'una-contraseña-sintética')
        self.store.update(lambda d: d['profiles']['one']['metadata'].clear())
        damaged = b'original-truncado'
        self.store.path.write_bytes(damaged)
        with override_settings(SECRET_KEY='different-account-synthetic-key'):
            target = Store()
            archive = target.restore(import_data(content, 'una-contraseña-sintética'))
            restored = target.read()
        self.assertEqual(restored['profiles'], self.data['profiles'] | {'one': self.data['profiles']['one'] | {'operation_active': False, 'busy_until': 0, 'automatic': self.data['profiles']['one']['automatic'] | {'next_at': None}}})
        self.assertEqual((self.store.path.parent / archive / 'connections.enc').read_bytes(), damaged)

    def test_legacy_migration_keeps_payload_and_original_backup(self):
        original = self.store.cipher.encrypt(json.dumps(self.data).encode())
        self.store.path.write_bytes(original)
        self.store.update(lambda d: None)
        self.assertEqual(self.store.read()['format'], 1)
        self.assertEqual(self.store.read()['profiles'], self.data['profiles'])
        backups = list((self.store.path.parent / 'backups').glob('*.enc'))
        self.assertEqual(backups[0].read_bytes(), original)

    def test_rotation_and_storage_failure_preserve_current(self):
        import os
        for i in range(9):
            for file in (self.store.path.parent / 'backups').glob('*.enc'):
                os.utime(file, (0, 0))
            self.store.update(lambda d: d.update(owner=str(i)))
        files = list((self.store.path.parent / 'backups').glob('*.enc'))
        self.assertEqual(len(files), 5)
        for file in files: self.store.decode(file.read_bytes())
        before = self.store.path.read_bytes()
        with patch('portal.store.os.replace', side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError): self.store.update(lambda d: d.update(owner='lost'))
        self.assertEqual(before, self.store.path.read_bytes())

    def test_active_operation_blocks_restore_and_unconfirmed_ui_does_not_change_state(self):
        self.store.update(lambda d: d['profiles']['one'].update(operation_active=True))
        before = self.store.path.read_bytes()
        with self.assertRaises(StateError): self.store.restore(self.data)
        self.assertEqual(before, self.store.path.read_bytes())
        self.client.post('/respaldo/', {'action': 'restore'})
        self.assertEqual(before, self.store.path.read_bytes())

    def test_parallel_writes_do_not_lose_localities_or_notes(self):
        def change(i):
            Store().update(lambda d: d['profiles']['one']['metadata'].update({str(i): {'notes': str(i)}}))
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(change, range(20)))
        self.assertEqual(len(self.store.read()['profiles']['one']['metadata']), 21)

    def test_local_restore_and_key_error_page(self):
        self.store.update(lambda d: d.update(owner='changed'))
        backup = next((self.store.path.parent / 'backups').glob('*.enc'))
        self.store.path.write_bytes(b'corrupt')
        response = self.client.post('/respaldo/', {'action': 'restore', 'backup': backup.name, 'confirmed': 'yes'})
        self.assertContains(response, 'Restauración completada')
        self.assertEqual(self.store.read()['profiles'], self.data['profiles'] | {'one': self.data['profiles']['one'] | {'operation_active': False, 'busy_until': 0, 'automatic': self.data['profiles']['one']['automatic'] | {'next_at': None}}})
        with override_settings(STATE_KEY_ERROR=True):
            self.assertContains(self.client.get('/'), 'clave de esta cuenta Windows')


    def test_future_portable_and_semantic_corruption_rejected(self):
        import base64
        from portal.recovery import portable_key
        salt = b'0123456789abcdef'
        future = dict(self.data, format=999)
        token = portable_key('contraseña-sintética-123', salt).encrypt(json.dumps(future).encode())
        content = b'SPICYOPS-PORTABLE-1\n' + base64.urlsafe_b64encode(salt) + b'\n' + token
        before = self.store.path.read_bytes()
        with self.assertRaisesRegex(StateError, 'incompatible'): import_data(content, 'contraseña-sintética-123')
        for change in ('uptime', 'clients'):
            malformed = copy.deepcopy(self.data)
            malformed['profiles']['one']['history'][0][change] = 'invalid'
            with self.assertRaises(StateError): self.store.restore(malformed)
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_backup_byte_budget_and_hourly_limit(self):
        import os
        with patch('portal.store.BACKUP_BYTES', self.store.path.stat().st_size * 2 + 100):
            for i in range(4):
                for file in (self.store.path.parent / 'backups').glob('*.enc'): os.utime(file, (0, 0))
                self.store.update(lambda d: d.update(owner=str(i)))
            files = list((self.store.path.parent / 'backups').glob('*.enc'))
            self.assertLessEqual(sum(p.stat().st_size for p in files), self.store.path.stat().st_size * 2 + 100)
            self.assertLessEqual(len(files), 2)
        before = set((self.store.path.parent / 'backups').glob('*.enc'))
        self.store.update(lambda d: d.update(owner='same-hour'))
        self.assertEqual(before, set((self.store.path.parent / 'backups').glob('*.enc')))

    def test_restore_blocks_during_request_or_coordinator_operation(self):
        from portal.store import operation
        before = self.store.path.read_bytes()
        with operation():
            with self.assertRaisesRegex(StateError, 'operaciones'): self.store.restore(self.data)
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_disk_failure_during_restore_preserves_original_and_current(self):
        from portal.store import atomic
        before = self.store.path.read_bytes()
        def fail_current(path, content):
            if path == self.store.path: raise OSError('synthetic full disk')
            return atomic(path, content)
        with patch('portal.store.atomic', side_effect=fail_current):
            with self.assertRaises(OSError): self.store.restore(self.data)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertTrue(any((p/'connections.enc').read_bytes() == before for p in self.store.path.parent.glob('original-*')))

    def test_failed_key_recovery_rolls_back_key(self):
        from portal.store import atomic
        key = self.store.path.parent / 'secret.dpapi'
        key.write_bytes(b'synthetic-damaged-key')
        before = self.store.path.read_bytes()
        def fail_current(path, content):
            if path == self.store.path: raise OSError('synthetic full disk')
            return atomic(path, content)
        with override_settings(STATE_KEY_ERROR=True), patch('portal.secret.dpapi', return_value=b'synthetic-replacement'), patch('portal.store.atomic', side_effect=fail_current):
            with self.assertRaises(OSError): self.store.restore(self.data)
        self.assertEqual(key.read_bytes(), b'synthetic-damaged-key')
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_recovery_requires_local_session_and_csrf(self):
        from django.test import Client
        self.assertEqual(Client().get('/respaldo/').status_code, 401)
        self.assertEqual(self.client.get('/respaldo/', REMOTE_ADDR='198.51.100.1').status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.cookies = self.client.cookies
        self.assertEqual(client.post('/respaldo/', {'action': 'export', 'password': 'contraseña-sintética'}).status_code, 403)

    def test_background_storage_failure_is_visible(self):
        with patch('portal.store.os.replace', side_effect=OSError('synthetic write failure')):
            with self.assertRaises(OSError): self.store.update(lambda d: d.update(owner='lost'))
        self.assertContains(self.client.get('/'), 'Los últimos cambios pueden no estar guardados')
        self.store.update(lambda d: None)
        self.assertNotContains(self.client.get('/'), 'Los últimos cambios pueden no estar guardados')
