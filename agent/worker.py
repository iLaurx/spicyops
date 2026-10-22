import time
from .contract import ACTIONS, validate_state

class Worker:
    def __init__(self, client, simulator, site):
        self.client, self.simulator, self.site = client, simulator, site

    def check(self, item):
        if (item.get('contract') != 1 or item.get('site') != self.site
                or item.get('action') not in ACTIONS or str(item.get('router')) not in self.simulator.inventory):
            raise ValueError('Tarea fuera del inventario o contrato.')
        validate_state(item['state'], self.simulator.inventory[str(item['router'])]['allowed_ips'])
        if min(item['lease_until'], item['expires_at']) <= time.time():
            raise ValueError('Concesión o solicitud vencida.')

    def flush(self):
        for pending in self.simulator.pending_reports():
            item, report = pending['envelope'], pending['report']
            if report['ok']:
                # Tras reinicio, un diario no sustituye a una lectura nueva.
                try:
                    state = self.simulator.read(item['router'], item['state'])
                    if state != report['state']:
                        report = {'ok': False, 'state': None, 'error': 'verification_failed'}
                except (ValueError, KeyError):
                    report = {'ok': False, 'state': None, 'error': 'verification_failed'}
            response = self.client.report(item, report)
            if response.get('status') in ('accepted', 'duplicate') or response.get('conflict'):
                self.simulator.acknowledge(item['attempt'])

    def once(self, fault=None):
        self.flush()
        item = self.client.claim()
        if item is None: return False
        self.check(item)
        confirmed = self.client.validate(item)
        if confirmed.get('conflict'): return True
        if confirmed.get('task') != item:
            raise ValueError('La intención cambió durante la validación.')
        self.check(item)
        try:
            state = self.simulator.apply(item['router'], item['action'], item['state'], fault=fault)
            report = {'ok': True, 'state': state, 'error': ''}
        except (ValueError, RuntimeError):
            report = {'ok': False, 'state': None, 'error': 'execution_failed'}
        if fault == 'before_report':
            self.simulator.save_report(item, report)
            raise RuntimeError('Interrupción simulada antes del reporte.')
        self.simulator.save_report(item, report)
        self.flush()
        return True
