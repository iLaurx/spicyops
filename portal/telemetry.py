"""Normalización de lecturas. Sin ORM ni escrituras de RouterOS."""
import ipaddress
import math
import re
import time

RESERVED = {0, 1, 2, 3, 4, 5, 6, 50, 90, 255}

def number(value):
    if isinstance(value, bool): raise ValueError('Número inválido.')
    result = int(value)
    if result < 0 or result > 2**64: raise ValueError('Contador inválido.')
    return result

def duration(value):
    if isinstance(value, (int, float)):
        if not math.isfinite(value) or value < 0: raise ValueError('Uptime inválido.')
        return float(value)
    text = str(value).strip()
    if re.fullmatch(r'\d+(?:\.\d+)?', text): return float(text)
    days = re.match(r'^(?:(\d+)w)?(?:(\d+)d)?(.*)$', text)
    total = int(days[1] or 0)*604800 + int(days[2] or 0)*86400
    rest = days[3]
    if ':' in rest:
        parts = rest.split(':')
        if len(parts) != 3: raise ValueError('Uptime inválido.')
        return total + int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
    tokens = re.findall(r'(\d+(?:\.\d+)?)(ms|h|m|s)', rest)
    if ''.join(a+b for a,b in tokens) != rest or (not tokens and not total):
        raise ValueError('Uptime inválido.')
    return total + sum(float(a)*{'h':3600, 'm':60, 's':1, 'ms':.001}[b] for a,b in tokens)

def speed(value):
    text = str(value).strip()
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([kKmMgG]?)', text)
    if not match: raise ValueError('Velocidad inválida.')
    return float(match[1])*{'':1,'k':1000,'m':1000000,'g':1000000000}[match[2].lower()]

def pair(value, parser):
    if isinstance(value, (tuple, list)) and len(value) == 2: return [parser(x) for x in value]
    parts = str(value).split('/')
    if len(parts) != 2: raise ValueError('Par de valores inválido.')
    return [parser(x) for x in parts]

def boolean(value): return value in (True, 'true', 'yes', '1')

def normalize(raw, timestamp, *, deadline=None):
    def check_time():
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('Se agotó el tiempo para validar el inventario.')
    check_time()
    if not isinstance(raw, dict) or raw.get('schema') != 1:
        raise ValueError('El lector de Raspberry devolvió un contrato desconocido.')
    resource = raw['router']
    uptime = duration(resource['uptime'])
    if uptime < duration(resource.get('uptime_start', resource['uptime'])):
        raise ValueError('El MikroTik reinició durante la lectura; vuelve a sincronizar.')
    if not str(resource['version']).startswith(('6.', '7.')):
        raise ValueError('Versión RouterOS fuera del contrato 6/7.')
    queues, restrictions = raw['queues'], raw.get('restrictions', [])
    if not isinstance(queues, list) or len(queues) > 5000: raise ValueError('Inventario demasiado grande.')
    excluded = 0
    clients = []
    ids = set()
    targets = {}
    for queue in queues:
        check_time()
        try:
            target = str(queue.get('target', '')).strip()
            if ',' in target: raise ValueError()
            net = ipaddress.ip_network(target if '/' in target else target+'/32', strict=True)
            if net.version != 4 or net.prefixlen != 32 or int(str(net.network_address).split('.')[-1]) in RESERVED:
                raise ValueError()
            ip = str(net.network_address)
        except ValueError:
            excluded += 1
            continue
        identifier = str(queue['.id'])
        if identifier in ids: raise ValueError('El router devolvió colas con identidad duplicada.')
        ids.add(identifier)
        upload, download = pair(queue['max-limit'], speed)
        byte_values = pair(queue['bytes'], number) if 'bytes' in queue else None
        rate_values = pair(queue.get('rate', '0/0'), speed)
        matching = []
        for entry in restrictions:
            check_time()
            if entry.get('list') != 'Morosos' or boolean(entry.get('disabled', False)): continue
            try:
                if net.network_address in ipaddress.ip_network(entry['address'], strict=False): matching.append(entry)
            except (ValueError, KeyError): continue
        name = str(queue.get('name', ip))[:180]
        clients.append({'id': identifier, 'name': name, 'ip': ip,
            'plan_up_mbps': upload/1e6, 'plan_down_mbps': download/1e6,
            'rate_up_mbps': rate_values[0]/1e6, 'rate_down_mbps': rate_values[1]/1e6,
            'upload_bytes': byte_values[0] if byte_values else None,
            'download_bytes': byte_values[1] if byte_values else None,
            'bytes': sum(byte_values) if byte_values else None,
            'status': 'Cola deshabilitada' if boolean(queue.get('disabled')) else 'Restricción activa' if matching else 'Cola habilitada',
            'restricted': bool(matching), 'disabled': boolean(queue.get('disabled')),
            'fingerprint': identifier+'|'+ip+'|'+name})
        targets[ip] = targets.get(ip, 0) + 1
    for client in clients:
        client['ambiguous'] = targets[client['ip']] > 1
        if client['ambiguous']: client['status'] = 'IP con varias colas'
    counted = [c['bytes'] for c in clients if c['bytes'] is not None and not c['ambiguous']]
    return {'timestamp': float(timestamp), 'uptime': uptime, 'identity': str(resource.get('identity', 'MikroTik'))[:180],
        'version': str(resource['version'])[:60], 'board': str(resource.get('board', ''))[:100],
        'raspberry': raw.get('raspberry', {}), 'clients': clients, 'excluded': excluded,
        'total_bytes': sum(counted) if counted or not clients else None, 'unknown_counters': len(clients)-len(counted)}

def same_boot(first, last):
    elapsed = last['timestamp'] - first['timestamp']
    uptime_delta = last['uptime'] - first['uptime']
    return elapsed > 0 and uptime_delta > 0 and abs(elapsed-uptime_delta) < max(8, elapsed*.03) and first['identity'] == last['identity']


def estimate_uptime(history):
    """Aproximación con uptime; nunca proyecta deltas entre lecturas."""
    latest = history[-1] if history else None
    rows = []
    for client in latest['clients'] if latest else []:
        row = dict(client, daily_bytes=None, monthly_bytes=None, estimate_note='Desde encendido · aprox.')
        if client['ambiguous'] or client['bytes'] is None:
            row['estimate_note'] = 'Cola ambigua' if client['ambiguous'] else 'Contador no disponible'
        elif latest['uptime'] < 60:
            row['estimate_note'] = 'Espera al menos un minuto desde el encendido'
        rows.append(row)
    # Un índice por lectura, descartado al avanzar: O(historial * clientes),
    # sin conservar índices de todo el historial ni modificar las lecturas.
    pending = [row for row in rows if row['estimate_note'] == 'Desde encendido · aprox.']
    for previous in reversed(history[:-1]):
        if not pending or not same_boot(previous, latest):
            break
        previous_clients = {}
        for client in previous['clients']:
            previous_clients.setdefault(client['fingerprint'], client)
        remaining = []
        for row in pending:
            old = previous_clients.get(row['fingerprint'])
            if old is None:
                row['estimate_note'] = 'Cola nueva o modificada; edad del contador desconocida'
            elif any(old[k] is not None and old[k] > row[k] for k in ('upload_bytes','download_bytes')):
                row['estimate_note'] = 'Contador reiniciado; edad desconocida'
            else:
                remaining.append(row)
        pending = remaining
    # El historial solo descarta resets/cambios; el promedio sigue usando uptime.
    for row in pending:
        row['daily_bytes'] = row['bytes'] / latest['uptime'] * 86400
        row['monthly_bytes'] = row['daily_bytes'] * 30
    ready = [row for row in rows if row['daily_bytes'] is not None]
    return rows, {'ready': bool(ready), 'estimated_count': len(ready),
        'daily_bytes': sum(row['daily_bytes'] for row in ready) if ready else None,
        'monthly_bytes': sum(row['monthly_bytes'] for row in ready) if ready else None}
