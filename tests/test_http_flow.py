from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, LiveServerTestCase, override_settings
from django.utils import timezone
from agent.client import CentralClient
from agent.simulator import Simulator
from ops.models import Customer, Membership, Service, Task
from ops.queue import claim, request_action
from .support import fixture

ROOT = Path(__file__).resolve().parents[1]

@override_settings(ALLOWED_HOSTS=['localhost', '127.0.0.1', 'testserver'], PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class HTTPFlowTests(LiveServerTestCase):
    def setUp(self):
        self.f = fixture()
        self.folder = tempfile.TemporaryDirectory(dir=ROOT / '.local' / 'tmp')
        self.addCleanup(self.folder.cleanup)
        self.state_file = str(Path(self.folder.name) / 'simulator.sqlite3')
        self.config_file = Path(self.folder.name) / 'agent.json'
        self.config = {'mode': 'simulator', 'url': self.live_server_url, 'allow_loopback_http': True,
            'site': self.f['site'].pk, 'agent': str(self.f['agent'].pk), 'token': self.f['token'],
            'state_file': self.state_file, 'routers': {str(self.f['router'].pk): {'allowed_ips': self.f['router'].allowed_ips}}}
        self.config_file.write_text(json.dumps(self.config))
        self.client.force_login(self.f['user'])

    def worker(self, fault=None, cli=False):
        args = [sys.executable, '-m', 'agent', '--config', str(self.config_file), '--once'] if cli else [sys.executable, '-m', 'tests.worker_process', str(self.config_file)]
        if fault: args.append(fault)
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=25)
        # Los procesos no reciben credenciales en argv ni las imprimen.
        self.assertNotIn(self.f['token'], result.stdout + result.stderr)
        return result

    def request(self, action='provision'):
        service = Service.objects.get(pk=self.f['service'].pk)
        response = self.client.post(f'/services/{service.pk}/', {'action': action, 'plan': self.f['faster'].pk,
            'reason': 'Recorrido HTTP ficticio', 'revision': service.revision})
        self.assertEqual(response.status_code, 302)
        return Task.objects.filter(service=service).latest('created_at')

    def test_panel_create_and_four_actions_through_actual_http_agent_process(self):
        response = self.client.post('/services/new/', {'name': 'Persona Ficticia HTTP', 'contact': 'demo@example.invalid',
            'router': self.f['router'].pk, 'equipment': self.f['equipment'].pk, 'ip': '198.51.100.21',
            'location': 'Casa demo 21', 'plan': self.f['plan'].pk})
        self.assertEqual(response.status_code, 302)
        self.f['service'] = Service.objects.get(ip='198.51.100.21')
        self.assertEqual(self.f['service'].customer.name, 'Persona Ficticia HTTP')
        for action, enabled in [('provision', True), ('suspend', False), ('resume', True), ('plan', True)]:
            task = self.request(action)
            self.assertEqual(self.worker(cli=True).returncode, 0)
            task.refresh_from_db()
            self.f['service'].refresh_from_db()
            self.assertEqual(task.status, 'verified')
            self.assertEqual(self.f['service'].observed['enabled'], enabled)
            sim = Simulator(self.state_file, self.config['routers'])
            self.assertEqual(sim.read(self.f['router'].pk, task.snapshot), task.snapshot)
            page = self.client.get(f'/services/{self.f["service"].pk}/')
            self.assertContains(page, 'Verificada')
            self.assertContains(page, 'Última comprobación del simulador')
        self.assertEqual(self.f['service'].observed['down_kbps'], 10000)
        connection.close()
        self.assertEqual(Task.objects.filter(service=self.f['service'], status='verified').count(), 4)

    def test_before_and_after_write_failures_recover_using_fresh_process(self):
        for fault in ('before_write', 'after_write'):
            task = self.request()
            self.assertEqual(self.worker(fault).returncode, 0)
            task.refresh_from_db()
            self.assertEqual(task.status, 'pending')
            service = Service.objects.get(pk=task.service_id)
            if fault == 'before_write': self.assertEqual(service.observed, {})
            Task.objects.filter(pk=task.pk).update(available_at=timezone.now()-timedelta(seconds=1))
            self.assertEqual(self.worker(cli=True).returncode, 0)
            task.refresh_from_db(); self.assertEqual(task.status, 'verified')
        sim = Simulator(self.state_file, self.config['routers'])
        self.assertEqual(len(sim.config(self.f['router'].pk)['queues']), 3)

    def test_real_process_exit_after_write_before_outbox_reconciles_without_false_success(self):
        task = self.request()
        self.assertEqual(self.worker('crash_after_write').returncode, 23)
        task.refresh_from_db()
        self.assertEqual(task.status, 'leased')
        self.assertEqual(Service.objects.get(pk=task.service_id).observed, {})
        sim = Simulator(self.state_file, self.config['routers'])
        self.assertEqual(sim.read(self.f['router'].pk, task.snapshot), task.snapshot)
        Task.objects.filter(pk=task.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.worker(cli=True).returncode, 0)
        task.refresh_from_db()
        self.assertEqual(task.status, 'verified')
        self.assertEqual(task.attempts, 2)
        self.assertEqual(len(sim.config(self.f['router'].pk)['queues']), 3)

    def test_process_restart_resends_durable_outbox_and_rereads_simulator(self):
        task = self.request()
        self.assertEqual(self.worker('before_report').returncode, 24)
        task.refresh_from_db()
        self.assertEqual(task.status, 'leased')
        sim = Simulator(self.state_file, self.config['routers'])
        self.assertEqual(len(sim.pending_reports()), 1)
        self.assertEqual(Service.objects.get(pk=task.service_id).observed, {})
        self.assertEqual(self.worker(cli=True).returncode, 0)
        task.refresh_from_db()
        self.assertEqual(task.status, 'verified')
        self.assertEqual(task.attempts, 1)
        self.assertEqual(sim.pending_reports(), [])

    def test_outbox_is_not_evidence_if_simulator_changed_while_offline(self):
        task = self.request()
        self.worker('before_report')
        sim = Simulator(self.state_file, self.config['routers'])
        config = sim.config(self.f['router'].pk)
        config['morosos']['198.51.100.20']['active'] = True
        with sim.connect() as db: db.execute('UPDATE routers SET config=?', (json.dumps(config),))
        self.assertEqual(self.worker(cli=True).returncode, 0)
        task.refresh_from_db()
        self.assertEqual(task.status, 'pending')
        self.assertEqual(Service.objects.get(pk=task.service_id).observed, {})

    def test_site_isolation_and_viewer_on_browser_and_agent_api(self):
        other = fixture('b')
        response = self.client.get(f'/services/{other["service"].pk}/')
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/services/new/', {'name': 'No permitido', 'router': other['router'].pk,
            'ip': '198.51.100.21', 'location': 'Demo', 'plan': other['plan'].pk})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(name='No permitido').exists())
        Membership.objects.filter(user=self.f['user']).update(role='viewer')
        response = self.client.post(f'/services/{self.f["service"].pk}/', {'action': 'provision', 'reason': 'Sin permiso', 'revision': 0})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Task.objects.count(), 0)
        api = CentralClient(self.live_server_url, str(self.f['agent'].pk), 'incorrecto', True)
        with self.assertRaises(RuntimeError): api.claim()

    def test_csrf_is_required_for_browser_actions(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.f['user'])
        response = client.post(f'/services/{self.f["service"].pk}/', {'action': 'provision', 'revision': 0, 'reason': 'Demo'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Task.objects.count(), 0)

    def test_duplicate_ip_rolls_back_new_customer_and_shows_inline_error(self):
        before = Customer.objects.count()
        response = self.client.post('/services/new/', {'name': 'No duplicar cliente', 'router': self.f['router'].pk,
            'equipment': self.f['equipment'].pk, 'ip': '198.51.100.20', 'location': 'Ficticia', 'plan': self.f['plan'].pk})
        self.assertContains(response, 'Esa IP ya tiene un servicio')
        self.assertEqual(Customer.objects.count(), before)

    def test_inventory_cannot_be_expanded_by_task_from_server(self):
        self.request()
        item = claim(self.f['agent'])
        from agent.worker import Worker
        sim = Simulator(self.state_file, {str(self.f['router'].pk): {'allowed_ips': ['198.51.100.21']}})
        worker = Worker(None, sim, self.f['site'].pk)
        with self.assertRaises(ValueError): worker.check(item)
        item['site'] = self.f['site'].pk + 999
        with self.assertRaises(ValueError): worker.check(item)

    def test_agent_api_rejects_arbitrary_parameters_and_forged_results(self):
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + self.f['token'], 'HTTP_X_AGENT_ID': str(self.f['agent'].pk)}
        self.assertEqual(self.client.post('/api/agent/claim/', json.dumps({'command': 'anything'}), content_type='application/json', **headers).status_code, 400)
        self.assertEqual(self.client.get('/api/agent/claim/', **headers).status_code, 405)
        self.assertEqual(self.client.post('/api/agent/validate/', json.dumps({'task': 'invalid', 'attempt': 'invalid'}), content_type='application/json', **headers).status_code, 400)

    def test_login_throttle_and_inline_errors(self):
        self.client.logout()
        for _ in range(12):
            self.client.post('/login/', {'username': 'nadie', 'password': 'ficticio'})
        self.assertEqual(self.client.post('/login/', {'username': 'nadie', 'password': 'ficticio'}).status_code, 429)
        self.client.force_login(self.f['user'])
        response = self.client.post('/services/new/', {'name': 'Demo', 'router': self.f['router'].pk, 'plan': self.f['plan'].pk,
            'location': 'Ficticio', 'ip': '198.51.100.90'})
        self.assertContains(response, 'Destino fuera del inventario')
