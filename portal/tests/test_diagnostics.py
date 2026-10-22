import copy
import io
import json
from pathlib import Path
import socket
import ssl
import tempfile
import threading
import time
from unittest.mock import MagicMock, patch
import paramiko
from django.test import Client, SimpleTestCase, override_settings
from portal import diagnostics as d
from portal.auth import identity
from portal.connector import collect, ConnectionFailure
from portal.store import Store
from portal.telemetry import normalize
from portal.views import refresh_profile
from .test_telemetry import raw


def controlled(value=None):
    def collect(profile, *, progress):
        for stage, _ in d.STAGES[:-1]:
            progress(stage, 'comprobando', '')
            progress(stage, 'correcto', {'access':'port_open', 'identity':'host_verified', 'auth':'authenticated',
                     'reader':'reader_ready', 'tls':'tls_verified', 'api':'api_read'}[stage])
        return raw() if value is None else copy.deepcopy(value)
    return collect


class DiagnosticTests(SimpleTestCase):
    def test_every_failure_skips_dependents_and_filters_messages(self):
        cases = {'access':['dns_failed','refused','timeout','communication'], 'identity':['host_new','host_changed'],
                 'auth':['auth_rejected'], 'reader':['python_unavailable','reader_missing'],
                 'tls':['ca_missing','ca_invalid','tls_failed','tls_expired','tls_hostname','tls_untrusted'],
                 'api':['api_auth','api_denied','incomplete','communication']}
        for stage, codes in cases.items():
            for code in codes:
                with self.subTest(stage=stage, code=code):
                    result = d.fresh_result()
                    def failure(profile, *, progress):
                        for key, _ in d.STAGES:
                            progress(key, 'comprobando')
                            if key == stage: raise ConnectionFailure('SECRET password trace', stage=key, code=code)
                            progress(key, 'correcto', '')
                    with patch.object(d, 'collect', side_effect=failure): d.run({}, result, lambda r: None)
                    index = [k for k, _ in d.STAGES].index(stage)
                    self.assertEqual(result['stages'][index]['state'], 'error')
                    self.assertTrue(all(r['state'] == 'no_comprobada' for r in result['stages'][index+1:]))
                    self.assertNotIn('SECRET', json.dumps(result)); self.assertFalse(result['running'])

    def test_empty_ambiguous_missing_counters_and_incomplete_inventory(self):
        empty = raw(); empty['queues'] = []
        ambiguous = raw(); ambiguous['queues'].append(dict(ambiguous['queues'][0], **{'.id':'*2'}))
        counters = raw(); counters['queues'][0].pop('bytes')
        unsupported = raw(); unsupported['router']['version'] = '8.0'
        for value, state, code in [(empty,'correcto','inventory_empty'), (ambiguous,'advertencia','inventory_warning'),
                (counters,'advertencia','inventory_warning'), ({'schema':1},'error','incomplete'),
                (unsupported,'error','inventory_version'), (raw(),'correcto','inventory_ok')]:
            with self.subTest(code=code):
                result = d.fresh_result()
                with patch.object(d, 'collect', side_effect=controlled(value)): d.run({},result,lambda r:None)
                self.assertEqual(result['stages'][-1]['state'],state)
                self.assertEqual(result['stages'][-1]['code'],code)

    def test_omitted_proofs_cannot_be_successful(self):
        result = d.fresh_result()
        with patch.object(d, 'collect', return_value=raw()): d.run({},result,lambda r:None)
        self.assertEqual(result['stages'][0]['state'], 'error')
        self.assertNotIn('7 etapas.', result['summary'])

    @patch('portal.connector.paramiko.SSHClient')
    @patch('portal.connector.socket.getaddrinfo')
    def test_resolution_failure_is_bounded_and_client_is_closed(self, resolve, factory):
        resolve.side_effect = socket.gaierror('SECRET')
        with self.assertRaises(ConnectionFailure) as caught:
            collect({'host':'test.invalid','port':22}, progress=lambda *args:None)
        self.assertEqual(caught.exception.code,'dns_failed');factory.return_value.close.assert_called()
        def slow(*args, **kwargs): time.sleep(.1); return []
        resolve.side_effect = slow
        before = time.monotonic()
        with self.assertRaises(ConnectionFailure) as caught:
            collect({'host':'test.invalid','port':22}, progress=lambda *args:None,total_timeout=.02)
        self.assertEqual(caught.exception.code,'timeout');self.assertLess(time.monotonic()-before,.09)

    @patch('portal.connector.paramiko.SSHClient')
    @patch('portal.connector.socket.socket')
    @patch('portal.connector.socket.getaddrinfo', return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',22))])
    def test_refused_timeout_and_auth_close_resources(self, resolve, sock, client):
        for error, code in [(ConnectionRefusedError('SECRET'),'refused'), (TimeoutError('SECRET'),'timeout')]:
            sock.return_value.connect.side_effect = error
            with self.assertRaises(ConnectionFailure) as caught:
                collect({'host':'127.0.0.1','port':22},progress=lambda *args:None)
            self.assertEqual(caught.exception.code,code);sock.return_value.close.assert_called()
        sock.return_value.connect.side_effect = None
        client.return_value.connect.side_effect = paramiko.AuthenticationException('SECRET')
        with self.assertRaises(ConnectionFailure) as caught:
            collect({'host':'127.0.0.1','port':22,'ssh_user':'test'},progress=lambda *args:None)
        self.assertEqual(caught.exception.code,'auth_rejected');self.assertNotIn('SECRET',str(caught.exception))

    def test_remote_safe_error_codes(self):
        from portal import remote_reader
        from librouteros.exceptions import TrapError
        for exc, code in [(ImportError('SECRET'),'reader_missing'), (FileNotFoundError('SECRET'),'incomplete'),
                          (ssl.SSLError('SECRET'),'tls_failed'), (ConnectionRefusedError('SECRET'),'api_refused'),
                          (TimeoutError('SECRET'),'remote_timeout'), (TrapError('SECRET'),'api_denied')]:
            with self.subTest(code=code):
                incoming = MagicMock();incoming.buffer.read.return_value=b'{"diagnostic":true}'
                out = io.StringIO()
                with patch.object(remote_reader,'collect',side_effect=exc), patch.object(remote_reader.sys,'stdin',incoming), patch.object(remote_reader.sys,'stdout',out):
                    remote_reader.main()
                self.assertEqual(json.loads(out.getvalue())['error'],code)
                self.assertNotIn('SECRET',out.getvalue())

    def test_inventory_budget_and_remote_read_only_guard(self):
        with self.assertRaises(TimeoutError): normalize(raw(),time.time(),deadline=time.monotonic()-1)
        from portal.remote_reader import collect as remote_collect, OperationRejected
        with self.assertRaises(OperationRejected):
            remote_collect({'diagnostic':True,'morosity':{}},connect=MagicMock())

    def test_remote_ca_tls_login_and_read_failures_close_resources(self):
        from portal.remote_reader import collect as remote_collect, OperationRejected
        from librouteros.exceptions import TrapError
        config={'diagnostic':True,'router_host':'198.51.100.1','router_user':'read',
                'router_password':'SECRET','ca_file':'~/only-test.crt'}
        with patch('portal.remote_reader.sys.stdout',io.StringIO()):
            for exc, code in [(FileNotFoundError(),'ca_missing'),(ssl.SSLError(),'ca_invalid')]:
                factory=MagicMock()
                with patch('portal.remote_reader.ssl.create_default_context',side_effect=exc), self.assertRaises(OperationRejected) as caught:
                    remote_collect(config,connect=factory)
                self.assertEqual(str(caught.exception),code);factory.assert_not_called()
            with patch('portal.remote_reader.ssl.create_default_context') as context:
                sock=MagicMock();context.return_value.wrap_socket.side_effect=ssl.SSLError('SECRET')
                def failed_tls(**kwargs): return kwargs['ssl_wrapper'](sock)
                with self.assertRaises(ssl.SSLError): remote_collect(config,connect=failed_tls)
                sock.close.assert_called_once()
            with patch('portal.remote_reader.ssl.create_default_context'):
                api=MagicMock(side_effect=TrapError('SECRET'))
                def rejected_login(**kwargs):
                    kwargs['login_method'](api,kwargs['username'],kwargs['password'])
                with self.assertRaises(OperationRejected) as caught: remote_collect(config,connect=rejected_login)
                self.assertEqual(str(caught.exception),'api_auth')
                with self.assertRaises(TrapError): remote_collect(config,connect=MagicMock(return_value=api))
                api.close.assert_called_once()


class DiagnosticIntegrationTests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]/'.local'/'tmp';root.mkdir(parents=True,exist_ok=True)
        folder = tempfile.TemporaryDirectory(dir=root);self.addCleanup(folder.cleanup)
        settings = override_settings(STATE_DIR=Path(folder.name));settings.enable();self.addCleanup(settings.disable)
        session=self.client.session;session['desktop']=identity();session.save();self.client.cookies['spicyops_portal']=session.session_key
        self.profile = {'id':'one','name':'Prueba','host':'127.0.0.1','port':22,'ssh_user':'test',
                        'connected':True,'last_error':'Error anterior','ssh_password':'SECRET',
                        'history':[normalize(raw(),1000)],'metadata':{},'last_read':1000}
        Store().update(lambda data:data['profiles'].update(one=copy.deepcopy(self.profile),two=dict(copy.deepcopy(self.profile),id='two')))

    def test_background_duplicate_operations_and_locality_isolation(self):
        entered=threading.Event();release=threading.Event();done=threading.Event()
        def blocked(profile, *, progress):
            entered.set();release.wait(3)
            return controlled()(profile,progress=progress)
        original_run = d.run
        def run(*args):
            try: return original_run(*args)
            finally: done.set()
        with patch.object(d,'collect',side_effect=blocked),patch.object(d,'run',side_effect=run),patch('portal.views.collect') as other:
            try:
                response=self.client.post('/conexiones/one/diagnosticar/')
                self.assertEqual(response.status_code,202);self.assertTrue(entered.wait(1))
                self.assertEqual(self.client.post('/conexiones/one/diagnosticar/').status_code,409)
                with self.assertRaises(ValueError): refresh_profile('one')
                self.client.post('/conexiones/one/desconectar/')
                self.client.post('/conexiones/one/configurar/',{})
                self.client.post('/clientes/one/*1/morosidad/',{'action':'suspend','confirmed':'yes'})
                other.assert_not_called()
                self.assertEqual(self.client.get('/conexiones/one/diagnostico/').json()['running'],True)
                # Una localidad ocupada no bloquea el trabajo en otra.
                other.return_value=raw();refresh_profile('two')
            finally: release.set();self.assertTrue(done.wait(3))
        current=Store().read()['profiles']['one']
        for field in ('last_read','last_error','connected','history','ssh_password'):
            self.assertEqual(current[field],self.profile[field])
        self.assertFalse(current['diagnostic']['running']);self.assertFalse(current['busy_until'])
        page=self.client.get('/conexiones/')
        self.assertContains(page,'Resultado guardado (histórico)');self.assertNotContains(page,'SECRET')

    @patch('portal.diagnostics.threading.Thread')
    def test_busy_locality_rejects_diagnostic_and_crash_recovery(self, thread):
        Store().update(lambda data:data['profiles']['one'].update(busy_until=time.time()+20))
        self.assertEqual(self.client.post('/conexiones/one/diagnosticar/').status_code,409);thread.assert_not_called()
        result=d.fresh_result();d.set_stage(result,'reader','comprobando')
        Store().update(lambda data:data['profiles']['one'].update(busy_until=0,diagnostic=result))
        recovered=self.client.get('/conexiones/one/diagnostico/').json()
        self.assertFalse(recovered['running']);self.assertIn('interrumpió',recovered['summary'])
        self.assertTrue(any(r['state']=='no_comprobada' for r in recovered['stages']))

    def test_auth_csrf_and_unknown_profile(self):
        self.assertEqual(Client().get('/conexiones/one/diagnostico/').status_code,401)
        self.assertEqual(self.client.get('/conexiones/unknown/diagnostico/').status_code,404)
        self.assertEqual(self.client.get('/conexiones/one/diagnosticar/').status_code,405)
        self.assertEqual(self.client.get('/conexiones/one/diagnostico/',REMOTE_ADDR='198.51.100.3').status_code,403)
        client=Client(enforce_csrf_checks=True);client.cookies=self.client.cookies
        self.assertEqual(client.post('/conexiones/one/diagnosticar/').status_code,403)

    def test_automatic_sync_skips_diagnostic_and_continues_other_locality(self):
        from portal.scheduling import Coordinator
        entered=threading.Event();release=threading.Event();done=threading.Event()
        def blocked(profile, *, progress):
            entered.set();release.wait(3)
            return controlled()(profile,progress=progress)
        original_run=d.run
        def run(*args):
            try: original_run(*args)
            finally: done.set()
        with patch.object(d,'collect',side_effect=blocked),patch.object(d,'run',side_effect=run):
            try:
                self.assertEqual(self.client.post('/conexiones/one/diagnosticar/').status_code,202)
                self.assertTrue(entered.wait(1))
                def enable(data):
                    for p in data['profiles'].values(): p['automatic']={'enabled':True,'interval':5,'next_at':time.time()-1}
                Store().update(enable)
                reader=MagicMock()
                coordinator=Coordinator(reader)
                try:
                    coordinator.tick()
                    for future in coordinator.pending.values(): future.result(timeout=1)
                    reader.assert_called_once_with('two')
                finally: coordinator.stop()
            finally: release.set();self.assertTrue(done.wait(3))

    @patch('portal.views.collect',return_value=raw())
    def test_configuration_invalidates_saved_result_and_retains_it(self, collect):
        from .test_app import AppTests
        payload={'name':'Prueba','host':'127.0.0.1','port':22,'ssh_user':'test','ssh_method':'password',
                 'ssh_password':'test','router_user':'read','router_password':'test','ca_file':'~/ca.crt','python_path':'~/bin/python'}
        result=d.fresh_result()
        with patch.object(d,'collect',side_effect=controlled()): d.run({},result,lambda r:None)
        Store().update(lambda data:data['profiles']['one'].update(diagnostic=result))
        self.assertEqual(self.client.post('/conexiones/one/configurar/',payload).status_code,302)
        self.assertTrue(Store().read()['profiles']['one']['diagnostic']['stale'])
        self.assertContains(self.client.get('/conexiones/'),'Resultado desactualizado')
