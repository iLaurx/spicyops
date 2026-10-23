import base64
from contextlib import contextmanager
import hashlib
import json
import secrets
import socket
import threading
import subprocess
import sys
import shlex
import time
from unittest.mock import MagicMock, patch
import paramiko
from django.test import SimpleTestCase
from portal.connector import collect, ConnectionFailure
from portal.remote_reader import collect as collect_router
from .test_telemetry import raw

@contextmanager
def ssh_reader(*, execute_reader=False, reader_delay=0):
    key=paramiko.RSAKey.generate(2048)
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(8)
    state={'authenticated':False,'command':'','payload':None}
    password=secrets.token_urlsafe(24)
    class Server(paramiko.ServerInterface):
        def __init__(self):self.ready=threading.Event()
        def get_allowed_auths(self,user):return 'password'
        def check_auth_password(self,user,supplied):
            state['authenticated']=user=='test' and supplied==password
            return paramiko.AUTH_SUCCESSFUL if state['authenticated'] else paramiko.AUTH_FAILED
        def check_channel_request(self,kind,channel_id):return paramiko.OPEN_SUCCEEDED
        def check_channel_exec_request(self,channel,command):
            state['command']=command.decode();self.ready.set();return True
    def serve():
        transport=None
        try:
            connection,_=listener.accept();transport=paramiko.Transport(connection);transport.add_server_key(key)
            server=Server();transport.start_server(server=server)
            channel=transport.accept(5)
            if not channel:return
            if not server.ready.wait(5):return
            payload=bytearray()
            while True:
                part=channel.recv(65536)
                if not part:break
                payload.extend(part)
            state['payload']=json.loads(payload)
            if reader_delay: time.sleep(reader_delay)
            if execute_reader:
                # Ejecutar exclusivamente el bootstrap recibido sobre esta PC
                # temporal, con una CA ausente que impide llegar a ninguna API.
                tokens=shlex.split(state['command'])
                assert tokens[:3]==['python3','-B','-c']
                result=subprocess.run([sys.executable,'-B','-c',tokens[3]],input=json.dumps(state['payload']),
                    text=True,capture_output=True,timeout=10,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                channel.sendall(result.stdout.encode());channel.send_exit_status(0);channel.close()
                return
            if state['payload'].get('diagnostic'):
                channel.sendall(b'{"event":"reader"}\n{"event":"tls"}\n')
            channel.sendall(json.dumps({'ok':True,'data':raw()}).encode())
            channel.send_exit_status(0)
            channel.close()
        except (EOFError,OSError,paramiko.SSHException):pass
        finally:
            if transport:transport.close()
    thread=threading.Thread(target=serve,daemon=True);thread.start()
    fingerprint='SHA256:'+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
    profile={'host':'127.0.0.1','port':listener.getsockname()[1],'ssh_user':'test','ssh_method':'password',
        'ssh_password':password,'fingerprint':fingerprint,'python_path':'~/test/bin/python',
        'router_host':'198.51.100.1','router_user':'read','router_password':secrets.token_urlsafe(24),'ca_file':'~/test.crt'}
    try:yield profile,state
    finally:listener.close();thread.join(timeout=6)

class ConnectorTests(SimpleTestCase):
    def test_total_deadline_stops_slow_reader_and_closes_ssh(self):
        with ssh_reader(reader_delay=.4) as (profile,state):
            before=time.monotonic()
            with self.assertRaises(ConnectionFailure) as caught:
                collect(profile,progress=lambda *event:None,total_timeout=.15)
            self.assertEqual(caught.exception.code,'timeout')
            self.assertLess(time.monotonic()-before,.7)

    def test_actual_bootstrap_missing_interpreter_and_ca_over_loopback(self):
        for missing_python, code, stage in [(True,'python_unavailable','reader'),(False,'ca_missing','tls')]:
            with self.subTest(code=code), ssh_reader(execute_reader=True) as (profile,state):
                profile['python_path'] = sys.executable+'.absent' if missing_python else sys.executable
                profile['ca_file'] = str(__import__('pathlib').Path(__file__).parent/'absent-test-ca.crt')
                with self.assertRaises(ConnectionFailure) as caught:
                    collect(profile,progress=lambda *event:None)
                self.assertEqual(caught.exception.code,code)
                self.assertEqual(caught.exception.stage,stage)

    def test_diagnostic_ssh_loopback_reports_verified_stages_and_is_read_only(self):
        events = []
        with ssh_reader() as (profile, state):
            collect(profile, progress=lambda *event: events.append(event))
            self.assertNotIn('morosity', state['payload'])
            self.assertEqual([s for s, status, code in events if status == 'correcto'],
                             ['access', 'identity', 'auth', 'reader', 'tls', 'api'])

    def test_actual_ssh_handshake_authentication_and_json_over_encrypted_stdin(self):
        with ssh_reader() as (profile,state):
            result=collect(profile)
            self.assertEqual(result['schema'],1)
            self.assertTrue(state['authenticated'])
            self.assertNotIn(profile['ssh_password'],state['command'])
            self.assertNotIn(profile['router_password'],state['command'])
            self.assertEqual(state['payload']['router_password'],profile['router_password'])
            self.assertIn('python3 -B -c ',state['command'])
            self.assertNotIn('pip install',state['command'])

    def test_unknown_host_stops_before_sending_password(self):
        with ssh_reader() as (profile,state):
            expected=profile['fingerprint'];profile['fingerprint']=''
            with self.assertRaises(ConnectionFailure) as caught:collect(profile)
            self.assertEqual(caught.exception.fingerprint,expected)
            self.assertFalse(state['authenticated'])

    def test_changed_host_pin_stops_before_authentication(self):
        with ssh_reader() as (profile,state):
            profile['fingerprint']='SHA256:'+'A'*43
            with self.assertRaises(ConnectionFailure) as caught:collect(profile)
            self.assertIn('cambió',str(caught.exception))
            self.assertFalse(state['authenticated'])

    @patch('portal.connector.paramiko.SSHClient')
    def test_auth_error_is_sanitized(self,client):
        client.return_value.connect.side_effect=paramiko.AuthenticationException('SENSITIVE_TEST_ONLY')
        profile={'host':'127.0.0.1','port':22,'ssh_user':'test','ssh_password':'not_real'}
        with patch('portal.connector.resolve_bounded', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1',22))]), \
                patch('portal.connector.socket.socket'), self.assertRaises(ConnectionFailure) as caught:
            collect(profile)
        self.assertTrue(client.return_value.connect.called)
        self.assertNotIn('SENSITIVE_TEST_ONLY',str(caught.exception))
        self.assertTrue(client.return_value.close.called)

    @patch('portal.remote_reader.ssl.create_default_context')
    def test_remote_collector_uses_only_read_paths_and_closes_api(self,tls):
        api=MagicMock()
        calls=[]
        def read(path,**options):
            calls.append((path,options))
            if path=='/system/resource/print':return iter([{'uptime':'1h','version':'6.49.23','board-name':'test'}])
            if path=='/system/identity/print':return iter([{'name':'Router test'}])
            if path=='/queue/simple/print':
                if 'stats' in options:return iter([{'.id':'*1','bytes':'100/200','rate':'0/0'}])
                return iter([{'.id':'*1','name':'test','target':'198.51.100.20/32','max-limit':'2M/4M'}])
            if path=='/ip/firewall/address-list/print':return iter([])
            raise AssertionError('No se permite escribir.')
        api.side_effect=read
        factory=MagicMock(return_value=api)
        result=collect_router({'router_host':'198.51.100.1','router_user':'read','router_password':'test-only','ca_file':'~/test.crt'},connect=factory)
        self.assertTrue(api.close.called)
        self.assertEqual(result['queues'][0]['bytes'],'100/200')
        self.assertTrue(all(path.endswith('/print') for path,_ in calls))
        self.assertEqual(factory.call_args.kwargs['port'],8729)
        self.assertEqual(tls.return_value.minimum_version,__import__('ssl').TLSVersion.TLSv1_2)
        wrapper=factory.call_args.kwargs['ssl_wrapper']
        self.assertEqual(wrapper.keywords['server_hostname'],'198.51.100.1')
