"""Contrato compartido sin dependencias de Django ni direcciones reales."""
import ipaddress

ACTIONS = ('provision', 'suspend', 'resume', 'plan')
STATE_KEYS = {'service', 'ip', 'revision', 'enabled', 'up_kbps', 'down_kbps'}

def validate_target(ip, allowed):
    address = ipaddress.ip_address(ip)
    if address.version != 4 or str(address) != ip or ip not in allowed:
        raise ValueError('Destino fuera del inventario aprobado.')
    if int(ip.split('.')[-1]) in {0, 1, 2, 3, 4, 5, 6, 50, 90, 255}:
        raise ValueError('Destino reservado para infraestructura.')

def validate_state(state, allowed):
    if not isinstance(state, dict) or set(state) != STATE_KEYS:
        raise ValueError('Contrato de estado inválido.')
    validate_target(state['ip'], allowed)
    if type(state['enabled']) is not bool:
        raise ValueError('Estado inválido.')
    for key in ('service', 'revision', 'up_kbps', 'down_kbps'):
        if type(state[key]) is not int or state[key] <= 0:
            raise ValueError('Parámetro numérico inválido.')
    if max(state['up_kbps'], state['down_kbps']) > 1000000:
        raise ValueError('Límite fuera de contrato.')
    return state
