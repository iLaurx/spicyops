"""Router simulado persistente. Nunca abre sockets ni importa librouteros."""
import json
import sqlite3
from contextlib import contextmanager
from .contract import ACTIONS, validate_state

class Simulator:
    def __init__(self, path, inventory):
        self.path, self.inventory = path, inventory
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS routers (id TEXT PRIMARY KEY, config TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS outbox (attempt TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            for router in inventory:
                initial = {'policy': 'Morosos-v1', 'queues': [
                    {'name': 'Descanso_Madrugada', 'shared': True}, {'name': 'Default Queue', 'shared': True}],
                    'morosos': {}, 'schedulers': ['Apagar_Red', 'Encender_Red']}
                db.execute('INSERT OR IGNORE INTO routers VALUES (?,?)', (router, json.dumps(initial)))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def config(self, router):
        with self.connect() as db:
            row = db.execute('SELECT config FROM routers WHERE id=?', (str(router),)).fetchone()
        if not row: raise ValueError('Router fuera del inventario.')
        return json.loads(row[0])

    def read(self, router, desired):
        config = self.config(router)
        matches = [q for q in config['queues'] if q.get('ip') == desired['ip']]
        if not matches: return None
        if len(matches) != 1 or matches[0].get('service') != desired['service']:
            raise ValueError('Cola duplicada o no administrada.')
        queue = matches[0]
        restriction = config['morosos'].get(desired['ip'])
        if not restriction or restriction['service'] != desired['service']:
            raise ValueError('Restricción ambigua.')
        return {'service': queue['service'], 'ip': queue['ip'], 'revision': queue['revision'],
                'enabled': not restriction['active'], 'up_kbps': queue['up_kbps'], 'down_kbps': queue['down_kbps']}

    def apply(self, router, action, desired, fault=None):
        router = str(router)
        if action not in ACTIONS:
            raise ValueError('Acción fuera de contrato.')
        validate_state(desired, self.inventory[router]['allowed_ips'])
        if fault == 'before_write': raise RuntimeError('Fallo simulado antes de escribir.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            config = json.loads(db.execute('SELECT config FROM routers WHERE id=?', (router,)).fetchone()[0])
            if config['policy'] != 'Morosos-v1' or [q.get('name') for q in config['queues'] if q.get('shared')] != ['Descanso_Madrugada', 'Default Queue']:
                raise ValueError('Política compartida inesperada; no escribir.')
            matches = [q for q in config['queues'] if q.get('ip') == desired['ip']]
            if len(matches) > 1 or (matches and matches[0].get('service') != desired['service']):
                raise ValueError('Cola duplicada o ajena; no adoptar automáticamente.')
            old = matches[0] if matches else None
            if old and old['revision'] > desired['revision']:
                raise ValueError('Revisión obsoleta en el router simulado.')
            if old and old['revision'] == desired['revision']:
                # Una misma revisión solo puede representar una intención.
                restriction = config['morosos'].get(desired['ip'], {})
                if any(old[k] != desired[k] for k in ('up_kbps', 'down_kbps')) or restriction.get('active') != (not desired['enabled']):
                    raise ValueError('Revisión reutilizada con parámetros distintos.')
            if old is None:
                if action != 'provision': raise ValueError('Falta alta técnica.')
                if desired['ip'] in config['morosos']:
                    raise ValueError('Restricción preexistente sin cola adoptada; no apropiarse de ella.')
                # Crear restringido, insertar después de la política nocturna y antes de Default.
                config['morosos'][desired['ip']] = {'service': desired['service'], 'active': True}
                old = {'name': f'spicyops:{desired["service"]}', 'service': desired['service'], 'ip': desired['ip'],
                       'burst': {'limit': '0/0', 'threshold': '0/0', 'time': '0s/0s'}, 'parent': 'none'}
                config['queues'].insert(len(config['queues']) - 1, old)
            restriction = config['morosos'].get(desired['ip'])
            if restriction is None or restriction['service'] != desired['service']:
                raise ValueError('Restricción ajena o ausente; requiere revisión.')
            old.update({k: desired[k] for k in ('revision', 'up_kbps', 'down_kbps')})
            restriction['active'] = not desired['enabled']
            db.execute('UPDATE routers SET config=? WHERE id=?', (json.dumps(config), router))
        if fault == 'after_write': raise RuntimeError('Fallo simulado después de escribir.')
        observed = self.read(router, desired)
        if observed != desired: raise ValueError('Lectura posterior distinta.')
        return observed

    def save_report(self, envelope, report):
        item = {'envelope': envelope, 'report': report}
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO outbox VALUES (?,?)', (envelope['attempt'], json.dumps(item)))

    def pending_reports(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM outbox ORDER BY rowid')]

    def acknowledge(self, attempt):
        with self.connect() as db:
            db.execute('DELETE FROM outbox WHERE attempt=?', (attempt,))
