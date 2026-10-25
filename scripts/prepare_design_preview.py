"""Create isolated UI fixtures only under build/redesign; never operator state."""
import copy
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
state = ROOT / 'build/redesign/synthetic'
os.environ['SPICYOPS_STATE_DIR'] = str(state)
os.environ['DJANGO_SETTINGS_MODULE'] = 'spicyops.portal_settings'
import django
django.setup()
from portal.store import Store
from portal.telemetry import normalize
from portal.diagnostics import fresh_result

now = time.time()
profiles = {}
for key, name in [('north', 'Sierra Norte'), ('south', 'Valle del Sur')]:
    history = []
    for step in range(13):
        queues = []
        for index, alias in enumerate(['Casa del Roble', 'Taller de cerámica', 'Biblioteca comunitaria',
                                      'Centro de aprendizaje y servicios de la comunidad de Sierra Norte',
                                      'Tienda La Esquina', 'Estudio del Valle', 'Casa del Pino']):
            queues.append({'.id': f'*{index+1}', 'name': alias, 'target': f'198.51.100.{20+index}/32',
                           'max-limit': '5M/20M', 'bytes': f'{(index+1)*300000000+step*step*23000000}/{(index+1)*900000000+step*step*(index+1)*57000000}'})
        queues.append({'.id': '*99', 'name': 'Enlace de infraestructura', 'target': '198.51.100.0/24', 'bytes': '1000/2000'})
        source = {'schema': 1, 'router': {'identity': 'Router · ' + name, 'version': '7.20.1',
                  'uptime': f'{86400+step*7200}s'}, 'queues': queues, 'raspberry': {},
                  'restrictions': [{'list': 'Morosos', 'address': '198.51.100.22', 'disabled': False}]}
        history.append(normalize(source, now - (12-step)*7200))
    diagnostic = fresh_result()
    diagnostic.update(running=False, finished=now-120, summary='Lectura verificada en entorno sintético.')
    for stage in diagnostic['stages']:
        stage.update(state='correcto', message='Comprobación sintética para revisión visual.')
    profiles[key] = {'id': key, 'name': name, 'connected': True, 'host': '127.0.0.1', 'port': 1,
                     'ssh_user': 'synthetic', 'history': history, 'metadata': {}, 'last_read': now,
                     'automatic': {'enabled': False, 'interval': 5}, 'diagnostic': diagnostic}
Store().update(lambda data: data.update(profiles=copy.deepcopy(profiles)))
print('Prepared synthetic fixtures under build/redesign/synthetic. Automatic updates disabled.')
