"""Carga acotada: varias localidades, historias llenas, sin conexiones externas."""
import os
import sys
from pathlib import Path
import tempfile
import copy
import time
import json
import statistics
import argparse
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spicyops.portal_settings')
os.environ.setdefault('SPICYOPS_STATE_DIR', str(ROOT/'build'/'release-tests'/'soak-bootstrap'))
os.environ.setdefault('DJANGO_SECRET_KEY', 'synthetic-soak-key')
import django
django.setup()
from django.test import override_settings
from portal.store import Store
from portal.scheduling import Coordinator
from portal.telemetry import estimate_uptime
from scripts.benchmark_portal_reads import history

parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=int, default=300)
args = parser.parse_args()
assert 60 <= args.seconds <= 1800, 'Usar una duración acotada de 60 a 1800 segundos.'
with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
    with override_settings(STATE_DIR=Path(temp)):
        store = Store()
        initial = {'profiles': {str(i): {'id': str(i), 'name': f'Sintética {i}', 'connected': False,
            'automatic': {'enabled': True, 'interval': 5}, 'metadata': {}, 'history': history(10, 1440)} for i in range(3)}}
        store.update(lambda d: d.update(initial))
        expected = [estimate_uptime(p['history']) for p in initial['profiles'].values()]
        coordinator = Coordinator(lambda _: (_ for _ in ()).throw(AssertionError('Red no autorizada')))
        coordinator.prepare()
        start = time.monotonic()
        ticks = rounds = 0
        latencies = []
        while time.monotonic()-start < args.seconds:
            for _ in range(100): coordinator.tick(); ticks += 1
            before = time.monotonic()
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(lambda i: Store().update(lambda d: d['profiles'][str(i)]['metadata'].update({'soak': {'notes': f'{i}-{rounds}'}})), range(3)))
            state = store.read()
            latencies.append(time.monotonic()-before)
            for i, p in enumerate(state['profiles'].values()):
                assert len(p['history']) == 1440
                assert p['metadata']['soak']['notes'] == f'{i}-{rounds}'
                assert estimate_uptime(p['history']) == expected[i]
            rounds += 1
        coordinator.stop()
        result = {'duration_seconds': round(time.monotonic()-start, 2), 'localities': 3, 'clients_each': 10,
            'samples_each': 1440, 'rounds': rounds, 'idle_ticks': ticks, 'state_bytes': store.path.stat().st_size,
            'median_three_writes_and_read_seconds': round(statistics.median(latencies), 3), 'result': 'OK', 'network': 'none'}
        (ROOT/'docs'/'release-soak.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
