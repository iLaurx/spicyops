"""Contrato puro compartido con el lector efímero (solo biblioteca estándar)."""
import ipaddress
import re

RESERVED = {0, 1, 2, 3, 4, 5, 6, 50, 90, 255}


def enabled(value):
    return value in (True, 'true', 'yes', '1')


def number(value):
    if isinstance(value, bool): raise ValueError('Número inválido.')
    result = int(value)
    if result < 0 or result > 2**64: raise ValueError('Contador inválido.')
    return result


def speed(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([kKmMgG]?)', str(value).strip())
    if not match: raise ValueError('Velocidad inválida.')
    return float(match[1])*{'':1,'k':1000,'m':1000000,'g':1000000000}[match[2].lower()]


def pair(value, parser):
    if isinstance(value, (tuple, list)) and len(value) == 2: return [parser(x) for x in value]
    parts = str(value).split('/')
    if len(parts) != 2: raise ValueError('Par de valores inválido.')
    return [parser(x) for x in parts]


def inclusion_values_valid(queue):
    try:
        pair(queue['max-limit'], speed)
        pair(queue['bytes'], number)
        pair(queue.get('rate', '0/0'), speed)
        return True
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def address_bounds(value):
    """Extremos inclusivos y clase; un rango nunca es una entrada individual."""
    text = str(value).strip()
    if '-' in text:
        first, last = text.split('-')
        low, high = int(ipaddress.IPv4Address(first.strip())), int(ipaddress.IPv4Address(last.strip()))
        if low > high:
            raise ValueError('Rango invertido')
        return low, high, False
    net = ipaddress.ip_network(text, strict=False)
    if net.version != 4:
        raise ValueError('Restricción no IPv4')
    return int(net.network_address), int(net.broadcast_address), net.prefixlen == 32


def restriction_state(restrictions, ip):
    """Falla cerrada ante entradas activas desconocidas, incluso nombres DNS."""
    address = int(ipaddress.IPv4Address(ip))
    individuals, shared, unknown = [], False, False
    for entry in restrictions:
        if entry.get('list') != 'Morosos':
            continue
        active = not enabled(entry.get('disabled'))
        try:
            low, high, individual = address_bounds(entry['address'])
        except (KeyError, ValueError, TypeError):
            unknown |= active
            continue
        if low <= address <= high:
            if not individual or enabled(entry.get('dynamic')):
                shared |= active
            else:
                individuals.append(entry)
    return dict(entries=individuals, active=shared or any(not enabled(e.get('disabled')) for e in individuals),
                unsafe=shared or unknown or len(individuals) > 1, unknown=unknown)


def queue_identity(queue, ip):
    return str(queue['.id'])+'|'+ip+'|'+str(queue.get('name', ip))[:180]


def individual_target(queue):
    target = ipaddress.ip_network(str(queue.get('target', '')).strip(), strict=True)
    if target.version != 4 or target.prefixlen != 32:
        raise ValueError('Destino no individual IPv4')
    return str(target.network_address)


def queue_safety(queues):
    """Cuenta también colas inválidas/excluidas para no eludir duplicados."""
    ips, ids = {}, {}
    for q in queues:
        key = str(q.get('.id', ''))
        ids[key] = ids.get(key, 0)+1
        # Múltiples destinos que repiten una IP también hacen insegura la excepción.
        for target in str(q.get('target', '')).split(','):
            try:
                net = ipaddress.ip_network(target.strip(), strict=True)
                if net.version == 4 and net.prefixlen == 32:
                    ip = str(net.network_address)
                    ips[ip] = ips.get(ip, 0)+1
            except ValueError:
                pass
    return ips, ids
