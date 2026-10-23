"""Comparación de auditoría con el mismo estado sintético; nunca usa accesos reales."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.benchmark_portal_reads import history, timed, visits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', default='3aba44f62b7a1f91d80dd696765c3c7c9356feb3')
    args = parser.parse_args()
    root = ROOT/'build'/'audit-tests'
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        os.environ['SPICYOPS_STATE_DIR'] = folder
        os.environ['DJANGO_SECRET_KEY'] = 'benchmark-audit-synthetic-key'
        os.environ['DJANGO_SETTINGS_MODULE'] = 'spicyops.portal_settings'
        import django
        django.setup()
        from portal.store import Store
        from portal.scheduling import Coordinator
        from portal.telemetry import estimate_uptime, carry_counter_validity
        from django.test import override_settings
        old_source = subprocess.run(['git', 'show', args.baseline_ref+':portal/telemetry.py'], cwd=ROOT,
            capture_output=True, encoding='utf-8', check=True).stdout
        old = {}; exec(compile(old_source, '<audit baseline HEAD>', 'exec'), old)
        report = dict(python=sys.version.split()[0], repeats=5, synthetic=True, real_network=False,
                      baseline=args.baseline_ref, calculations=[])
        for clients, samples in ((20, 120), (100, 240), (300, 240), (100, 1440)):
            data = history(clients, samples)
            assert old['estimate_uptime'](data) == estimate_uptime(data)
            report['calculations'].append(dict(clients=clients, samples=samples,
                before_ms=timed(lambda: old['estimate_uptime'](data), 5),
                after_ms=timed(lambda: estimate_uptime(data), 5),
                before_visits=visits(old['estimate_uptime'], data), after_visits=visits(estimate_uptime, data)))
        profiles = {str(i): dict(id=str(i), connected=True, history=history(100, 240), metadata={},
                    automatic=dict(enabled=True, interval=5, next_at=2e10)) for i in range(2)}
        with override_settings(STATE_DIR=folder):
            store = Store(); store.update(lambda d: d.update(profiles=profiles))
            coordinator = Coordinator(lambda key: None, store=store)
            try:
                # Antes: tick leía y descifraba el archivo entero sin trabajo.
                before_ms = timed(store.read, 5)
                with patch.object(Store, '_read', autospec=True, side_effect=Store._read) as reads:
                    coordinator.tick()
                    cold_reads = reads.call_count
                    after_ms = timed(coordinator.tick, 5)
                    idle_reads = reads.call_count-cold_reads
                report['state'] = dict(localities=2, clients_per_locality=100, samples_per_locality=240,
                    encrypted_bytes=store.path.stat().st_size, before_idle_tick_ms=before_ms,
                    after_idle_tick_ms=after_ms, before_reads_per_tick=1, after_warm_reads=idle_reads,
                    cold_reads=cold_reads, update_ms=timed(lambda: store.update(lambda d: None), 5))
                with patch.object(Store, '_read', autospec=True, side_effect=Store._read) as reads:
                    coordinator.tick()
                assert reads.call_count == 1
                report['state']['reloads_after_file_change'] = reads.call_count
            finally:
                coordinator.stop()
        output = ROOT/'docs'/'auditoria-mediciones.json'
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
