import copy
import json
from pathlib import Path
import tempfile
from django.test import SimpleTestCase
from agent.client import CentralClient
from agent.contract import validate_state, validate_target
from agent.routeros import RouterOSAdapter, RouterOSTransport
from agent.simulator import Simulator

class SimulatorTests(SimpleTestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / '.local' / 'tmp')
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'router.sqlite3'
        self.inventory = {'1': {'allowed_ips': ['198.51.100.20']}}
        self.sim = Simulator(self.path, self.inventory)
        self.state = {'service': 1, 'ip': '198.51.100.20', 'revision': 1, 'enabled': True, 'up_kbps': 2000, 'down_kbps': 4000}

    def test_all_actions_repeated_preserve_order_burst_and_shared_objects(self):
        original = self.sim.config(1)
        state = self.sim.apply(1, 'provision', self.state)
        self.sim.apply(1, 'provision', self.state)
        for revision, action, enabled in [(2, 'suspend', False), (3, 'resume', True), (4, 'plan', True)]:
            state = dict(self.state, revision=revision, enabled=enabled, down_kbps=10000 if action == 'plan' else 4000)
            self.sim.apply(1, action, state)
            self.sim.apply(1, action, state)
            self.assertEqual(self.sim.read(1, state), state)
        config = self.sim.config(1)
        self.assertEqual(len(config['queues']), 3)
        self.assertEqual(len(config['morosos']), 1)
        self.assertEqual(config['queues'][0], original['queues'][0])
        self.assertEqual(config['queues'][-1], original['queues'][-1])
        self.assertEqual(config['schedulers'], original['schedulers'])
        self.assertEqual(config['queues'][1]['burst'], {'limit': '0/0', 'threshold': '0/0', 'time': '0s/0s'})

    def test_before_write_failure_is_not_success(self):
        with self.assertRaises(RuntimeError): self.sim.apply(1, 'provision', self.state, 'before_write')
        self.assertIsNone(self.sim.read(1, self.state))

    def test_after_write_failure_restart_reconciles(self):
        with self.assertRaises(RuntimeError): self.sim.apply(1, 'provision', self.state, 'after_write')
        restarted = Simulator(self.path, self.inventory)
        self.assertEqual(restarted.apply(1, 'provision', self.state), self.state)
        self.assertEqual(len(restarted.config(1)['queues']), 3)

    def test_stale_revision_and_revision_reuse_rejected(self):
        self.sim.apply(1, 'provision', self.state)
        self.sim.apply(1, 'suspend', dict(self.state, revision=2, enabled=False))
        with self.assertRaises(ValueError): self.sim.apply(1, 'resume', self.state)
        with self.assertRaises(ValueError): self.sim.apply(1, 'resume', dict(self.state, revision=2))

    def test_unknown_action_and_foreign_restriction_block_provision(self):
        with self.assertRaises(ValueError): self.sim.apply(1, 'arbitrary', self.state)
        config = self.sim.config(1)
        config['morosos']['198.51.100.20'] = {'service': 99, 'active': True}
        with self.sim.connect() as db: db.execute('UPDATE routers SET config=?', (json.dumps(config),))
        with self.assertRaises(ValueError): self.sim.apply(1, 'provision', self.state)
        self.assertEqual(self.sim.config(1), config)

    def test_existing_nonzero_burst_and_queue_position_are_preserved(self):
        self.sim.apply(1, 'provision', self.state)
        config = self.sim.config(1)
        burst = {'limit': '8M/16M', 'threshold': '2M/4M', 'time': '15s/15s'}
        config['queues'][1]['burst'] = burst
        with self.sim.connect() as db: db.execute('UPDATE routers SET config=?', (json.dumps(config),))
        self.sim.apply(1, 'plan', dict(self.state, revision=2, up_kbps=5000, down_kbps=10000))
        self.assertEqual(self.sim.config(1)['queues'][1]['burst'], burst)
        self.assertEqual([q['name'] for q in self.sim.config(1)['queues']], [q['name'] for q in config['queues']])

    def test_duplicate_queue_and_unknown_policy_block_writes(self):
        self.sim.apply(1, 'provision', self.state)
        config = self.sim.config(1)
        config['queues'].insert(1, copy.deepcopy(config['queues'][1]))
        with self.sim.connect() as db: db.execute('UPDATE routers SET config=?', (json.dumps(config),))
        with self.assertRaises(ValueError): self.sim.apply(1, 'suspend', dict(self.state, revision=2, enabled=False))
        config['queues'].pop(1); config['policy'] = 'desconocida'
        with self.sim.connect() as db: db.execute('UPDATE routers SET config=?', (json.dumps(config),))
        with self.assertRaises(ValueError): self.sim.apply(1, 'suspend', dict(self.state, revision=2, enabled=False))

    def test_protected_ips_subnets_and_unapproved_destinations(self):
        for ip in ['198.51.100.1', '198.51.100.2', '198.51.100.50', '198.51.100.90', '198.51.100.0/24', '198.51.100.21']:
            with self.assertRaises(ValueError): validate_target(ip, self.inventory['1']['allowed_ips'])
        with self.assertRaises(ValueError): validate_state(dict(self.state, arbitrary='command'), self.inventory['1']['allowed_ips'])
        with self.assertRaises(ValueError): validate_state(dict(self.state, enabled='true'), self.inventory['1']['allowed_ips'])

    def test_real_transport_and_writes_are_disabled(self):
        transport = RouterOSTransport(host='192.0.2.1', username='', password='', ca_file='unused')
        with self.assertRaises(RuntimeError): transport.open()
        adapter = RouterOSAdapter(transport, ['198.51.100.20'])
        with self.assertRaises(RuntimeError): adapter.apply(1, 'provision', self.state)

    def test_https_required_with_only_explicit_loopback_exception(self):
        for url in ['http://198.51.100.1', 'http://127.0.0.1', 'ftp://localhost']:
            with self.assertRaises(ValueError): CentralClient(url, 'unused', '', False)
        with self.assertRaises(ValueError): CentralClient('http://198.51.100.1', 'unused', '', True)
        CentralClient('http://127.0.0.1:8000', 'unused', '', True)
        CentralClient('https://example.invalid', 'unused', '')
