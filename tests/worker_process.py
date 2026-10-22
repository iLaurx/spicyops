"""Proceso de prueba: fallos deliberados; no se distribuye como agente de producción."""
import json
import os
from pathlib import Path
import sys
from agent.client import CentralClient
from agent.simulator import Simulator
from agent.worker import Worker

config = json.loads(Path(sys.argv[1]).read_text())
fault = sys.argv[2] if len(sys.argv) > 2 else None
sim = Simulator(config['state_file'], config['routers'])
if fault == 'crash_after_write':
    original = sim.apply
    def crash(*args, **kwargs):
        original(*args, **kwargs)
        os._exit(23)
    sim.apply = crash
worker = Worker(CentralClient(config['url'], config['agent'], config['token'], True), sim, config['site'])
try:
    worker.once(fault=fault)
except RuntimeError:
    sys.exit(24)
