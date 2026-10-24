"""Aceptación del EXE con datos sintéticos; no usa equipos reales."""
import os
import sys
from pathlib import Path
import tempfile
import subprocess
import time
import json
import re
import copy
from urllib.request import Request
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
os.environ.setdefault('SPICYOPS_STATE_DIR', str(ROOT/'build/release-tests/recovery-bootstrap'))
os.environ.pop('DJANGO_SECRET_KEY',None)
from smoke_windows import start
from portal.secret import dpapi
import django
django.setup()
from django.test import override_settings
from portal.store import Store
from portal.recovery import export_data
from portal.telemetry import normalize
from portal.tests.test_telemetry import raw
from portal.version import VERSION
EXE=ROOT/'dist'/f'SpicyOps-{VERSION}-Windows'/'SpicyOps/SpicyOps.exe'
OLD=ROOT/'dist/auditoria-20261022/SpicyOps/SpicyOps.exe'
PASSWORD='contraseña-solo-prueba-123'
process=None

def post(opener,runtime,path,fields,file=None):
    base=f'http://127.0.0.1:{runtime["port"]}'
    page=opener.open(base+'/respaldo/').read().decode()
    fields=dict(fields,csrfmiddlewaretoken=re.search('name="csrfmiddlewaretoken" value="([^"]+)"',page)[1])
    if file is None:
        body=urlencode(fields).encode();content_type='application/x-www-form-urlencoded'
    else:
        boundary='SpicyOpsSyntheticBoundary'
        chunks=[]
        for name,value in fields.items():
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="backup_file"; filename="synthetic.spicybackup"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+file+b'\r\n')
        chunks.append(f'--{boundary}--\r\n'.encode())
        body=b''.join(chunks);content_type='multipart/form-data; boundary='+boundary
    return opener.open(Request(base+path,data=body,headers={'Content-Type':content_type,'Referer':base+'/respaldo/'}),timeout=20).read()

def close():
    global process
    post(opener,runtime,'/salir/',{'confirmed':'yes'})
    process.wait(timeout=90)
    assert process.returncode==0
    process=None

def ui(state,mode):
    env=os.environ.copy()
    env['NODE_PATH']=str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    subprocess.run(['node',str(ROOT/'scripts/check_release_ui.cjs'),str(state/'runtime.json'),mode],env=env,check=True,timeout=60)

with tempfile.TemporaryDirectory(dir=ROOT/'build') as folder:
    state=Path(folder)
    try:
        process,runtime,opener,page=start(OLD,state)
        process.terminate();process.wait(timeout=10);process=None  # La versión histórica no tiene salida HTTP.
        secret=dpapi((state/'secret.dpapi').read_bytes(),decrypt=True).decode()
        sample=normalize(raw(),time.time())
        data={'owner':None,'login':{},'profiles':{'one':{'id':'one','name':'Localidad sintética','connected':False,
            'host':'127.0.0.1','ssh_user':'synthetic','history':[sample],
            'metadata':{'*1|198.51.100.20':{'alias':'Conservar alias','notes':'Conservar notas'}},
            'automatic':{'enabled':True,'interval':15}}}}
        with override_settings(STATE_DIR=state,SECRET_KEY=secret):
            store=Store()
            old_bytes=store.cipher.encrypt(json.dumps(data).encode())
            store.path.write_bytes(old_bytes)
        process,runtime,opener,page=start(OLD,state)
        assert 'Localidad sintética' in page
        process.terminate();process.wait(timeout=10);process=None
        # El formato anterior sigue sin campo format; la versión nueva lo migra al iniciar.
        process,runtime,opener,page=start(EXE,state,('--tray',))
        for _ in range(50):
            if json.loads((state/'runtime.json').read_text()).get('tray_ready'): break
            time.sleep(.1)
        else: raise AssertionError('La bandeja no se inicializó.')
        assert VERSION in page
        ui(state,'healthy')
        with override_settings(STATE_DIR=state,SECRET_KEY=secret):
            migrated=Store().read()
            assert migrated['format']==1
            assert migrated['profiles']['one']['history']==data['profiles']['one']['history']
            assert migrated['profiles']['one']['metadata']==data['profiles']['one']['metadata']
            assert migrated['profiles']['one']['automatic']['interval']==15
            assert any('format' not in Store().decode(p.read_bytes()) for p in (state/'backups').glob('*.enc'))
        portable=post(opener,runtime,'/respaldo/',{'action':'export','password':PASSWORD})
        assert portable.startswith(b'SPICYOPS-PORTABLE-1') and b'Conservar notas' not in portable
        close()
        damaged=b'corrupt-synthetic-state'
        (state/'connections.enc').write_bytes(damaged)
        process,runtime,opener,page=start(EXE,state)
        assert 'Respaldos y recuperación' in page
        ui(state,'corrupt')
        assert (state/'connections.enc').read_bytes()==damaged
        bad=post(opener,runtime,'/respaldo/',{'action':'import','password':'contraseña-incorrecta','confirmed':'yes'},portable)
        assert 'Contraseña incorrecta' in bad.decode()
        assert (state/'connections.enc').read_bytes()==damaged
        restored=post(opener,runtime,'/respaldo/',{'action':'import','password':PASSWORD,'confirmed':'yes'},portable)
        assert 'Restauración completada' in restored.decode()
        assert any((p/'connections.enc').read_bytes()==damaged for p in state.glob('original-*'))
        close()
        # Clave DPAPI corrupta: interfaz recuperable sin sustituirla hasta confirmar importación.
        badkey=b'bad-synthetic-key'
        (state/'secret.dpapi').write_bytes(badkey)
        process,runtime,opener,page=start(EXE,state)
        assert 'clave de esta cuenta Windows' in page
        assert (state/'secret.dpapi').read_bytes()==badkey
        restored=post(opener,runtime,'/respaldo/',{'action':'import','password':PASSWORD,'confirmed':'yes'},portable)
        assert 'Restauración completada' in restored.decode()
        close()
        process,runtime,opener,page=start(EXE,state)
        assert 'Localidad sintética' in page
        secret=dpapi((state/'secret.dpapi').read_bytes(),decrypt=True).decode()
        with override_settings(STATE_DIR=state,SECRET_KEY=secret):
            current=Store().read()['profiles']['one']
            assert current['history']==data['profiles']['one']['history']
            assert current['metadata']==data['profiles']['one']['metadata']
            assert current['automatic']['enabled'] and current['automatic']['interval']==15
            assert not current['connected']
        close()
        print('OK: dos versiones EXE, migración, bandeja nativa inicializada, cierre ordenado, recuperación de estado y clave, traslado con contraseña y reapertura con datos conservados.')
    finally:
        if process and process.poll() is None: process.terminate();process.wait(timeout=10)
