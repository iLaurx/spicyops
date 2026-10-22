"""Comparación local reproducible; solo datos sintéticos y estado temporal propio.

El baseline se carga desde una revisión Git, nunca desde el estado del usuario.
No inicia el coordinador ni abre conexiones SSH/API.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def history(clients, samples):
    rows = [dict(id=str(i), name=f'Sintético {i}', ip=f'198.18.{i//240}.{i%240+10}',
                 fingerprint=f'{i}|synthetic', ambiguous=False, disabled=False, restricted=False,
                 status='Cola habilitada', plan_up_mbps=2, plan_down_mbps=4,
                 rate_up_mbps=0, rate_down_mbps=0) for i in range(clients)]
    return [dict(timestamp=1_800_000_000+j*60, uptime=3600+j*60, identity='Sintético',
                 version='6.49.23', board='test', excluded=0, unknown_counters=0,
                 total_bytes=clients*(j+1)*3000, raspberry={},
                 clients=[dict(row, upload_bytes=(j+1)*1000, download_bytes=(j+1)*2000,
                               bytes=(j+1)*3000) for row in rows]) for j in range(samples)]


def timed(fn, repeats):
    fn()  # calentamiento excluido
    values = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        values.append((time.perf_counter()-start)*1000)
    return round(statistics.median(values), 3)


class CountedClients(list):
    visits = 0

    def __iter__(self):
        for row in super().__iter__():
            type(self).visits += 1
            yield row


def visits(fn, source):
    counted = [dict(sample, clients=CountedClients(sample['clients'])) for sample in source]
    CountedClients.visits = 0
    fn(counted)
    return CountedClients.visits


def equivalence(before, after):
    # Orden, prioridad de avisos, reinicios, identidades, contadores por dirección,
    # clientes desaparecidos/modificados, ambiguos y ausencia de contadores.
    rng = random.Random(731)
    for case in range(160):
        source = history(12, 8)
        for sample in source:
            rng.shuffle(sample['clients'])
            if rng.random() < .2: sample['identity'] = 'Otra identidad'
            if rng.random() < .2: sample['uptime'] = rng.randrange(30, 5000)
            sample['clients'] = [row for row in sample['clients'] if rng.random() > .08]
            for row in sample['clients']:
                if rng.random() < .08: row['fingerprint'] += '|cambio'
                if rng.random() < .08: row['ambiguous'] = True
                if rng.random() < .08:
                    row.update(bytes=None, upload_bytes=None, download_bytes=None)
                elif rng.random() < .15:
                    row['upload_bytes'] = rng.randrange(0, 20000)
                    row['bytes'] = row['upload_bytes'] + row['download_bytes']
        saved = copy.deepcopy(source)
        assert before(source) == after(source), case
        assert source == saved, f'Mutación del historial: {case}'
    assert before([]) == after([])
    return 161


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', required=True)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--output', type=Path, help='Guardar el informe JSON sintético')
    args = parser.parse_args()
    if args.repeats < 1: parser.error('--repeats debe ser positivo')
    baseline = subprocess.run(['git', 'show', f'{args.baseline_ref}:portal/telemetry.py'],
                              cwd=ROOT, check=True, capture_output=True, encoding='utf-8').stdout
    namespace = {}
    exec(compile(baseline, '<baseline telemetry>', 'exec'), namespace)
    before = namespace['estimate_uptime']
    from portal.telemetry import estimate_uptime as after
    report = dict(baseline=args.baseline_ref, python=sys.version.split()[0], repeats=args.repeats,
                  equivalent_cases=equivalence(before, after), calculations=[])
    for clients, samples in [(20, 120), (100, 240), (300, 240), (100, 1440)]:
        source = history(clients, samples)
        assert before(source) == after(source)
        report['calculations'].append(dict(clients=clients, samples=samples,
            before_ms=timed(lambda: before(source), args.repeats),
            after_ms=timed(lambda: after(source), args.repeats),
            before_client_visits=visits(before, source), after_client_visits=visits(after, source)))
    root = ROOT/'.local'/'tmp'
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        # Configurar ANTES de cargar Django: nunca leer secret.key ni conexiones privadas.
        os.environ['SPICYOPS_STATE_DIR'] = folder
        os.environ['DJANGO_SECRET_KEY'] = 'benchmark-synthetic-key-not-for-production'
        os.environ['DJANGO_SETTINGS_MODULE'] = 'spicyops.portal_settings'
        import django
        django.setup()
        from django.test import Client
        from portal.auth import identity
        from portal.store import Store
        from portal.scheduling import Coordinator
        from portal.views import refresh_profile
        store = Store()
        source = history(100, 240)
        profiles = {str(i): dict(id=str(i), name=f'Localidad sintética {i}', connected=True,
                    last_error='', last_read=source[-1]['timestamp'], history=source, metadata={},
                    automatic=dict(enabled=False, interval=5)) for i in range(2)}
        store.update(lambda data: data.update(profiles=profiles))
        client = Client()
        session = client.session
        session['desktop'] = identity()
        session.save()
        client.cookies['spicyops_portal'] = session.session_key
        def reads_for(fn):
            with patch.object(Store, '_read', autospec=True, side_effect=Store._read) as reads:
                result = fn()
            return reads.call_count, result
        report['state'] = dict(localities=2, clients_per_locality=100, samples_per_locality=240,
            encrypted_bytes=store.path.stat().st_size, read_ms=timed(store.read, args.repeats),
            update_ms=timed(lambda: store.update(lambda data: None), args.repeats))
        report['pages'] = []
        with patch('portal.views.collect', side_effect=AssertionError('Red prohibida')) as network:
            for url in ['/?site=0', '/clientes/?site=all', '/conexiones/']:
                def get():
                    response = client.get(url, HTTP_X_SPICYOPS_LIVE='1')
                    assert response.status_code == 200
                    return response
                with patch('portal.views.estimate_uptime', before):
                    old_ms = timed(get, args.repeats)
                    old_page = get().content
                new_ms = timed(get, args.repeats)
                count, page = reads_for(get)
                # Django cambia la máscara CSRF en cada respuesta; todo lo demás
                # debe coincidir byte por byte, incluidas cifras, avisos y gráfica.
                def without_csrf(content):
                    return re.sub(rb'(name="csrfmiddlewaretoken" value=")[^"]+', rb'\1TOKEN', content)
                assert without_csrf(old_page) == without_csrf(page.content), url
                report['pages'].append(dict(url=url, before_ms=old_ms, after_ms=new_ms,
                                            state_reads=count, response_bytes=len(page.content)))
            network.assert_not_called()
        coordinator = Coordinator(lambda key: None, store=store)
        try:
            count, _ = reads_for(coordinator.tick)
            report['idle_tick'] = dict(state_reads=count, ms=timed(coordinator.tick, args.repeats))
        finally:
            coordinator.stop()
        with patch('portal.views.collect') as reader:
            # Contrato remoto sintético; probar el recorrido de persistencia manual.
            reader.return_value = {'schema': 1, 'router': dict(identity='Sintético', version='6.49.23', uptime='1h'),
                                  'queues': [], 'restrictions': [], 'raspberry': {}}
            count, error = reads_for(lambda: refresh_profile('0'))
            assert error == ''
            report['manual_refresh'] = dict(state_reads=count, connector_calls=reader.call_count)
            store.update(lambda data: data['profiles']['0'].update(
                automatic=dict(enabled=True, interval=5, next_at=1)))
            reader.reset_mock()
            coordinator = Coordinator(refresh_profile, store=store)
            try:
                count, _ = reads_for(lambda: coordinator.execute('0'))
                report['automatic_refresh'] = dict(state_reads=count, connector_calls=reader.call_count)
            finally:
                coordinator.stop()
        from portal.remote_reader import collect as remote_collect
        calls = []
        def api_read(path, **options):
            calls.append((path, options))
            return iter({'/system/resource/print': [dict(uptime='1h', version='6.49.23')],
                         '/system/identity/print': [dict(name='Sintético')],
                         '/queue/simple/print': [{'.id': '*1', 'name': 'Sintético',
                             'target': '198.51.100.20/32', 'max-limit': '2M/4M', 'bytes': '100/200', 'rate': '0/0'}],
                         '/ip/firewall/address-list/print': []}[path])
        api = MagicMock(side_effect=api_read)
        with patch('portal.remote_reader.ssl.create_default_context'):
            result = remote_collect(dict(router_host='198.51.100.1', router_user='synthetic',
                router_password='synthetic', ca_file='synthetic.crt'), connect=MagicMock(return_value=api))
        assert len(calls) == 6 and all(path.endswith('/print') for path, _ in calls)
        assert api.close.called
        report['controlled_remote_reader'] = dict(api_reads=len(calls), paths=[path for path, _ in calls],
            result_bytes=len(json.dumps(result).encode()), real_network=False)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output+'\n', encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
