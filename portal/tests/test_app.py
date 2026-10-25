import json
from pathlib import Path
import tempfile
import time
from unittest.mock import patch
from django.core import signing
from django.test import Client, SimpleTestCase, override_settings
from portal.auth import identity
from portal.connector import ConnectionFailure
from portal.store import Store
from portal.telemetry import normalize
from portal.views import refresh_profile
from .test_telemetry import raw

class AppTests(SimpleTestCase):
    @patch('portal.views.collect')
    def test_all_clients_keeps_overlapping_ips_and_actions_scoped(self, reader):
        self.profile(); self.profile('two'); self.profile('offline')
        def prepare(data):
            data['profiles']['one']['name'] = 'Norte'
            data['profiles']['two'].update(name='Sur', last_error='Error de lectura')
            data['profiles']['offline'].update(name='Desconectada', connected=False)
        Store().update(prepare)
        page = self.client.get('/clientes/?site=all')
        self.assertTrue(page.context['all_sites'])
        self.assertEqual(page.context['total_clients'], 2)
        self.assertEqual({r['locality_id'] for r in page.context['rows']}, {'one', 'two'})
        self.assertContains(page, '/clientes/one/*1/datos/')
        self.assertContains(page, '/clientes/two/*1/morosidad/')
        self.assertContains(page, 'SUSPENSIÓN · Sur')
        self.assertContains(page, 'Error de lectura · Datos guardados')
        self.assertNotContains(page, '/clientes/offline/*1/datos/')
        self.assertNotContains(page, 'test-only-ssh')
        self.assertEqual(len(self.client.get('/clientes/?q=Sur').context['rows']), 1)
        self.client.post('/clientes/two/*1/datos/', {'alias': 'Alias del sur'})
        self.assertTrue(self.client.get('/clientes/').context['all_sites'])
        state = Store().read()['profiles']
        self.assertEqual(state['one']['metadata'], {})
        self.assertEqual(state['two']['metadata']['*1|198.51.100.20']['alias'], 'Alias del sur')
        reader.assert_not_called()
        individual = self.client.get('/clientes/?site=offline')
        self.assertEqual(len(individual.context['rows']), 1)
        self.assertFalse(individual.context['all_sites'])

    @patch('portal.views.collect')
    def test_all_clients_empty_and_confirmed_morosity_keep_selection(self, reader):
        self.assertEqual(self.client.get('/clientes/?site=all').context['total_clients'], 0)
        self.profile(); self.profile('two')
        self.client.get('/clientes/?site=all')
        row = Store().read()['profiles']['two']['history'][-1]['clients'][0]
        result = raw()
        result['restrictions'] = [{'list': 'Morosos', 'address': row['ip'], 'disabled': False}]
        reader.return_value = result
        self.client.post('/clientes/two/*1/morosidad/',
            {'confirmed': 'yes', 'fingerprint': row['fingerprint'], 'action': 'suspend'})
        self.assertEqual(reader.call_args.args[0]['id'], 'two')
        self.assertTrue(self.client.get('/clientes/').context['all_sites'])
        state = Store().read()['profiles']
        self.assertFalse(state['one']['history'][-1]['clients'][0]['restricted'])
        self.assertTrue(state['two']['history'][-1]['clients'][0]['restricted'])
        self.client.post('/conexiones/one/desconectar/')
        self.client.post('/conexiones/two/desconectar/')
        self.assertEqual(self.client.get('/clientes/?site=all').context['total_clients'], 0)

    @patch('portal.views.collect')
    def test_reconfigure_and_disconnect_cannot_replace_inflight_operation(self, reader):
        self.profile()
        def concurrent_operation(profile):
            Store().update(lambda d: d['profiles']['one'].update(generation='write-inflight', busy_until=time.time()+60))
            return raw()
        reader.side_effect = concurrent_operation
        payload = dict(self.payload, name='Replacement', ssh_password='', router_password='')
        response = self.client.post('/conexiones/one/configurar/', payload)
        self.assertContains(response, 'operación en curso')
        current = Store().read()['profiles']['one']
        self.assertEqual(current['generation'], 'write-inflight')
        self.assertNotEqual(current['name'], 'Replacement')
        self.client.post('/conexiones/one/desconectar/')
        current = Store().read()['profiles']['one']
        self.assertTrue(current['connected'])
        self.assertEqual(current['generation'], 'write-inflight')

    @patch('portal.views.collect')
    def test_morosity_confirm_suspend_restore_and_locality_isolation(self, reader):
        self.profile(); self.profile('two')
        row = Store().read()['profiles']['one']['history'][-1]['clients'][0]
        payload = {'confirmed': 'yes', 'fingerprint': row['fingerprint'], 'action': 'suspend'}
        page = self.client.get('/clientes/?site=one')
        self.assertContains(page, 'Suspender cliente')
        self.assertContains(page, 'Confirmar suspensión')
        result = raw()
        result['restrictions'] = [{'list': 'Morosos', 'address': row['ip'], 'disabled': False}]
        reader.return_value = result
        self.assertEqual(self.client.post('/clientes/one/*1/morosidad/', payload).status_code, 302)
        state = Store().read()
        self.assertTrue(state['profiles']['one']['history'][-1]['clients'][0]['restricted'])
        self.assertFalse(state['profiles']['two']['history'][-1]['clients'][0]['restricted'])
        self.assertEqual(reader.call_args.kwargs['morosity']['ip'], row['ip'])
        self.assertContains(self.client.get('/clientes/'), 'Reactivar cliente')
        # El mismo envío obsoleto no vuelve a ejecutar el conector.
        reader.reset_mock()
        self.client.post('/clientes/one/*1/morosidad/', payload)
        reader.assert_not_called()
        reader.return_value = raw()
        payload['action'] = 'restore'
        self.client.post('/clientes/one/*1/morosidad/', payload)
        self.assertFalse(Store().read()['profiles']['one']['history'][-1]['clients'][0]['restricted'])

    @patch('portal.views.collect')
    def test_morosity_rejects_invalid_unconfirmed_stale_disconnected_and_busy(self, reader):
        self.profile()
        row = Store().read()['profiles']['one']['history'][-1]['clients'][0]
        payload = {'confirmed': 'yes', 'fingerprint': row['fingerprint'], 'action': 'suspend'}
        url = '/clientes/one/*1/morosidad/'
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, dict(payload, confirmed='')).status_code, 400)
        self.assertEqual(self.client.post(url, dict(payload, action='reboot')).status_code, 400)
        self.client.post(url, dict(payload, fingerprint='stale'))
        self.client.post('/clientes/two/*1/morosidad/', payload)
        for values in ({'connected': False}, {'connected': True, 'busy_until': time.time()+60},
                       {'busy_until': 0, 'last_error': 'Resultado incierto'}):
            Store().update(lambda d: d['profiles']['one'].update(values))
            self.client.post(url, payload)
        reader.assert_not_called()
        client = Client(enforce_csrf_checks=True)
        session = client.session; session['desktop'] = identity(); session.save()
        client.cookies['spicyops_portal'] = session.session_key
        self.assertEqual(client.post(url, payload).status_code, 403)
        self.assertEqual(Client().post(url, payload).status_code, 401)

    @patch('portal.views.collect')
    def test_morosity_failed_write_preserves_observed_state_and_requires_refresh(self, reader):
        profile = self.profile()
        row = profile['history'][-1]['clients'][0]
        payload = {'confirmed': 'yes', 'fingerprint': row['fingerprint'], 'action': 'suspend'}
        reader.side_effect = ConnectionFailure('No se pudo confirmar')
        self.client.post('/clientes/one/*1/morosidad/', payload)
        current = Store().read()['profiles']['one']
        self.assertEqual(current['history'], profile['history'])
        self.assertFalse(current['busy_until'])
        self.assertIn('incierto', current['last_error'])
        reader.reset_mock()
        self.client.post('/clientes/one/*1/morosidad/', payload)
        reader.assert_not_called()

    def setUp(self):
        # Todos los archivos efímeros de test se guardan dentro del proyecto.
        root=Path(__file__).resolve().parents[2]/'.local'/'tmp'
        root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.override=override_settings(STATE_DIR=Path(self.temp.name))
        self.override.enable();self.addCleanup(self.override.disable)
        session=self.client.session;session['desktop']=identity();session.save()
        self.client.cookies['spicyops_portal']=session.session_key
        self.payload={'name':'Localidad de test','host':'127.0.0.1','port':22,'ssh_user':'test','ssh_method':'password','ssh_password':'test-only-ssh',
            'key_file':'','router_host':'198.51.100.1','router_user':'read','router_password':'test-only-api',
            'ca_file':'~/test-ca.crt','python_path':'~/test-venv/bin/python','fingerprint':''}

    def profile(self,profile_id='one'):
        profile=dict(self.payload,id=profile_id,connected=True,last_error='',last_read=time.time(),
            history=[normalize(raw(),time.time())],metadata={})
        Store().update(lambda data:data['profiles'].update({profile_id:profile}))
        return profile

    def test_empty_application_has_navigation_without_demo_or_database(self):
        response=self.client.get('/')
        self.assertContains(response,'Analytics')
        self.assertContains(response,'Clientes')
        self.assertContains(response,'Nueva localidad')
        self.assertNotContains(response,'Marina')
        self.assertNotContains(response,'2000/4000')
        self.assertEqual(Store().read()['profiles'],{})
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertIn("frame-ancestors 'none'",response['Content-Security-Policy'])

    def test_no_launch_session_cannot_read_or_connect(self):
        client=Client()
        self.assertEqual(client.get('/').status_code,401)
        self.assertEqual(client.post('/conexiones/nueva/',self.payload).status_code,401)
        self.assertEqual(client.get('/',REMOTE_ADDR='198.51.100.70').status_code,403)

    def test_signed_desktop_launch_authenticates_without_account_or_db(self):
        client=Client();token=signing.dumps('open',salt='spicyops-desktop-open')
        response=client.get('/open/'+token+'/')
        self.assertEqual(response.status_code,302)
        self.assertEqual(client.get('/').status_code,200)
        self.assertEqual(client.get('/open/forged/').status_code,401)

    def test_profile_and_credentials_are_encrypted_and_reloadable(self):
        self.profile()
        file=Path(self.temp.name)/'connections.enc'
        contents=file.read_bytes()
        self.assertNotIn(b'test-only-ssh',contents)
        self.assertNotIn(b'198.51.100.20',contents)
        self.assertEqual(Store().read()['profiles']['one']['ssh_user'],'test')

    @patch('portal.views.collect')
    def test_connect_imports_actual_connector_result_and_never_renders_passwords(self,reader):
        reader.return_value=raw()
        response=self.client.post('/conexiones/nueva/',self.payload)
        self.assertEqual(response.status_code,302)
        self.assertEqual(len(Store().read()['profiles']),1)
        page=self.client.get('/clientes/')
        self.assertContains(page,'Abonado de test')
        self.assertContains(page,'2 / 4')
        self.assertNotContains(page,'test-only-ssh')
        self.assertNotContains(page,'test-only-api')

    @patch('portal.views.collect')
    def test_failed_connection_does_not_fabricate_clients(self,reader):
        reader.side_effect=ConnectionFailure('Raspberry conectada. MikroTik no disponible.',stage='router')
        response=self.client.post('/conexiones/nueva/',self.payload)
        self.assertContains(response,'MikroTik no disponible')
        self.assertEqual(Store().read()['profiles'],{})

    @patch('portal.views.collect')
    def test_host_key_confirmation_preserves_secrets_only_in_vault(self,reader):
        fingerprint='SHA256:'+'A'*43
        reader.side_effect=ConnectionFailure('Confirma la huella',fingerprint=fingerprint)
        response=self.client.post('/conexiones/nueva/',self.payload)
        self.assertContains(response,fingerprint)
        self.assertNotContains(response,'value="test-only-ssh"')
        payload=dict(self.payload,ssh_password='',router_password='',fingerprint=fingerprint)
        reader.side_effect=None;reader.return_value=raw()
        response=self.client.post('/conexiones/nueva/',payload)
        self.assertEqual(response.status_code,302)
        self.assertEqual(reader.call_args.args[0]['ssh_password'],'test-only-ssh')

    @patch('portal.views.collect')
    def test_read_failure_preserves_previous_data_and_marks_error(self,reader):
        profile=self.profile()
        reader.side_effect=ConnectionFailure('No se pudo leer')
        error=refresh_profile('one')
        self.assertEqual(error,'No se pudo leer')
        current=Store().read()['profiles']['one']
        self.assertEqual(current['history'],profile['history'])
        self.assertEqual(current['last_error'],error)
        self.assertFalse(current['busy_until'])

    @patch('portal.views.collect')
    def test_metadata_persists_across_refresh_and_is_scoped_by_locality(self,reader):
        self.profile();self.profile('two')
        response=self.client.post('/clientes/one/*1/datos/',{'alias':'Alias persistente','contact':'Contacto de test','location':'Ubicación de test','notes':'Nota de test'})
        self.assertEqual(response.status_code,302)
        reader.return_value=raw()
        refresh_profile('one')
        store=Store().read()
        self.assertEqual(store['profiles']['one']['metadata']['*1|198.51.100.20']['alias'],'Alias persistente')
        self.assertEqual(store['profiles']['two']['metadata'],{})
        self.assertContains(self.client.get('/clientes/?site=one'),'Alias persistente')
        self.assertNotContains(self.client.get('/clientes/?site=two'),'Alias persistente')

    def test_csrf_required_for_connections_and_metadata(self):
        client=Client(enforce_csrf_checks=True)
        session=client.session;session['desktop']=identity();session.save();client.cookies['spicyops_portal']=session.session_key
        self.assertEqual(client.post('/conexiones/nueva/',self.payload).status_code,403)
        self.assertEqual(client.post('/clientes/one/*1/datos/',{}).status_code,403)

    @patch('portal.views.collect')
    def test_reconnect_same_profile_retains_metadata_without_duplicate_locality(self,reader):
        self.profile()
        self.client.post('/clientes/one/*1/datos/',{'alias':'Persistente'})
        reader.return_value=raw()
        payload=dict(self.payload,ssh_password='',router_password='')
        self.assertEqual(self.client.post('/conexiones/one/configurar/',payload).status_code,302)
        self.assertEqual(len(Store().read()['profiles']),1)
        self.assertEqual(Store().read()['profiles']['one']['metadata']['*1|198.51.100.20']['alias'],'Persistente')

    def test_disconnect_removes_secrets_but_retains_notes_and_last_read(self):
        self.profile()
        self.client.post('/conexiones/one/desconectar/')
        profile=Store().read()['profiles']['one']
        self.assertFalse(profile['connected'])
        self.assertEqual(profile['ssh_password'],'')
        self.assertEqual(profile['router_password'],'')
        self.assertEqual(len(profile['history']),1)
        with self.assertRaises(ValueError):refresh_profile('one')

    def test_credentials_do_not_appear_in_signed_browser_session(self):
        self.profile()
        self.client.get('/?site=one')
        session=dict(self.client.session)
        self.assertNotIn('test-only-ssh',json.dumps(session))
        self.assertNotIn('router_password',json.dumps(session))

    def test_inflight_read_cannot_be_reclaimed_simultaneously(self):
        profile=self.profile()
        Store().update(lambda d:d['profiles']['one'].update(busy_until=time.time()+50))
        with self.assertRaises(ValueError):refresh_profile('one')

    @patch('portal.views.collect')
    def test_refresh_keeps_chart_and_only_uptime_estimates(self,reader):
        self.profile()
        old=normalize(raw('100/200','1h'),time.time()-120)
        Store().update(lambda d:d['profiles']['one'].update(history=[old]))
        reader.return_value=raw('200/400','1h2m')
        self.client.post('/conexiones/one/leer/',{'mode':'uptime'})
        response=self.client.get('/?mode=interval')
        self.assertContains(response,'Consumo observado')
        self.assertContains(response,'Actualizar lectura')
        self.assertContains(response,'class="bar-date"')
        self.assertEqual(response.context['bars'][0]['bytes'],300)
        self.assertContains(response,'Estimación por cliente')
        self.assertContains(response,'Estimado en 24 horas')
        self.assertContains(response,'Estimado a 30 días')
        self.assertNotContains(response,'historial válido')
        self.assertNotContains(response,'name="mode"')
        self.assertNotIn('mode',self.client.session)
        self.assertContains(response,'Aproximación desde encendido')
        self.assertNotContains(response,'Periodo analizado')
        self.assertAlmostEqual(response.context['rows'][0]['daily_bytes'],600/3720*86400)

    def test_chart_does_not_mix_restarts_or_counter_resets(self):
        self.profile()
        samples=[normalize(raw('100/200','1h'),10000),
            normalize(raw('200/400','1m'),10060),
            normalize(raw('50/500','2m'),10120),
            normalize(raw('100/600','3m'),10180)]
        Store().update(lambda d:d['profiles']['one'].update(history=samples))
        bars=self.client.get('/').context['bars']
        self.assertEqual(len(bars),1)
        self.assertEqual(bars[0]['bytes'],150)
        self.assertEqual(bars[0]['start'],10120)

    def test_metadata_cannot_target_unknown_client(self):
        self.profile()
        self.assertEqual(self.client.post('/clientes/one/unknown/datos/',{'alias':'No válido'}).status_code,400)

    def test_password_whitespace_is_preserved(self):
        from portal.forms import ConnectionForm
        payload=dict(self.payload,ssh_password=' ssh secret with spaces ',router_password=' api secret with spaces ')
        form=ConnectionForm(payload)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['ssh_password'],payload['ssh_password'])
        self.assertEqual(form.cleaned_data['router_password'],payload['router_password'])

    @patch('portal.views.collect')
    def test_switch_lan_to_tailscale_keeps_host_identity_and_metadata(self,reader):
        self.profile()
        fingerprint='SHA256:'+'A'*43
        Store().update(lambda d:d['profiles']['one'].update(fingerprint=fingerprint))
        self.client.post('/clientes/one/*1/datos/',{'alias':'Conservar al cambiar de red'})
        reader.return_value=raw()
        payload=dict(self.payload,host='100.64.0.2',fingerprint='SHA256:'+'B'*43,ssh_password='',router_password='')
        self.assertEqual(self.client.post('/conexiones/one/configurar/',payload).status_code,302)
        self.assertEqual(reader.call_args.args[0]['fingerprint'],fingerprint)
        profile=Store().read()['profiles']['one']
        self.assertEqual(profile['host'],'100.64.0.2')
        self.assertEqual(profile['metadata']['*1|198.51.100.20']['alias'],'Conservar al cambiar de red')
