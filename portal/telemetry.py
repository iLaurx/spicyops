"""Normalización de lecturas. Sin ORM ni escrituras de RouterOS."""
import ipaddress
import math
import re
import time

from .router_contract import RESERVED, restriction_state, individual_target, queue_safety, number, speed, pair

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

def boolean(value): return value in (True, 'true', 'yes', '1')

def normalize(raw, timestamp, *, deadline=None, inclusions=()):
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
    inventory, excluded_queues = [], []
    ip_counts, id_counts = queue_safety(queues)
    clients = []
    ids = set()
    targets = {}
    for queue in queues:
        check_time()
        try:
            ip = individual_target(queue)
        except ValueError:
            excluded += 1
            excluded_queues.append(dict(id=str(queue.get('.id', '')), name=str(queue.get('name', ''))[:180],
                ip=str(queue.get('target', ''))[:250], reason='Destino compartido, múltiple o no IPv4 individual', eligible=False))
            continue
        identifier = str(queue['.id'])
        if identifier in ids: raise ValueError('El router devolvió colas con identidad duplicada.')
        ids.add(identifier)
        upload, download = pair(queue['max-limit'], speed)
        byte_values = pair(queue['bytes'], number) if 'bytes' in queue else None
        rate_values = pair(queue.get('rate', '0/0'), speed)
        restriction = restriction_state(restrictions, ip)
        matching = restriction['active']
        name = str(queue.get('name', ip))[:180]
        client = {'id': identifier, 'name': name, 'ip': ip,
            'plan_up_mbps': upload/1e6, 'plan_down_mbps': download/1e6,
            'rate_up_mbps': rate_values[0]/1e6, 'rate_down_mbps': rate_values[1]/1e6,
            'upload_bytes': byte_values[0] if byte_values else None,
            'download_bytes': byte_values[1] if byte_values else None,
            'bytes': sum(byte_values) if byte_values else None,
            'status': 'Cola deshabilitada' if boolean(queue.get('disabled')) else 'Restricción activa' if matching else 'Cola habilitada',
            'restricted': bool(matching), 'restriction_unsafe': restriction['unsafe'], 'restriction_unknown': restriction['unknown'],
            'disabled': boolean(queue.get('disabled')) or boolean(queue.get('invalid')),
            'fingerprint': identifier+'|'+ip+'|'+name}
        client['ambiguous'] = ip_counts[ip] > 1 or id_counts[identifier] > 1
        if restriction['unknown']: client['status'] = 'Morosos sin interpretar; sincroniza y revisa'
        heuristic = int(ip.split('.')[-1]) in RESERVED
        client['infrastructure'] = heuristic
        client['inclusion_eligible'] = heuristic and not client['ambiguous'] and not client['disabled'] and byte_values is not None
        if heuristic: inventory.append(client)
        if heuristic and (client['fingerprint'] not in inclusions or not client['inclusion_eligible']):
            excluded += 1
            excluded_queues.append(dict(client, reason='Filtro de infraestructura por terminación IPv4', eligible=client['inclusion_eligible']))
        else:
            clients.append(client)
        targets[ip] = ip_counts[ip]
    for client in clients:
        client['ambiguous'] = targets[client['ip']] > 1
        if client['ambiguous']: client['status'] = 'IP con varias colas'
    counted = [c['bytes'] for c in clients if c['bytes'] is not None and not c['ambiguous']]
    return {'timestamp': float(timestamp), 'uptime': uptime, 'identity': str(resource.get('identity', 'MikroTik'))[:180],
        'version': str(resource['version'])[:60], 'board': str(resource.get('board', ''))[:100],
        'raspberry': raw.get('raspberry', {}), 'clients': clients, 'excluded': excluded,
        'inventory': inventory, 'excluded_queues': excluded_queues,
        'total_bytes': sum(counted) if counted or not clients else None, 'unknown_counters': len(clients)-len(counted)}

def same_boot(first, last):
    elapsed = last['timestamp'] - first['timestamp']
    uptime_delta = last['uptime'] - first['uptime']
    return elapsed > 0 and uptime_delta > 0 and abs(elapsed-uptime_delta) < max(8, elapsed*.03) and first['identity'] == last['identity']


def apply_inclusions(sample, inclusions):
    """Proyección local de la última lectura, sin fabricar mediciones."""
    if 'inventory' not in sample:
        return
    clients = [dict(c) for c in sample['clients'] if not c.get('infrastructure')]
    clients += [dict(c) for c in sample['inventory']
                if c['inclusion_eligible'] and c['fingerprint'] in inclusions]
    other = [c for c in sample.get('excluded_queues', []) if not c.get('infrastructure')]
    sample['excluded_queues'] = other + [dict(c, reason='Filtro de infraestructura por terminación IPv4',
        eligible=c['inclusion_eligible']) for c in sample['inventory']
        if c['infrastructure'] and not (c['inclusion_eligible'] and c['fingerprint'] in inclusions)]
    sample['clients'] = clients
    sample['excluded'] = len(sample['excluded_queues'])
    counted = [c['bytes'] for c in clients if c['bytes'] is not None and not c['ambiguous']]
    sample['total_bytes'] = sum(counted) if counted or not clients else None
    sample['unknown_counters'] = len(clients)-len(counted)


def estimate_uptime(history):
    """Aproximación con uptime; nunca proyecta deltas entre lecturas."""
    latest = history[-1] if history else None
    rows = []
    for client in latest['clients'] if latest else []:
        row = dict(client, daily_bytes=None, monthly_bytes=None,
                   estimate_note=client.get('counter_note') or 'Desde encendido · aprox.')
        if client['ambiguous'] or client['bytes'] is None:
            row['estimate_note'] = 'Cola ambigua' if client['ambiguous'] else 'Contador no disponible'
        elif latest['uptime'] < 60:
            row['estimate_note'] = 'Espera al menos un minuto desde el encendido'
        rows.append(row)
    # Un índice por lectura, descartado al avanzar: O(historial * clientes),
    # sin conservar índices de todo el historial ni modificar las lecturas.
    pending = [row for row in rows if row['estimate_note'] == 'Desde encendido · aprox.']
    newer = {row['fingerprint']: row for row in pending}
    adjacent = latest
    for previous in reversed(history[:-1]):
        if not pending or not same_boot(previous, adjacent) or not same_boot(previous, latest):
            break
        previous_clients = {}
        for client in previous['clients']:
            previous_clients.setdefault(client['fingerprint'], client)
        remaining = []
        for row in pending:
            old = previous_clients.get(row['fingerprint'])
            new = newer[row['fingerprint']]
            if old is None:
                row['estimate_note'] = 'Cola nueva o modificada; edad del contador desconocida'
            elif old.get('counter_note'):
                row['estimate_note'] = old['counter_note']
            elif old['ambiguous']:
                row['estimate_note'] = 'Cola ambigua; edad del contador desconocida'
            elif ((old['upload_bytes'] is not None and new['upload_bytes'] is not None and
                   old['upload_bytes'] > new['upload_bytes']) or
                  (old['download_bytes'] is not None and new['download_bytes'] is not None and
                   old['download_bytes'] > new['download_bytes'])):
                row['estimate_note'] = 'Contador reiniciado; edad desconocida'
            else:
                remaining.append(row)
        pending = remaining
        newer = previous_clients
        adjacent = previous
    # El historial solo descarta resets/cambios; el promedio sigue usando uptime.
    for row in pending:
        row['daily_bytes'] = row['bytes'] / latest['uptime'] * 86400
        row['monthly_bytes'] = row['daily_bytes'] * 30
    ready = [row for row in rows if row['daily_bytes'] is not None]
    return rows, {'ready': bool(ready), 'estimated_count': len(ready),
        'daily_bytes': sum(row['daily_bytes'] for row in ready) if ready else None,
        'monthly_bytes': sum(row['monthly_bytes'] for row in ready) if ready else None}


def carry_counter_validity(history, sample):
    """Retiene resets conocidos aunque roten las 1440 lecturas del historial.

    Al actualizar una instalación antigua se recorre su historial una vez.
    Después basta el índice de la lectura inmediatamente anterior: O(clientes).
    Los marcadores se descartan al cambiar de router/época de arranque.
    """
    previous = history[-1] if history else None
    if previous and same_boot(previous, sample):
        if not previous.get('counter_validity_recorded'):
            rows, _ = estimate_uptime(history+[sample])
            invalid = {r['fingerprint']: r['estimate_note'] for r in rows
                       if r['estimate_note'].startswith(('Contador reiniciado', 'Cola nueva', 'Cola ambigua;'))}
        else:
            old = {c['fingerprint']: c for c in previous['clients']}
            invalid = {}
            for row in sample['clients']:
                prior = old.get(row['fingerprint'])
                if prior is None:
                    note = 'Cola nueva o modificada; edad del contador desconocida'
                elif prior.get('counter_note'):
                    note = prior['counter_note']
                elif prior['ambiguous']:
                    note = 'Cola ambigua; edad del contador desconocida'
                elif any(prior[k] is not None and row[k] is not None and prior[k] > row[k]
                         for k in ('upload_bytes', 'download_bytes')):
                    note = 'Contador reiniciado; edad desconocida'
                else:
                    continue
                invalid[row['fingerprint']] = note
        for row in sample['clients']:
            if row['fingerprint'] in invalid:
                row['counter_note'] = invalid[row['fingerprint']]
        # La proyección de una excepción no debe perder el marcador ya observado.
        for row in sample.get('inventory', []):
            if row['fingerprint'] in invalid:
                row['counter_note'] = invalid[row['fingerprint']]
    sample['counter_validity_recorded'] = True
