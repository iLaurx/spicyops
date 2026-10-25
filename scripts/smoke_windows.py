"""Prueba del ejecutable construido, sin ventana y sin equipos externos."""
import http.cookiejar
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import re
import socket
from urllib.parse import urlencode
from urllib.request import build_opener,HTTPCookieProcessor,ProxyHandler,Request
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','spicyops.portal_settings')
from portal.version import VERSION

def start(exe,state,extra=()):
    (state/'runtime.json').unlink(missing_ok=True)
    process=subprocess.Popen([str(exe),'--no-open','--state-dir',str(state),*extra],cwd=ROOT,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for _ in range(80):
        if (state/'runtime.json').exists():break
        if process.poll() is not None:raise AssertionError('El ejecutable no arrancó; consultar startup-error.json de la prueba.')
        time.sleep(.15)
    assert (state/'runtime.json').exists(),'El ejecutable no publicó su estado de arranque.'
    runtime=json.loads((state/'runtime.json').read_text())
    opener=build_opener(ProxyHandler({}),HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for _ in range(30):
        try:
            page=opener.open(runtime['launch_url'],timeout=2).read().decode();break
        except OSError:time.sleep(.1)
    else:raise AssertionError('El servidor embebido no respondió.')
    return process,runtime,opener,page

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--exe',type=Path,default=ROOT/'dist'/f'SpicyOps-{VERSION}-Windows'/'SpicyOps'/'SpicyOps.exe')
    exe=parser.parse_args().exe.resolve()
    assert exe.exists(),'Construir primero SpicyOps.exe.'
    root=ROOT/'.local'/'tmp';root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        state=Path(folder)
        assert state.resolve().is_relative_to(root.resolve())
        process=None
        try:
            process,runtime,opener,page=start(exe,state)
            assert 'Nueva localidad' in page
            assert 'Marina' not in page
            base=f'http://127.0.0.1:{runtime["port"]}'
            for path,needle in [('/clientes/','Sin clientes'),('/conexiones/','Conecta tu primera localidad'),
                ('/conexiones/nueva/','ACCESO A RASPBERRY'),('/static/portal/app.css','.sidebar')]:
                assert needle in opener.open(base+path,timeout=5).read().decode(),path
            try:opener.open(base+'/open/forged/',timeout=5)
            except HTTPError as error:assert error.code==401
            else:raise AssertionError('Apertura sin firma admitida.')
            assert (state/'secret.dpapi').exists()
            assert not (state/'secret.key').exists()
            # Una segunda apertura reutiliza la instalación; no crea otro servidor.
            existing=json.loads((state/'runtime.json').read_text())['pid']
            other=subprocess.run([str(exe),'--no-open','--state-dir',str(state)],cwd=ROOT,timeout=10)
            assert other.returncode==0
            assert json.loads((state/'runtime.json').read_text())['pid']==existing
            process.terminate();process.wait(timeout=10);process=None
            from portal.secret import dpapi
            secret=dpapi((state/'secret.dpapi').read_bytes(),decrypt=True).decode()
            import django
            django.setup()
            from django.test import override_settings
            from portal.store import Store
            from portal.telemetry import normalize
            from portal.tests.test_telemetry import raw
            # Exclusivo de esta carpeta temporal de test; nunca se incorpora al programa o la vista del usuario.
            sample_time=time.time()
            previous_sample=normalize(raw(),sample_time-120)
            synthetic_raw=raw('200000000/400000000','1h2m')
            synthetic_raw['queues'].append(dict(synthetic_raw['queues'][0], **{
                '.id':'*EXCLUDED', 'name':'Cola filtrada exclusiva de test', 'target':'198.51.100.50/32'}))
            sample=normalize(synthetic_raw,sample_time)
            profile={'id':'smoke','name':'Localidad exclusiva de test','host':'127.0.0.1','ssh_user':'test',
                'connected':True,'last_read':sample['timestamp'],'last_error':'','history':[previous_sample,sample],
                'metadata':{'*1|198.51.100.20':{'alias':'Persistencia compilada verificada'}}}
            # Puerto reservado en loopback sin listen: rechazo controlado, sin red externa.
            rejected=socket.socket();rejected.bind(('127.0.0.1',0))
            profile['port']=rejected.getsockname()[1]
            with override_settings(STATE_DIR=state,SECRET_KEY=secret):
                Store().update(lambda d:d['profiles'].update(smoke=profile))
                other_profile = dict(profile, id='second', name='Segunda localidad de test',
                    metadata={'*1|198.51.100.20': {'alias': 'Cliente segunda localidad'}})
                offline = dict(profile, id='offline', name='Localidad desconectada de test', connected=False,
                    metadata={'*1|198.51.100.20': {'alias': 'Cliente desconectado'}})
                failed = dict(profile, id='failed', name='Localidad con error de test',
                    last_error='Fallo exclusivo de prueba', history=[])
                Store().update(lambda d:d['profiles'].update(second=other_profile, offline=offline, failed=failed))
            process,runtime,opener,page=start(exe,state)
            base=f'http://127.0.0.1:{runtime["port"]}'
            analytics = opener.open(base+'/?site=smoke',timeout=5).read().decode()
            from portal.templatetags.portal_tags import chart_datetime
            assert 'class="bar-date"' in analytics
            assert 'GB por barra' in analytics
            assert 'Consumo observado' in analytics
            assert 'Actualizar lectura' in analytics
            assert 'Estimación por cliente' in analytics
            assert 'Estimado en 24 horas' in analytics
            assert 'Estimado a 30 días' in analytics
            assert 'Aproximación desde encendido' in analytics
            assert 'Periodo analizado' not in analytics
            assert 'name="mode"' not in analytics
            assert f'{chart_datetime(previous_sample["timestamp"])} → {chart_datetime(sample["timestamp"])}' in analytics
            clients = opener.open(base+'/clientes/?site=smoke',timeout=5).read().decode()
            assert 'Persistencia compilada verificada' in clients
            assert 'Suspender cliente' in clients
            assert 'role="switch" aria-checked="false"' in clients
            assert '<th>Suspender</th>' in clients
            assert 'Habilitada' in clients
            assert 'Cola habilitada' not in clients
            assert 'Confirmar suspensión' in clients
            assert '/clientes/smoke/*1/morosidad/' in clients
            assert '198.51.100.20' in clients
            assert 'class="connection-status online"' in clients
            assert 'Revisar colas excluidas' in clients
            inventory=opener.open(base+'/inventario/smoke/',timeout=5).read().decode()
            assert 'Cola filtrada exclusiva de test' in inventory and 'Incluir en Clientes' in inventory
            excluded=sample['inventory'][0]
            def inventory_change(action):
                page=opener.open(base+'/inventario/smoke/',timeout=5).read().decode()
                csrf=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',page)[1]
                return opener.open(Request(base+'/inventario/smoke/',data=urlencode(dict(
                    csrfmiddlewaretoken=csrf, action=action, fingerprint=excluded['fingerprint'],
                    reading=str(sample['timestamp']))).encode()),timeout=5).read().decode()
            assert 'Revertir inclusión' in inventory_change('include')
            included=opener.open(base+'/clientes/?site=smoke',timeout=5).read().decode()
            assert 'Cola filtrada exclusiva de test' in included
            assert 'Incluir en Clientes' in inventory_change('revert')
            with override_settings(STATE_DIR=state,SECRET_KEY=secret):
                assert Store().read()['profiles']['smoke']['inclusions']==[]
            connections = opener.open(base+'/conexiones/',timeout=5).read().decode()
            for status in ('online', 'error', 'offline'):
                assert f'class="connection-status {status}"' in connections
            assert 'Error de conexión' in connections
            assert 'Desconectada' in connections
            assert 'Actualización automática' in connections
            assert 'value="5" selected' in connections
            assert 'Desactivada · Próxima: —' in connections
            assert 'Última lectura:' in connections
            assert 'data-notice' in connections
            javascript=opener.open(base+'/static/portal/app.js',timeout=5).read().decode()
            assert 'Cerrar aviso' in javascript and 'Date.now()+6000' in javascript
            # Persistencia de preferencias en el ejecutable, sin activar accesos.
            assert 'data-live-revision' in connections
            assert 'Diagnosticar' in connections
            csrf=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',connections)[1]
            submitted=opener.open(Request(base+'/conexiones/smoke/diagnosticar/',
                data=urlencode({'csrfmiddlewaretoken':csrf}).encode()),timeout=5)
            assert submitted.status==202
            result=None
            for _ in range(100):
                result=json.loads(opener.open(base+'/conexiones/smoke/diagnostico/',timeout=5).read())
                if not result['running']:break
                time.sleep(.15)
            rejected.close()
            assert result and not result['running']
            assert result['stages'][0]['code']=='refused',result
            assert all(step['state']=='no_comprobada' for step in result['stages'][1:])
            with override_settings(STATE_DIR=state,SECRET_KEY=secret):
                saved=Store().read()['profiles']['smoke']
                assert saved['history']==[previous_sample,sample]
                assert saved['connected'] and saved['last_error']==''
            restored=opener.open(base+'/conexiones/',timeout=5).read().decode()
            assert 'Resultado guardado (histórico)' in restored
            combined = opener.open(base+'/clientes/?site=all',timeout=5).read().decode()
            assert 'value="all" selected' in combined
            assert 'Persistencia compilada verificada' in combined
            assert 'Cliente segunda localidad' in combined
            assert 'Cliente desconectado' not in combined
            assert '/clientes/smoke/*1/datos/' in combined
            assert '/clientes/second/*1/morosidad/' in combined
            assert 'SUSPENSIÓN · Segunda localidad de test' in combined
            combined = opener.open(base+'/clientes/?q=segunda',timeout=5).read().decode()
            assert 'Cliente segunda localidad' in combined
            assert 'Persistencia compilada verificada' not in combined
            # Coordinador del EXE sin ventanas: servidor SSH efímero en loopback.
            from portal.tests.test_connector import ssh_reader
            with ssh_reader() as (access, observed):
                auto_profile = dict(access, id='automatic-smoke', name='Autolectura exclusiva de test',
                    connected=True, last_error='', last_read=sample['timestamp'], history=[sample],
                    metadata={'*1|198.51.100.20': {'alias': 'Nota conservada en autolectura'}},
                    automatic={'enabled':True,'interval':5,'failures':0,'next_at':time.time()})
                with override_settings(STATE_DIR=state,SECRET_KEY=secret):
                    Store().update(lambda d:d['profiles'].update({'automatic-smoke':auto_profile}))
                    for _ in range(60):
                        result=Store().read()['profiles']['automatic-smoke']
                        if result.get('last_attempt'):break
                        time.sleep(.1)
                    assert observed['authenticated'],'El EXE no inició la autolectura en loopback.'
                    assert len(result['history'])==2 and not result['last_error'],result.get('last_error')
                    assert result['metadata']==auto_profile['metadata']
                    assert result['automatic']['next_at']>time.time()+250
                    assert 'morosity' not in observed['payload']
                    assert result['automatic']['enabled']
            process.terminate();process.wait(timeout=10);process=None
            process,runtime,opener,page=start(exe,state)
            with override_settings(STATE_DIR=state,SECRET_KEY=secret):
                restored=Store().read()['profiles']['automatic-smoke']
                assert restored['automatic']['enabled'] and restored['automatic']['interval']==5
                assert len(restored['history'])==2 and restored['metadata']==auto_profile['metadata']
                assert restored['automatic']['next_at']>time.time()+250
            print('OK: coordinador del EXE sin ventanas, autolectura SSH loopback solo de lectura y preferencias conservadas al reiniciar.')
            print('OK: EXE Windows arranca, usa DPAPI, conserva datos y ejecuta diagnóstico de puerto rechazado en loopback sin alterar lecturas ni conexión.')
        finally:
            if process and process.poll() is None:process.terminate();process.wait(timeout=10)

if __name__=='__main__':main()
