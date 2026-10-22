"""Transporte preparado para API tradicional 6/7. No participa en el MVP local.

El adaptador permanece cerrado a escrituras hasta adoptar inventario y validar
la política física de cada router en una fase autorizada independiente.
"""
from functools import partial
import ssl
from .contract import validate_state

class RouterOSTransport:
    READ_PATHS = {('system', 'resource'), ('queue', 'simple'), ('ip', 'firewall', 'address-list'),
                  ('ip', 'firewall', 'filter'), ('system', 'scheduler')}

    def __init__(self, *, host, username, password, ca_file, enabled=False):
        self.host, self.username, self.password = host, username, password
        self.ca_file, self.enabled = ca_file, enabled
        self.api = None

    def open(self):
        if not self.enabled:
            raise RuntimeError('Transporte real deshabilitado explícitamente.')
        from librouteros import connect
        context = ssl.create_default_context(cafile=self.ca_file)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.api = connect(host=self.host, port=8729, username=self.username, password=self.password,
            ssl_wrapper=partial(context.wrap_socket, server_hostname=self.host), timeout=10)
        version = str(self.read(('system', 'resource'))[0]['version'])
        if not version.startswith(('6.', '7.')):
            self.close()
            raise ValueError('Versión fuera del contrato RouterOS 6/7.')
        return version

    def read(self, path):
        if path not in self.READ_PATHS or self.api is None:
            raise ValueError('Lectura fuera de contrato o transporte cerrado.')
        return list(self.api.path(*path))

    def close(self):
        if self.api: self.api.close()
        self.api = None

class RouterOSAdapter:
    def __init__(self, transport, allowed_ips):
        self.transport, self.allowed_ips = transport, allowed_ips

    def read(self, router, desired):
        validate_state(desired, self.allowed_ips)
        queues = [q for q in self.transport.read(('queue', 'simple')) if q.get('target') == desired['ip'] + '/32']
        restrictions = [r for r in self.transport.read(('ip', 'firewall', 'address-list'))
                        if r.get('list') == 'Morosos' and r.get('address') == desired['ip']]
        tag = 'spicyops:' + str(desired['service'])
        if len(queues) != 1 or len(restrictions) != 1 or any(x.get('comment') != tag for x in queues + restrictions):
            raise ValueError('Objetos ausentes, duplicados o sin adopción autorizada.')
        queue, restriction = queues[0], restrictions[0]
        if queue.get('disabled') not in (False, 'false', 'no'):
            raise ValueError('Cola deshabilitada; requiere revisión.')
        def rate(value):
            text = str(value)
            factor = 1000 if text.endswith('M') else 1 if text.endswith('k') else .001
            return int(float(text.rstrip('Mk')) * factor)
        up, down = map(rate, queue['max-limit'].split('/'))
        # RouterOS no acredita por sí solo la revisión central.
        return {'ip': desired['ip'], 'service': desired['service'], 'revision': None,
                'enabled': restriction.get('disabled') in (True, 'true', 'yes'), 'up_kbps': up, 'down_kbps': down}

    def apply(self, router, action, desired, fault=None):
        validate_state(desired, self.allowed_ips)
        raise RuntimeError('Escrituras físicas bloqueadas: pendiente adopción y pruebas de política, orden y burst.')
