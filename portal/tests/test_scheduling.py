from pathlib import Path
import threading
from unittest.mock import patch

from django.test import Client, SimpleTestCase
from portal.connector import ConnectionFailure
from portal.scheduling import Coordinator, auto_context, locality_lock
from portal.store import Store
from portal.views import refresh_profile
from . import test_app
from .test_telemetry import raw


class SchedulingTests(SimpleTestCase):
    setUp = test_app.AppTests.setUp
    profile = test_app.AppTests.profile

    def coordinator(self, **kwargs):
        self.now = 10000
        coordinator = Coordinator(refresh_profile, clock=lambda: self.now, **kwargs)
        self.addCleanup(coordinator.stop)
        return coordinator

    def enable(self, key='one', interval=5):
        self.client.post(f'/conexiones/{key}/automatica/', {'enabled': 'on', 'interval': interval})

    def complete(self, coordinator):
        for future in list(coordinator.pending.values()):
            future.result(timeout=5)

    def test_defaults_validation_pause_persistence_and_restart(self):
        original = self.profile()
        self.assertEqual(auto_context(original)['interval'], 5)
        self.assertFalse(auto_context(original)['enabled'])
        self.assertContains(self.client.get('/conexiones/'), 'Actualización automática')
        for interval in (1, 5, 10, 15, 30, 60):
            self.enable(interval=interval)
            self.assertEqual(Store().read()['profiles']['one']['automatic']['interval'], interval)
        self.assertEqual(self.client.post('/conexiones/one/automatica/', {'interval': 2}).status_code, 400)
        coordinator = self.coordinator()
        coordinator.prepare()
        saved = Store().read()['profiles']['one']
        self.assertEqual(saved['automatic']['next_at'], self.now+3600)
        self.assertEqual(saved['history'], original['history'])
        self.client.post('/conexiones/one/automatica/', {'interval': 5})
        coordinator.prepare()
        saved = Store().read()['profiles']['one']
        self.assertIsNone(saved['automatic']['next_at'])
        self.assertFalse(saved['automatic']['enabled'])
        self.assertEqual(saved['ssh_password'], original['ssh_password'])
        self.assertEqual(saved['history'], original['history'])
        self.assertNotIn(b'test-only-ssh', (Path(self.temp.name)/'connections.enc').read_bytes())
        self.assertEqual(Client().post('/conexiones/one/automatica/', {}).status_code, 401)
        csrf = Client(enforce_csrf_checks=True)
        csrf.cookies = self.client.cookies
        self.assertEqual(csrf.post('/conexiones/one/automatica/', {}).status_code, 403)

    @patch('portal.views.collect', return_value=raw())
    def test_due_once_no_catchup_manual_reschedules_and_read_only(self, reader):
        self.profile()
        self.enable()
        coordinator = self.coordinator()
        coordinator.prepare()
        self.now += 36000  # Se perdió más de un ciclo.
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            coordinator.tick()
            self.complete(coordinator)
            coordinator.tick()
            self.assertEqual(reader.call_count, 1)
            self.assertEqual(reader.call_args.kwargs, {})  # Ningún Morosos.
            self.assertEqual(Store().read()['profiles']['one']['automatic']['next_at'], self.now+300)
            self.now += 200
            refresh_profile('one')
            self.assertEqual(Store().read()['profiles']['one']['automatic']['next_at'], self.now+300)
            coordinator.tick()
            self.assertEqual(reader.call_count, 2)

    @patch('portal.views.collect')
    def test_errors_backoff_capped_recovery_preserves_history_and_metadata(self, reader):
        original = self.profile()
        self.client.post('/clientes/one/*1/datos/', {'alias': 'Conservar'})
        self.enable(interval=1)
        coordinator = self.coordinator()
        coordinator.prepare()
        reader.side_effect = ConnectionFailure('Fallo controlado')
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            for delay in (60, 120, 240, 900, 900):
                self.now = Store().read()['profiles']['one']['automatic']['next_at']
                coordinator.tick()
                self.complete(coordinator)
                saved = Store().read()['profiles']['one']
                self.assertEqual(saved['automatic']['next_at'], self.now+delay)
                self.assertEqual(saved['history'], original['history'])
                self.assertEqual(saved['last_error_at'], self.now)
                self.assertEqual(auto_context(saved)['status'], 'esperando reintento')
                count = reader.call_count
                coordinator.tick()
                self.assertEqual(reader.call_count, count)
            reader.side_effect = None
            reader.return_value = raw('200/400')
            self.now = saved['automatic']['next_at']
            coordinator.tick()
            self.complete(coordinator)
        saved = Store().read()['profiles']['one']
        self.assertEqual(len(saved['history']), 2)
        self.assertEqual(saved['last_error'], '')
        self.assertEqual(saved['automatic']['failures'], 0)
        self.assertEqual(saved['metadata']['*1|198.51.100.20']['alias'], 'Conservar')
        self.assertFalse(saved['operation_active'])

    @patch('portal.views.collect')
    def test_slow_locality_does_not_block_others_or_duplicate_expired_lease(self, reader):
        self.profile()
        self.profile('two')
        self.profile('three')
        for key in ('one', 'two', 'three'): self.enable(key)
        coordinator = self.coordinator()
        coordinator.prepare()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def collect(profile):
            if profile['id'] == 'one':
                entered.set()
                if not release.wait(5): raise AssertionError('No se liberó la lectura')
            return raw()
        reader.side_effect = collect
        self.now += 1000
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            coordinator.tick()
            self.assertTrue(entered.wait(2))
            self.assertLessEqual(len(coordinator.pending), 2)
            other = coordinator.pending.get('two')
            if other: other.result(timeout=2)
            # Incluso después del plazo heredado, el bloqueo real sigue vigente.
            self.now += 1000
            with self.assertRaises(ValueError): refresh_profile('one')
            self.client.post('/conexiones/one/desconectar/')
            self.client.post('/conexiones/one/automatica/', {'interval': 1})
            self.client.post('/conexiones/one/configurar/', self.payload)
            row = Store().read()['profiles']['one']['history'][-1]['clients'][0]
            self.client.post('/clientes/one/*1/morosidad/', {'confirmed': 'yes', 'action': 'suspend', 'fingerprint': row['fingerprint']})
            self.assertTrue(Store().read()['profiles']['one']['connected'])
            self.assertTrue(Store().read()['profiles']['one']['automatic']['enabled'])
            for _ in range(5): coordinator.tick()
            release.set()
            self.complete(coordinator)
        self.assertEqual(sum(call.args[0]['id'] == 'one' for call in reader.call_args_list), 1)
        self.assertTrue(all(not call.kwargs for call in reader.call_args_list))
        self.assertGreaterEqual(len(Store().read()['profiles']['two']['history']), 2)

    @patch('portal.views.collect', return_value=raw())
    def test_disconnect_cancels_due_work_restart_only_connected_enabled(self, reader):
        self.profile()
        self.profile('two')
        self.profile('three')
        self.enable()
        self.enable('two')
        coordinator = self.coordinator()
        coordinator.prepare()
        self.client.post('/conexiones/one/desconectar/')
        self.now += 1000
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            coordinator.tick()
            self.complete(coordinator)
        self.assertEqual([c.args[0]['id'] for c in reader.call_args_list], ['two'])
        coordinator.prepare()
        state = Store().read()['profiles']
        self.assertIsNone(state['one']['automatic']['next_at'])
        self.assertIsNone(state['three']['automatic']['next_at'])
        self.assertEqual(state['two']['automatic']['next_at'], self.now+300)

    def test_single_start_and_staggered_restart(self):
        for key in ('one', 'two', 'three'):
            self.profile(key)
            self.enable(key)
        coordinator = self.coordinator()
        coordinator.start()
        thread = coordinator.thread
        coordinator.start()
        self.assertIs(coordinator.thread, thread)
        values = sorted(p['automatic']['next_at'] for p in Store().read()['profiles'].values())
        self.assertEqual(values, [10300, 10303, 10306])
        coordinator.stop()
        self.assertFalse(thread.is_alive())

    @patch('portal.views.collect', return_value=raw())
    def test_configuration_locks_do_not_starve_another_locality(self, reader):
        for key in ('one', 'two', 'three'):
            self.profile(key)
            self.enable(key)
        coordinator = self.coordinator()
        coordinator.prepare()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def configure():
            with locality_lock('one'), locality_lock('three'):
                entered.set()
                release.wait(5)
        thread = threading.Thread(target=configure)
        thread.start()
        self.assertTrue(entered.wait(2))
        self.now += 1000
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            coordinator.tick()
            self.complete(coordinator)
        release.set()
        thread.join(3)
        self.assertEqual([call.args[0]['id'] for call in reader.call_args_list], ['two'])

    @patch('portal.views.collect')
    def test_headless_worker_shutdown_waits_for_persistence(self, reader):
        self.profile()
        self.enable(interval=1)
        coordinator = self.coordinator()
        coordinator.prepare()
        entered, release, stopped = threading.Event(), threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def collect(profile):
            entered.set()
            if not release.wait(5): raise AssertionError('No se liberó la lectura')
            return raw()
        reader.side_effect = collect
        self.now += 100
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            coordinator.tick()
            self.assertTrue(entered.wait(2))
            thread = threading.Thread(target=lambda: (coordinator.stop(), stopped.set()))
            thread.start()
            self.assertFalse(stopped.wait(.05))
            release.set()
            thread.join(3)
        self.assertTrue(stopped.is_set())
        self.assertEqual(len(Store().read()['profiles']['one']['history']), 2)
        self.assertFalse(Store().read()['profiles']['one']['operation_active'])
        count = reader.call_count
        self.now += 10000
        coordinator.tick()
        self.assertEqual(reader.call_count, count)

    @patch('portal.views.collect')
    def test_automatic_during_morosity_cannot_execute_until_write_finishes(self, reader):
        self.profile()
        self.enable()
        coordinator = self.coordinator()
        coordinator.prepare()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def collect(profile, **kwargs):
            if kwargs:
                entered.set()
                if not release.wait(5): raise AssertionError('No se liberó Morosos')
                result = raw()
                result['restrictions'] = [{'list': 'Morosos', 'address': '198.51.100.20', 'disabled': False}]
                return result
            return raw()
        reader.side_effect = collect
        row = Store().read()['profiles']['one']['history'][-1]['clients'][0]
        client = Client()
        client.cookies = self.client.cookies.copy()
        thread = threading.Thread(target=lambda: client.post('/clientes/one/*1/morosidad/',
            {'confirmed': 'yes', 'action': 'suspend', 'fingerprint': row['fingerprint']}))
        thread.start()
        self.assertTrue(entered.wait(2))
        self.now += 1000
        coordinator.tick()
        self.complete(coordinator)
        self.assertEqual(reader.call_count, 1)
        release.set()
        thread.join(3)
        self.assertFalse(thread.is_alive())
        with patch('portal.views.time.time', side_effect=lambda: self.now):
            coordinator.tick()
            self.complete(coordinator)
        self.assertEqual(reader.call_count, 2)
        self.assertEqual(reader.call_args.kwargs, {})

    def test_live_poll_does_not_consume_operator_notice_or_expose_access(self):
        self.profile()
        session = self.client.session
        session['notice'] = 'Conservar aviso'
        session.save()
        self.client.cookies['spicyops_portal'] = session.session_key
        response = self.client.get('/conexiones/', HTTP_X_SPICYOPS_LIVE='1')
        self.assertNotContains(response, 'test-only-ssh')
        self.assertNotContains(response, 'router_password')
        self.assertContains(response, 'data-live-revision')
        self.assertEqual(self.client.session['notice'], 'Conservar aviso')

    @patch('portal.views.collect')
    def test_notes_saved_during_configuration_are_not_overwritten(self, reader):
        self.profile()
        self.enable()
        def read(profile):
            Store().update(lambda d:d['profiles']['one']['metadata'].update(
                {'*1|198.51.100.20': {'alias': 'Editado durante la lectura'}}))
            return raw()
        reader.side_effect = read
        self.client.post('/conexiones/one/configurar/', self.payload)
        saved = Store().read()['profiles']['one']
        self.assertEqual(saved['metadata']['*1|198.51.100.20']['alias'], 'Editado durante la lectura')
        self.assertTrue(saved['automatic']['enabled'])
