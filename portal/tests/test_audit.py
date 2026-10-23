"""Regresiones de la auditoría: solo inventario sintético y loopback."""
import copy
import socket
import threading
import time
import subprocess
import sys
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from portal.connector import collect, ConnectionFailure, resolve_bounded
from portal.remote_reader import change_morosity, OperationRejected
from portal.router_contract import restriction_state, queue_identity
from portal.store import Store
from portal.telemetry import normalize, estimate_uptime, carry_counter_validity
from portal.scheduling import Coordinator
from .test_telemetry import raw
from .test_app import AppTests
from .test_connector import ssh_reader
from .test_morosity import MorosityTests


class RestrictionAuditTests(SimpleTestCase):
    def test_range_endpoints_cidr_and_individual_share_interpretation(self):
        for text in ('198.51.100.20', '198.51.100.20/32', '198.51.100.0/24',
                     '198.51.100.20-198.51.100.30', '198.51.100.10-198.51.100.20'):
            entries = [{'list': 'Morosos', 'address': text}]
            self.assertTrue(restriction_state(entries, '198.51.100.20')['active'])
            source = raw(); source['restrictions'] = entries
            self.assertTrue(normalize(source, 10000)['clients'][0]['restricted'])
        self.assertFalse(restriction_state([{'list': 'Morosos', 'address': '198.51.100.21-198.51.100.30'}],
                                          '198.51.100.20')['active'])

    def test_individual_plus_range_cannot_suspend_or_restore(self):
        api = MagicMock()
        for action in ('suspend', 'restore'):
            for text in ('198.51.100.20-198.51.100.30', '198.51.100.10-198.51.100.20',
                         '198.51.100.0/24', '198.51.100.20-198.51.100.20',
                         '198.51.100.30-198.51.100.20', 'dns.example.invalid', '::/0', ''):
                with self.subTest(action=action, address=text):
                    entries = [{'.id': '*A', 'list': 'Morosos', 'address': '198.51.100.20'},
                               {'.id': '*B', 'list': 'Morosos', 'address': text}]
                    operation = dict(id='*1', name='Abonado de test', ip='198.51.100.20', action=action, identity='Router de test')
                    with self.assertRaisesRegex(OperationRejected, 'restriction_ambiguous'):
                        change_morosity(api, raw()['queues'], entries, 'Router de test', operation)
        api.assert_not_called()

    def test_unknown_active_is_visible_and_disabled_shared_is_untouched(self):
        source = raw(); source['restrictions'] = [{'list': 'Morosos', 'address': 'dns.invalid'}]
        row = normalize(source, 1)['clients'][0]
        self.assertTrue(row['restriction_unknown'])
        self.assertIn('sin interpretar', row['status'])
        for field in ('dynamic', 'disabled'):
            entries = [{'list': 'Morosos', 'address': '198.51.100.20', field: True}]
            self.assertEqual(restriction_state(entries, row['ip'])['unsafe'], field == 'dynamic')

    def test_disabled_range_is_never_modified_and_dynamic_duplicates_fail_closed(self):
        op = dict(id='*1', name='Abonado de test', ip='198.51.100.20', action='suspend', identity='Router de test')
        entries = [{'.id': '*RANGE', 'list': 'Morosos', 'address': '198.51.100.20-198.51.100.30', 'disabled': True}]
        api = MagicMock(return_value=iter([]))
        change_morosity(api, raw()['queues'], entries, 'Router de test', op)
        self.assertEqual(api.call_args.args[0], '/ip/firewall/address-list/add')
        self.assertNotIn('.id', api.call_args.kwargs)
        self.assertTrue(entries[0]['disabled'])


class ConfirmationAuditTests(SimpleTestCase):
    setUp = MorosityTests.setUp
    command = MorosityTests.command
    writes = MorosityTests.writes
    def test_shared_or_unknown_appearing_after_write_is_uncertain(self):
        original = self.command
        for address in ('198.51.100.20-198.51.100.30', 'dns.invalid', '198.51.100.0/24'):
            self.data = raw(); self.calls = []
            def command(path, **options):
                result = original(path, **options)
                if path.endswith('/add'):
                    self.data['restrictions'].append(dict(list='Morosos', address=address))
                return result
            self.api.side_effect = command
            with self.assertRaisesRegex(OperationRejected, 'write_unconfirmed'):
                __import__('portal.remote_reader', fromlist=['collect']).collect(self.config, self.factory)
            self.assertEqual(len(self.writes()), 1)


class CounterAuditTests(SimpleTestCase):
    def test_reset_survives_history_rotation_until_reboot(self):
        history = [normalize(raw(value, str(3600+i*60)), 10000+i*60)
                   for i, value in enumerate(('1000/1000', '100/100', '1200/1200'))]
        sample = normalize(raw('1300/1300', '3780'), 10180)
        carry_counter_validity(history, sample)
        self.assertIn('reiniciado', sample['clients'][0]['counter_note'])
        for i in range(4, 8):
            newer = normalize(raw('2000/2000', str(3600+i*60)), 10000+i*60)
            carry_counter_validity([sample], newer)
            sample = newer
        self.assertFalse(estimate_uptime([sample])[1]['ready'])
        rebooted = normalize(raw('2000/2000', '90'), sample['timestamp']+60)
        carry_counter_validity([sample], rebooted)
        self.assertTrue(estimate_uptime([sample, rebooted])[1]['ready'])

    def test_reset_stays_invalid_after_counter_recovers_each_direction(self):
        for counters in [('1000/1000', '100/1100', '1200/1200'),
                         ('1000/1000', '1100/100', '1200/1200')]:
            history = [normalize(raw(value, str(3600+i*60)), 10000+i*60) for i, value in enumerate(counters)]
            rows, summary = estimate_uptime(history)
            self.assertIsNone(rows[0]['daily_bytes'])
            self.assertIn('reiniciado', rows[0]['estimate_note'])
            self.assertFalse(summary['ready'])

    def test_adjacent_boot_boundary_prevents_cross_epoch_and_router_mix(self):
        history = [normalize(raw('1000/1000', '3600'), 10000),
                   normalize(raw('100/100', '30'), 10060),
                   normalize(raw('1200/1200', '90'), 10120)]
        self.assertTrue(estimate_uptime(history)[1]['ready'])
        history[1]['identity'] = 'Otro router'
        self.assertTrue(estimate_uptime(history)[1]['ready'])
        # Dos reinicios con el mismo uptime absoluto respecto al último tampoco se mezclan.
        history[1]['uptime'] = 9000
        self.assertTrue(estimate_uptime(history)[1]['ready'])


class InventoryAuditTests(SimpleTestCase):
    setUp = AppTests.setUp
    profile = AppTests.profile

    def setup_inventory(self, key='one'):
        self.profile(key)
        source = raw(); source['queues'][0]['target'] = '198.51.100.50/32'
        sample = normalize(source, 10000)
        Store().update(lambda d: d['profiles'][key].update(history=[sample]))
        return source, sample['inventory'][0]

    def include(self, row, key='one', action='include', reading='10000.0'):
        return self.client.post('/inventario/'+key+'/', dict(action=action, fingerprint=row['fingerprint'], reading=reading))

    def test_persistence_revert_locality_isolation_and_analytics(self):
        source, row = self.setup_inventory(); self.setup_inventory('two')
        page = self.client.get('/inventario/one/')
        self.assertContains(page, 'Filtro de infraestructura')
        self.assertContains(page, '198.51.100.50')
        self.assertContains(self.client.get('/clientes/?site=one'), 'Revisar colas excluidas')
        self.include(row)
        saved = Store().read()['profiles']
        self.assertEqual(saved['one']['inclusions'], [row['fingerprint']])
        self.assertEqual(len(saved['one']['history'][-1]['clients']), 1)
        self.assertEqual(saved['two']['history'][-1]['clients'], [])
        self.assertEqual(self.client.get('/?site=one').context['summary']['estimated_count'], 1)
        self.assertContains(self.client.get('/inventario/one/'), 'Revertir inclusión')
        with patch('portal.views.collect', return_value=source) as reader:
            from portal.views import refresh_profile
            refresh_profile('one')
            self.assertEqual(reader.call_args.args[0]['inclusions'], [row['fingerprint']])
        sample = Store().read()['profiles']['one']['history'][-1]
        self.include(row, action='revert', reading=str(sample['timestamp']))
        saved = Store().read()['profiles']['one']
        self.assertEqual(saved['inclusions'], [])
        self.assertEqual(saved['history'][-1]['clients'], [])

    def test_no_browser_bypass_stale_forged_and_changed_targets(self):
        source, row = self.setup_inventory()
        self.include(dict(row, fingerprint='forged'))
        self.include(row, reading='9999')
        self.assertNotIn('inclusions', Store().read()['profiles']['one'])
        for field, value in (('.id', '*2'), ('name', 'Otro'), ('target', '198.51.100.90/32')):
            changed = copy.deepcopy(source); changed['queues'][0][field] = value
            self.assertEqual(normalize(changed, 10000, inclusions=[row['fingerprint']])['clients'], [])
        self.assertEqual(self.client.post('/inventario/one/', {'action': 'arbitrary'}).status_code, 400)

    def test_shared_multiple_ipv6_invalid_and_ambiguous_cannot_be_included(self):
        source, row = self.setup_inventory()
        for target in ('198.51.100.0/24', '198.51.100.50/32,198.51.100.90/32', '::1/128', 'bad'):
            changed = copy.deepcopy(source); changed['queues'][0]['target'] = target
            self.assertEqual(normalize(changed, 1, inclusions=[row['fingerprint']])['clients'], [])
        for invalid in ('invalid', 'disabled'):
            changed = copy.deepcopy(source); changed['queues'][0][invalid] = True
            self.assertFalse(normalize(changed, 1)['inventory'][0]['inclusion_eligible'])
        changed = copy.deepcopy(source); changed['queues'].append(dict(changed['queues'][0], **{'.id': '*2'}))
        sample = normalize(changed, 1, inclusions=[row['fingerprint']])
        self.assertEqual(sample['clients'], [])
        Store().update(lambda d: d['profiles']['one'].update(history=[sample]))
        self.include(row, reading='1.0')
        self.assertNotIn('inclusions', Store().read()['profiles']['one'])

    def test_remote_exception_is_server_profile_bound_and_fresh(self):
        source, row = self.setup_inventory()
        api = MagicMock(return_value=iter([]))
        op = dict(id=row['id'], ip=row['ip'], name=row['name'], identity='Router de test', action='suspend')
        with self.assertRaises(OperationRejected):
            change_morosity(api, source['queues'], [], 'Router de test', op)
        api.assert_not_called()
        change_morosity(api, source['queues'], [], 'Router de test', op, [row['fingerprint']])
        api.assert_called_once()
        changed = copy.deepcopy(source); changed['queues'][0]['name'] = 'Otro'
        with self.assertRaises(OperationRejected):
            change_morosity(api, changed['queues'], [], 'Router de test', op, [row['fingerprint']])
        for field, value in (('bytes', None), ('max-limit', 'invalid'), ('rate', '-1/0')):
            changed = copy.deepcopy(source); changed['queues'][0][field] = value
            with self.assertRaises(OperationRejected):
                change_morosity(api, changed['queues'], [], 'Router de test', op, [row['fingerprint']])

    def test_unknown_restriction_prevents_browser_action_and_uncertain_requires_sync(self):
        self.profile()
        source = raw(); source['restrictions'] = [{'list': 'Morosos', 'address': 'dns.invalid'}]
        sample = normalize(source, 10000)
        Store().update(lambda d: d['profiles']['one'].update(history=[sample]))
        row = sample['clients'][0]
        with patch('portal.views.collect') as reader:
            self.client.post('/clientes/one/*1/morosidad/', dict(confirmed='yes', action='suspend', fingerprint=row['fingerprint'], included='yes'))
            reader.assert_not_called()
        Store().update(lambda d: d['profiles']['one'].update(history=[normalize(raw(), 10000)]))
        with patch('portal.views.collect', side_effect=ConnectionFailure('Tiempo agotado')) as reader:
            self.client.post('/clientes/one/*1/morosidad/', dict(confirmed='yes', action='suspend', fingerprint=row['fingerprint']))
            self.assertEqual(reader.call_count, 1)
            self.client.post('/clientes/one/*1/morosidad/', dict(confirmed='yes', action='suspend', fingerprint=row['fingerprint']))
            self.assertEqual(reader.call_count, 1)
        self.assertIn('sincroniza', Store().read()['profiles']['one']['last_error'])


class TimeoutAuditTests(SimpleTestCase):
    def test_blocked_operations_have_fixed_capacity_and_no_write_retry(self):
        release = threading.Event()
        calls = []
        def blocked(*a, **k):
            calls.append(k); release.wait(2)
        with patch('portal.connector._collect', side_effect=blocked):
            try:
                for _ in range(7):
                    with self.assertRaises(ConnectionFailure):
                        collect({}, morosity={'action': 'suspend'}, total_timeout=.015)
                self.assertEqual(len(calls), 4)
            finally:
                release.set()
        time.sleep(.05)

    def test_process_can_exit_with_permanently_blocked_resolver(self):
        code = '''
import threading
from portal.connector import collect, ConnectionFailure
import portal.connector as connector
connector.socket.getaddrinfo = lambda *a, **k: threading.Event().wait()
try: collect(dict(host='synthetic.invalid', port=22), total_timeout=.04)
except ConnectionFailure: pass
'''
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocked_dns_is_bounded_and_does_not_accumulate_threads(self):
        entered, release = threading.Event(), threading.Event()
        calls = []
        def blocked(*args, **kwargs):
            calls.append(args); entered.set(); release.wait(2)
            return []
        with patch('portal.connector.socket.getaddrinfo', side_effect=blocked):
            try:
                for _ in range(8):
                    before = time.monotonic()
                    with self.assertRaises(ConnectionFailure):
                        collect(dict(host='synthetic.invalid', port=22), total_timeout=.025)
                    self.assertLess(time.monotonic()-before, .3)
                self.assertLessEqual(len(calls), 2)
            finally: release.set()
        time.sleep(.05)

    def test_multiple_addresses_fall_through_to_loopback(self):
        with ssh_reader() as (profile, state):
            addresses = socket.getaddrinfo(profile['host'], profile['port'], type=socket.SOCK_STREAM)
            bad = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))
            with patch('portal.connector.socket.getaddrinfo', return_value=[bad]+addresses):
                self.assertEqual(collect(profile)['schema'], 1)
            self.assertTrue(state['authenticated'])

    def test_auth_reader_and_close_use_normal_global_deadline(self):
        for block in ('connect', 'close'):
            release, finished = threading.Event(), threading.Event()
            with ssh_reader() as (profile, state), patch('portal.connector.paramiko.SSHClient') as factory:
                client = factory.return_value
                if block == 'connect':
                    client.connect.side_effect = lambda *a, **k: release.wait(2)
                else:
                    client.connect.side_effect = OSError('synthetic')
                    client.close.side_effect = lambda: (release.wait(2), finished.set())
                try:
                    before = time.monotonic()
                    with self.assertRaises(ConnectionFailure) as caught:
                        collect(profile, total_timeout=.04)
                    self.assertEqual(caught.exception.code, 'timeout')
                    self.assertLess(time.monotonic()-before, .3)
                finally: release.set()
        with ssh_reader(reader_delay=.2) as (profile, state):
            with self.assertRaises(ConnectionFailure) as caught:
                collect(profile, morosity={'action': 'suspend'}, total_timeout=.08)
            self.assertIn('incierto', str(caught.exception))


class ScheduleAuditTests(SimpleTestCase):
    setUp = AppTests.setUp
    profile = AppTests.profile

    def test_idle_cache_invalidated_by_external_store_updates(self):
        self.profile()
        coordinator = Coordinator(lambda key: None)
        self.addCleanup(coordinator.stop)
        with patch.object(Store, '_read', autospec=True, side_effect=Store._read) as reads:
            coordinator.tick()
            self.assertEqual(reads.call_count, 1)
            for _ in range(10): coordinator.tick()
            self.assertEqual(reads.call_count, 1)
            Store().update(lambda d: d['profiles']['one'].update(connected=False))
            count = reads.call_count
            coordinator.tick()
            self.assertEqual(reads.call_count, count+1)
        self.assertFalse(coordinator.schedule_snapshot[1][0]['connected'])
        self.assertNotIn('history', coordinator.schedule_snapshot[1][0])
        self.assertNotIn('ssh_password', coordinator.schedule_snapshot[1][0])

    def test_stale_scheduled_work_rechecks_pause_disconnect_and_credentials(self):
        self.profile()
        calls = []
        coordinator = Coordinator(lambda key: calls.append(key), clock=lambda: 10000)
        self.addCleanup(coordinator.stop)
        for changes in (dict(connected=False), dict(automatic=dict(enabled=False, next_at=1)),
                        dict(automatic=dict(enabled=True, next_at=20000))):
            Store().update(lambda d: d['profiles']['one'].update(changes))
            coordinator.execute('one')
        self.assertEqual(calls, [])
