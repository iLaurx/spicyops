import copy
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from portal.connector import collect as collect_ssh
from portal.remote_reader import collect, OperationRejected
from .test_connector import ssh_reader
from .test_telemetry import raw


class MorosityTests(SimpleTestCase):
    def setUp(self):
        self.data = raw()
        self.operation = dict(action='suspend', id='*1', name='Abonado de test',
                              ip='198.51.100.20', identity='Router de test')
        self.config = dict(router_host='198.51.100.1', router_user='test',
                           router_password='test-only', ca_file='test.crt', morosity=self.operation)
        self.calls = []
        self.deny = False
        self.ignore_write = False
        self.api = MagicMock(side_effect=self.command)
        self.factory = MagicMock(return_value=self.api)
        self.tls = patch('portal.remote_reader.ssl.create_default_context').start()
        self.addCleanup(patch.stopall)

    def command(self, path, **options):
        self.calls.append((path, options))
        if path == '/system/resource/print':
            return iter([dict(uptime='1h', version='6.49.23')])
        if path == '/system/identity/print':
            return iter([dict(name=self.data['router']['identity'])])
        if path == '/queue/simple/print':
            return iter(copy.deepcopy(self.data['queues']))
        if path == '/ip/firewall/address-list/print':
            return iter(copy.deepcopy(self.data['restrictions']))
        if self.deny:
            raise RuntimeError('test-only private API exception')
        if not self.ignore_write:
            if path == '/ip/firewall/address-list/add':
                self.data['restrictions'].append(dict(options, **{'.id': '*A'}))
            elif path == '/ip/firewall/address-list/set':
                entry = next(e for e in self.data['restrictions'] if e['.id'] == options['.id'])
                entry.update(options)
            else:
                raise AssertionError('Comando fuera del alcance')
        return iter([])

    def writes(self):
        return [(p, o) for p, o in self.calls if not p.endswith('/print')]

    def test_add_verify_idempotent_restore_reenable_without_changing_plan(self):
        queues = copy.deepcopy(self.data['queues'])
        result = collect(self.config, self.factory)
        self.assertEqual(result['restrictions'][0]['address'], self.operation['ip'])
        self.assertEqual(len(self.writes()), 1)
        collect(self.config, self.factory)
        self.assertEqual(len(self.writes()), 1)
        self.operation['action'] = 'restore'
        result = collect(self.config, self.factory)
        self.assertEqual(result['restrictions'][0]['disabled'], 'yes')
        self.assertEqual(self.writes()[-1][0], '/ip/firewall/address-list/set')
        self.operation['action'] = 'suspend'
        collect(self.config, self.factory)
        self.assertEqual(len(self.data['restrictions']), 1)
        self.assertEqual(self.data['queues'], queues)
        self.assertTrue(self.api.close.called)

    def test_reject_router_queue_or_ip_changes_and_duplicate_targets(self):
        original = copy.deepcopy(self.data)
        for field, value in [('name', 'changed'), ('target', '198.51.100.21/32'),
                             ('disabled', True), ('invalid', True), ('.id', '*2')]:
            self.data = copy.deepcopy(original)
            self.data['queues'][0][field] = value
            with self.assertRaises(OperationRejected): collect(self.config, self.factory)
        self.data = copy.deepcopy(original)
        self.data['queues'].append(dict(self.data['queues'][0], **{'.id': '*2'}))
        with self.assertRaises(OperationRejected): collect(self.config, self.factory)
        self.data = copy.deepcopy(original)
        self.data['router']['identity'] = 'Otro router'
        with self.assertRaises(OperationRejected): collect(self.config, self.factory)
        self.assertEqual(self.writes(), [])

    def test_reject_shared_dynamic_and_duplicate_restrictions(self):
        for entries in (
            [{'.id': '*A', 'list': 'Morosos', 'address': '198.51.100.0/24'}],
            [{'.id': '*A', 'list': 'Morosos', 'address': self.operation['ip'], 'dynamic': True}],
            [{'.id': key, 'list': 'Morosos', 'address': self.operation['ip']} for key in ('*A', '*B')],
        ):
            self.data['restrictions'] = entries
            with self.assertRaises(OperationRejected): collect(self.config, self.factory)
        self.assertEqual(self.writes(), [])

    def test_permission_denied_and_missing_confirmation_do_not_claim_success(self):
        self.deny = True
        with self.assertRaisesRegex(OperationRejected, '^write_unconfirmed$'):
            collect(self.config, self.factory)
        self.deny = False
        self.ignore_write = True
        with self.assertRaisesRegex(OperationRejected, '^write_unconfirmed$'):
            collect(self.config, self.factory)
        self.assertTrue(self.api.close.called)

    def test_write_operation_over_real_loopback_ssh_not_in_shell_command(self):
        with ssh_reader() as (profile, state):
            collect_ssh(profile, morosity=self.operation)
            self.assertEqual(state['payload']['morosity'], self.operation)
            self.assertNotIn(self.operation['ip'], state['command'])
