import argparse
import json
import logging
import os
from pathlib import Path
import time
from .client import CentralClient
from .simulator import Simulator
from .worker import Worker

class InstanceLock:
    def __init__(self, path): self.path = path
    def __enter__(self):
        self.file = open(self.path, 'a+b')
        self.file.seek(0)
        self.file.write(b'1')
        self.file.flush()
        self.file.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return self
    def __exit__(self, *args): self.file.close()

def main():
    parser = argparse.ArgumentParser(description='Agente local SpicyOps, exclusivamente simulación.')
    parser.add_argument('--config', default='.local/agent.json')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    path = Path(args.config).resolve()
    config = json.loads(path.read_text())
    if config.get('mode') != 'simulator':
        raise ValueError('Ejecución real deshabilitada en este MVP.')
    state = path.parent / config.get('state_file', 'simulator.sqlite3')
    client = CentralClient(config['url'], config['agent'], config['token'], config.get('allow_loopback_http', False))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    with InstanceLock(str(state) + '.lock'):
        worker = Worker(client, Simulator(state, config['routers']), config['site'])
        while True:
            try:
                active = worker.once()
                if active: logging.info('Ciclo simulado procesado; consultar resultado en el panel.')
            except Exception:
                # Nunca imprimir cuerpos HTTP, cabeceras, tokens ni excepciones con URL.
                logging.error('Ciclo incompleto; se conservará la tarea y se reintentará.')
                if args.once: raise SystemExit(1) from None
            if args.once: break
            time.sleep(2)

if __name__ == '__main__': main()
