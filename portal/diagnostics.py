"""Diagnóstico de lectura independiente del historial y del estado de conexión."""
import copy
import threading
import time
import uuid
from .connector import collect, ConnectionFailure
from .store import Store
from .telemetry import normalize
from .scheduling import locality_lock

STAGES = [('access', 'Acceso a Raspberry'), ('identity', 'Identidad SSH'),
          ('auth', 'Autenticación SSH'), ('reader', 'Lector disponible'),
          ('tls', 'Certificado de MikroTik'), ('api', 'Acceso API-SSL'), ('inventory', 'Inventario')]
MESSAGES = {
    'port_open': 'La dirección se resolvió y el puerto SSH aceptó la conexión.',
    'dns_failed': 'No se pudo resolver la dirección. Revisa la dirección de Raspberry en Configurar.',
    'refused': 'El puerto rechazó la conexión. Revisa el puerto y el servicio configurados.',
    'timeout': 'Se agotó el tiempo de esta comprobación. Revisa el acceso de red y vuelve a intentar.',
    'communication': 'No se pudo completar la comunicación. Comprueba el acceso por red local o Tailscale y la configuración.',
    'host_verified': 'La huella coincide con la confirmada para esta localidad.',
    'host_new': 'Huella nueva: abre Configurar y compara la huella del equipo antes de confirmarla.',
    'host_changed': 'La huella SSH cambió. Detén el acceso y consulta al administrador; no se sustituyó la huella guardada.',
    'authenticated': 'El equipo aceptó el método de acceso SSH configurado.',
    'auth_rejected': 'El equipo rechazó el acceso SSH. Revisa el usuario y la contraseña o clave SSH en Configurar.',
    'auth_missing': 'No hay contraseña SSH guardada. Abre Configurar para introducir el acceso de esta localidad.',
    'reader_ready': 'El Python configurado puede ejecutar el lector y tiene librouteros.',
    'reader_missing': 'Falta librouteros en el Python configurado. Consulta al administrador; no se instaló nada.',
    'python_unavailable': 'No se pudo ejecutar el Python configurado. Revisa su ruta en Configurar.',
    'ca_missing': 'No se encontró la CA configurada. Revisa la ruta del certificado en Raspberry.',
    'ca_invalid': 'No se pudo cargar la CA configurada. Revisa el formato del certificado.',
    'tls_verified': 'La CA se cargó y el certificado del MikroTik pasó la validación TLS.',
    'tls_failed': 'No se pudo validar TLS. Revisa certificado, dirección y fecha del equipo.',
    'tls_expired': 'El certificado presentado está vencido según la validación TLS. Consulta al administrador.',
    'tls_hostname': 'El certificado no corresponde a la dirección configurada del MikroTik.',
    'tls_untrusted': 'La cadena del certificado no es de confianza para la CA configurada.',
    'api_auth': 'La API rechazó el acceso al autenticar. Revisa la cuenta API en Configurar; no se determinó que la contraseña sea incorrecta.',
    'api_denied': 'La API rechazó una lectura solicitada. Revisa los permisos de lectura con el administrador.',
    'api_read': 'La API aceptó el acceso y respondió a las lecturas permitidas.',
    'incomplete': 'La lectura está incompleta o su formato no es compatible. Consulta al administrador.',
    'inventory_ok': 'Inventario RouterOS 6/7 válido, con colas individuales y contadores disponibles.',
    'inventory_empty': 'Inventario válido sin clientes individuales; no es un fallo de conexión.',
    'inventory_warning': 'Inventario válido con colas ambiguas, excluidas o contadores ausentes. Revisa las colas con el administrador.',
    'inventory_version': 'La versión leída no está contemplada. El lector admite RouterOS 6 y 7.',
    'interrupted': 'El diagnóstico anterior se interrumpió. Vuelve a diagnosticar para comprobar esta etapa.',
}


def fresh_result():
    return {'id': uuid.uuid4().hex, 'started': time.time(), 'finished': None, 'running': True,
            'stale': False, 'summary': 'Comprobando acceso de lectura…',
            'stages': [dict(stage=key, label=label, state='pendiente', code='', message='Pendiente de comprobación.') for key, label in STAGES]}


def set_stage(result, stage, state, code=''):
    row = next(r for r in result['stages'] if r['stage'] == stage)
    row.update(state=state, code=code if code in MESSAGES else '',
               message=MESSAGES.get(code, 'Comprobando…' if state == 'comprobando' else 'Comprobación terminada.'))


def complete(result):
    result.update(running=False, finished=time.time())
    stopped = next((r for r in result['stages'] if r['state'] == 'error'), None)
    if not stopped:
        stopped = next((r for r in result['stages'] if r['state'] not in ('correcto', 'advertencia')), None)
        if stopped: set_stage(result, stopped['stage'], 'error', 'interrupted')
    for row in result['stages']:
        if row['state'] in ('pendiente', 'comprobando'):
            row.update(state='no_comprobada', code='dependency', message='No comprobada: depende de una etapa que no terminó correctamente.')
    checked = sum(r['state'] in ('correcto', 'advertencia') for r in result['stages'])
    result['summary'] = (f"Se detuvo en {stopped['label']}. {checked} de 7 etapas comprobadas. {stopped['message']}"
        if stopped else 'Se comprobó el acceso Raspberry → MikroTik y su lectura. Revisa las advertencias del inventario.'
        if any(r['state'] == 'advertencia' for r in result['stages']) else
        'Se comprobó el acceso Raspberry → MikroTik y su lectura en las 7 etapas.')


def run(profile, result, publish):
    deadline = time.monotonic()+60
    def progress(stage, state, code=''):
        set_stage(result, stage, state, code); publish(result)
    try:
        raw = collect(profile, progress=progress)
        progress('inventory', 'comprobando')
        if isinstance(raw, dict) and isinstance(raw.get('router'), dict) and 'version' in raw['router']:
            if not str(raw['router']['version']).startswith(('6.', '7.')):
                raise ConnectionFailure('', stage='inventory', code='inventory_version')
        sample = normalize(raw, time.time(), deadline=min(deadline, time.monotonic()+8), inclusions=profile.get('inclusions', ()))
        # Exigir estructura de las listas, incluso cuando están vacías.
        if not isinstance(raw.get('restrictions'), list): raise ValueError()
        warning = sample['excluded'] or sample['unknown_counters'] or any(c['ambiguous'] for c in sample['clients'])
        progress('inventory', 'advertencia' if warning else 'correcto',
                 'inventory_warning' if warning else 'inventory_ok' if sample['clients'] else 'inventory_empty')
    except ConnectionFailure as exc:
        stage = exc.stage if exc.stage in dict(STAGES) else next((r['stage'] for r in result['stages'] if r['state'] == 'comprobando'), 'access')
        progress(stage, 'error', exc.code)
    except TimeoutError:
        progress('inventory', 'error', 'timeout')
    except Exception:
        stage = next((r['stage'] for r in result['stages'] if r['state'] == 'comprobando'), 'inventory')
        progress(stage, 'error', 'incomplete')
    finally:
        complete(result); publish(result)


def recover(profile):
    """Un cierre de Windows nunca convierte etapas pendientes en éxitos."""
    result = profile.get('diagnostic')
    if result and result['running'] and profile.get('busy_until', 0) <= time.time():
        row = next((r for r in result['stages'] if r['state'] == 'comprobando'), result['stages'][0])
        set_stage(result, row['stage'], 'error', 'interrupted'); complete(result)
        profile['busy_until'] = 0
    return result


def start(profile_id):
    store = Store()
    result = fresh_result()
    def claim(data):
        profile = data['profiles'].get(profile_id)
        if not profile: raise ValueError('La localidad no existe.')
        if profile.get('busy_until', 0) > time.time():
            raise ValueError('La localidad tiene una operación en curso. Espera a que termine.')
        profile.update(generation=result['id'], busy_until=time.time()+75, diagnostic=result)
        return copy.deepcopy(profile)
    lock = locality_lock(profile_id)
    if not lock.acquire(blocking=False):
        raise ValueError('La localidad tiene una operación en curso. Espera a que termine.')
    try:
        profile = store.update(claim)
    finally:
        lock.release()
    def publish(value):
        def save(data):
            current = data['profiles'].get(profile_id)
            if current and current.get('generation') == result['id']:
                current['diagnostic'] = copy.deepcopy(value)
                if not value['running']: current['busy_until'] = 0
        store.update(save)
    def execute():
        with lock:
            run(profile, copy.deepcopy(result), publish)
    worker = threading.Thread(target=execute, daemon=True)
    try: worker.start()
    except RuntimeError:
        set_stage(result, 'access', 'error', 'interrupted'); complete(result); publish(result)
    return result
