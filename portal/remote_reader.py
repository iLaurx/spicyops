"""Lector efímero y acción cerrada de Morosos; no instala archivos remotos."""
import sys
sys.dont_write_bytecode = True
import json
import os
from pathlib import Path
import ssl
import ipaddress
import socket
from functools import partial


class OperationRejected(Exception):
    pass


def enabled(value):
    return value in (True, 'true', 'yes', '1')


def change_morosity(api, queues, restrictions, identity, operation):
    """Solo una IPv4 individual ya inventariada; nunca cambia colas ni firewall."""
    if (operation.get('action') not in ('suspend', 'restore') or
            operation.get('identity') != identity):
        raise OperationRejected('client_changed')
    try:
        address = ipaddress.IPv4Address(operation['ip'])
    except (KeyError, ValueError):
        raise OperationRejected('client_changed') from None
    if int(str(address).split('.')[-1]) in {0, 1, 2, 3, 4, 5, 6, 50, 90, 255}:
        raise OperationRejected('client_changed')
    matching = []
    for queue in queues:
        try:
            target = ipaddress.ip_network(queue.get('target', ''), strict=True)
        except ValueError:
            continue
        if address in target:
            matching.append((queue, target))
    individual = [(q, n) for q, n in matching if n.prefixlen == 32]
    if len(individual) != 1:
        raise OperationRejected('client_changed')
    queue, _ = individual[0]
    if (queue.get('.id') != operation.get('id') or queue.get('name', '') != operation.get('name') or
            enabled(queue.get('disabled')) or enabled(queue.get('invalid'))):
        raise OperationRejected('client_changed')
    entries = []
    for entry in restrictions:
        if entry.get('list') != 'Morosos':
            continue
        try:
            network = ipaddress.ip_network(entry['address'], strict=False)
        except (ValueError, KeyError):
            continue
        if address in network:
            # No tocar subredes, rangos ni entradas dinámicas que afectan a otros.
            if network.prefixlen != 32 or enabled(entry.get('dynamic')):
                if not enabled(entry.get('disabled')):
                    raise OperationRejected('restriction_ambiguous')
                continue
            entries.append(entry)
    if len(entries) > 1:
        raise OperationRejected('restriction_ambiguous')
    desired = operation['action'] == 'suspend'
    current = bool(entries and not enabled(entries[0].get('disabled')))
    if current == desired:
        return  # Repetir la misma intención no crea duplicados.
    try:
        if entries:
            list(api('/ip/firewall/address-list/set', **{'.id': entries[0]['.id'], 'disabled': 'no' if desired else 'yes'}))
        elif desired:
            list(api('/ip/firewall/address-list/add', list='Morosos', address=str(address),
                     disabled='no', comment='SpicyOps: suspension por adeudo'))
    except Exception:
        raise OperationRejected('write_unconfirmed') from None

def collect(config, connect=None):
    if connect is None:
        from librouteros import connect
    diagnostic = config.get('diagnostic') is True
    if diagnostic and 'morosity' in config:
        raise OperationRejected('read_only')
    def event(name):
        if diagnostic: print(json.dumps({'event': name}), flush=True)
    event('reader')
    host = config.get('router_host', '').strip()
    if not host:
        # La ruta por defecto es una propuesta automática; no se explora la subred.
        import socket
        import struct
        for line in Path('/proc/net/route').read_text().splitlines()[1:]:
            fields = line.split()
            if fields[1] == '00000000' and int(fields[3], 16) & 2:
                host = socket.inet_ntoa(struct.pack('<L', int(fields[2], 16)))
                break
    if not host: raise ValueError('gateway_missing')
    ca = Path(config['ca_file']).expanduser()
    try:
        context = ssl.create_default_context(cafile=str(ca))
    except FileNotFoundError:
        raise OperationRejected('ca_missing') from None
    except ssl.SSLError:
        if diagnostic: raise OperationRejected('ca_invalid') from None
        raise
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    wrapper = partial(context.wrap_socket, server_hostname=host)
    options = {}
    if diagnostic:
        from librouteros import DEFAULTS
        from librouteros.exceptions import TrapError
        def login(api, username, password):
            try: DEFAULTS['login_method'](api, username, password)
            except TrapError: raise OperationRejected('api_auth') from None
        options['login_method'] = login
        def wrapper(sock):
            try: secured = context.wrap_socket(sock, server_hostname=host)
            except BaseException:
                sock.close()
                raise
            event('tls')
            return secured
    api = connect(host=host, port=8729, username=config['router_user'], password=config['router_password'],
        ssl_wrapper=wrapper, timeout=8, **options)
    def read(path, **kwargs):
        # No aceptar rutas/comandos del navegador. Solo cuatro lecturas cerradas.
        if path not in {'/system/resource/print', '/system/identity/print', '/queue/simple/print', '/ip/firewall/address-list/print'}:
            raise ValueError('read_not_allowed')
        result = []
        for row in api(path, **kwargs):
            result.append(row)
            if len(result) > 5000: raise ValueError('inventory_limit')
        return result
    try:
        resource = read('/system/resource/print', **{'.proplist': 'uptime,version,board-name'})[0]
        identity = read('/system/identity/print', **{'.proplist': 'name'})[0]
        columns = '.id,name,target,parent,disabled,invalid,max-limit,bytes,rate'
        queues = read('/queue/simple/print', **{'.proplist': columns})
        stats = read('/queue/simple/print', stats='', **{'.proplist': '.id,bytes,rate'})
        stats_by_id = {row['.id']: row for row in stats}
        for queue in queues:
            # Las estadísticas no sustituyen campos de configuración.
            queue.update({k: v for k, v in stats_by_id.get(queue['.id'], {}).items() if k in ('bytes', 'rate')})
        restriction_columns = '.id,list,address,disabled,dynamic'
        restrictions = read('/ip/firewall/address-list/print', **{'.proplist': restriction_columns})
        if 'morosity' in config:
            change_morosity(api, queues, restrictions, identity['name'], config['morosity'])
            restrictions = read('/ip/firewall/address-list/print', **{'.proplist': restriction_columns})
            address = ipaddress.IPv4Address(config['morosity']['ip'])
            active = False
            for entry in restrictions:
                if entry.get('list') != 'Morosos' or enabled(entry.get('disabled')):
                    continue
                try:
                    active = active or address in ipaddress.ip_network(entry['address'], strict=False)
                except (KeyError, ValueError):
                    continue
            if active != (config['morosity']['action'] == 'suspend'):
                raise OperationRejected('write_unconfirmed')
        after = read('/system/resource/print', **{'.proplist': 'uptime'})[0]
        resource.update(identity=identity['name'], uptime_start=resource['uptime'], uptime=after['uptime'], board=resource.pop('board-name', ''))
        return {'schema': 1, 'router': resource, 'queues': queues, 'restrictions': restrictions,
            'raspberry': {'architecture': os.uname().machine if hasattr(os, 'uname') else 'unknown', 'python': sys.version.split()[0]}}
    finally:
        api.close()

def main():
    config = {}
    try:
        config = json.loads(sys.stdin.buffer.read(65537))
        print(json.dumps({'ok': True, 'data': collect(config)}))
    except OperationRejected as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
    except ImportError:
        print(json.dumps({'ok': False, 'error': 'reader_missing'}))
    except FileNotFoundError:
        print(json.dumps({'ok': False, 'error': 'incomplete'}))
    except ssl.SSLCertVerificationError as exc:
        code = {10: 'tls_expired', 62: 'tls_hostname', 64: 'tls_hostname', 18: 'tls_untrusted',
                19: 'tls_untrusted', 20: 'tls_untrusted', 21: 'tls_untrusted'}.get(exc.verify_code, 'tls_failed')
        print(json.dumps({'ok': False, 'error': code}))
    except ssl.SSLError:
        print(json.dumps({'ok': False, 'error': 'tls_failed'}))
    except Exception as exc:
        code = 'write_unconfirmed' if 'morosity' in config else 'router_unavailable'
        if config.get('diagnostic'):
            if isinstance(exc, ConnectionRefusedError): code = 'api_refused'
            elif isinstance(exc, TimeoutError): code = 'remote_timeout'
            elif isinstance(exc, (KeyError, IndexError, TypeError, ValueError)): code = 'incomplete'
            else:
                # Solo tipos de biblioteca, nunca buscar palabras en mensajes remotos.
                from librouteros.exceptions import TrapError
                if isinstance(exc, TrapError): code = 'api_denied'
        print(json.dumps({'ok': False, 'error': code}))

if __name__ == '__main__': main()
