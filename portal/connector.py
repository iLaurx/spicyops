import base64
import hashlib
import json
from pathlib import Path
import shlex
import socket
import time
import queue
import threading
import paramiko

_resolvers = threading.BoundedSemaphore(2)
_operations = threading.BoundedSemaphore(4)


def resolve_bounded(host, port, timeout):
    if not _resolvers.acquire(blocking=False):
        raise ConnectionFailure('Hay resoluciones pendientes. Espera antes de reintentar.', stage='access', code='timeout')
    result = queue.Queue(maxsize=1)
    def run():
        try:
            try: result.put(socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
            except OSError as exc: result.put(exc)
        finally: _resolvers.release()
    threading.Thread(target=run, name='spicyops-dns', daemon=True).start()
    try: addresses = result.get(timeout=max(.001, timeout))
    except queue.Empty:
        raise ConnectionFailure('La dirección no se resolvió a tiempo.', stage='access', code='timeout') from None
    if isinstance(addresses, OSError):
        raise ConnectionFailure('No se pudo resolver la dirección de la Raspberry.', stage='access', code='dns_failed')
    return addresses

class ConnectionFailure(Exception):
    def __init__(self, message, stage='raspberry', fingerprint='', code='communication'):
        super().__init__(message)
        self.stage, self.fingerprint = stage, fingerprint
        self.code = code

class PinnedHostKey(paramiko.MissingHostKeyPolicy):
    def __init__(self, expected, progress=None): self.expected, self.progress = expected, progress
    def missing_host_key(self, client, hostname, key):
        actual = 'SHA256:' + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
        if not self.expected:
            raise ConnectionFailure('Confirma la huella SSH de esta Raspberry en Configurar antes de autenticarte.', fingerprint=actual, stage='identity', code='host_new')
        if actual != self.expected:
            raise ConnectionFailure('La huella SSH cambió. No se enviaron credenciales a este equipo.', stage='identity', code='host_changed')
        if self.progress:
            self.progress('identity', 'correcto', 'host_verified')
            self.progress('auth', 'comprobando', '')

def collect(profile, *, morosity=None, progress=None, total_timeout=60):
    """Espera global acotada incluso si el sistema/biblioteca bloquea DNS o cierre.

    Los trabajadores y resolutores son daemon y tienen cupo fijo; nunca se
    reintenta una escritura. Un trabajador atascado conserva su cupo.
    """
    if progress and morosity is not None:
        raise ValueError('El diagnóstico es exclusivamente de lectura.')
    if not _operations.acquire(blocking=False):
        raise ConnectionFailure('Hay comunicaciones pendientes. Espera y sincroniza antes de reintentar.', code='timeout')
    end = time.monotonic()+total_timeout
    result = queue.Queue(maxsize=1)
    cancelled = threading.Event()
    resources = {}
    def worker():
        try:
            try: result.put((True, _collect(profile, morosity=morosity, progress=progress,
                                           end=end, cancelled=cancelled, resources=resources)))
            except BaseException as exc: result.put((False, exc))
        finally: _operations.release()
    threading.Thread(target=worker, name='spicyops-ssh', daemon=True).start()
    ok = None
    while True:
        deadline = min(end, resources.get('stage_end', end)) if progress else end
        try:
            ok, value = result.get(timeout=max(.001, min(.05, deadline-time.monotonic())))
            break
        except queue.Empty:
            deadline = min(end, resources.get('stage_end', end)) if progress else end
            if time.monotonic() < deadline:
                continue
            break
    if ok is None:
        cancelled.set()
        connection = resources.get('socket')
        if connection:
            try: connection.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            connection.close()
        message = 'Se agotó el tiempo total de comunicación.'
        if morosity is not None: message += ' El resultado puede ser incierto; sincroniza antes de reintentar.'
        raise ConnectionFailure(message, stage=resources.get('stage', 'access'), code='timeout') from None
    if not ok:
        if morosity is not None and isinstance(value, ConnectionFailure):
            value = ConnectionFailure(str(value)+' El resultado puede ser incierto; sincroniza antes de reintentar.',
                                      stage=value.stage, code=value.code, fingerprint=value.fingerprint)
        raise value
    return value


def _collect(profile, *, morosity, progress, end, cancelled, resources):
    if progress and morosity is not None:
        raise ValueError('El diagnóstico es exclusivamente de lectura.')
    stage = 'access'
    stage_end = min(end, time.monotonic()+8)
    def report(name, state, code=''):
        nonlocal stage, stage_end
        if cancelled.is_set() or time.monotonic() >= end:
            raise ConnectionFailure('Se agotó el tiempo total de comunicación.', stage=stage, code='timeout')
        if state == 'comprobando':
            stage = name
            resources['stage'] = name
            stage_end = min(end, time.monotonic() + (25 if name == 'api' else 8))
            resources['stage_end'] = stage_end
        if progress: progress(name, state, code)
        if progress and name == 'auth' and state == 'comprobando' and profile.get('ssh_method') == 'password' and not profile.get('ssh_password'):
            raise ConnectionFailure('No hay contraseña SSH guardada. Revisa Configurar.', stage='auth', code='auth_missing')
    def remaining():
        left = (min(end, stage_end) if progress else end)-time.monotonic()
        if left <= 0 or cancelled.is_set():
            raise ConnectionFailure('Se agotó el tiempo de comprobación. Revisa el acceso de red y vuelve a intentar.', stage=stage, code='timeout')
        return left
    client = paramiko.SSHClient()
    connection = None
    # Pin independiente por localidad; no se modifica known_hosts del equipo.
    client.set_missing_host_key_policy(PinnedHostKey(profile.get('fingerprint', ''), report if progress else None))
    try:
        report('access', 'comprobando')
        # El resolutor del sistema no ofrece timeout; aislarlo en un hilo
        # daemon sin secretos ni recursos SSH y esperar solo el presupuesto.
        host, port = profile['host'], profile['port']
        addresses = resolve_bounded(host, port, min(8, remaining()))
        errors = []
        for family, kind, proto, _, address in addresses:
            connection = socket.socket(family, kind, proto)
            resources['socket'] = connection
            try:
                connection.settimeout(min(8, remaining()/max(1, len(addresses)))); connection.connect(address)
                break
            except OSError as exc:
                connection.close(); connection = None; errors.append(exc)
        if connection is None:
            code = ('refused' if errors and all(isinstance(e, ConnectionRefusedError) for e in errors)
                    else 'timeout' if errors and all(isinstance(e, TimeoutError) for e in errors) else 'communication')
            raise ConnectionFailure('No se pudo acceder al puerto SSH. Comprueba que la PC tenga acceso a la Raspberry por red local o Tailscale.', stage='access', code=code)
        report('access', 'correcto', 'port_open')
        report('identity', 'comprobando')
        use_key = profile.get('ssh_method') == 'key'
        options = {'sock': connection}
        client.connect(profile['host'], port=profile['port'], username=profile['ssh_user'],
            password=None if use_key else profile.get('ssh_password') or None,
            passphrase=profile.get('ssh_password') or None if use_key else None,
            key_filename=profile.get('key_file') or None if use_key else None,
            look_for_keys=use_key, allow_agent=use_key, timeout=min(8, remaining()),
            banner_timeout=min(8, remaining()), auth_timeout=min(8, remaining()), **options)
        if progress:
            remaining()
            report('auth', 'correcto', 'authenticated')
            report('reader', 'comprobando')
        source = (Path(__file__).parent / 'remote_reader.py').read_text(encoding='utf-8')
        source = (Path(__file__).parent / 'router_contract.py').read_text(encoding='utf-8')+'\n'+source
        # Bootstrap fijo. El ejecutable configurado se pasa como dato, nunca como shell.
        bootstrap = """import sys,json,os,subprocess
p=json.loads(sys.stdin.read()); budget=p.pop('_timeout',45)
exe=os.path.expanduser(p.pop('python_path')); code=p.pop('_reader')
try:
 child=subprocess.Popen([exe,'-B','-u','-c',code],stdin=subprocess.PIPE,stdout=sys.stdout,stderr=subprocess.DEVNULL,text=True)
 try: child.communicate(json.dumps(p),timeout=budget)
 except subprocess.TimeoutExpired:
  child.kill(); child.wait(); print(json.dumps({'ok':False,'error':'remote_timeout'}),flush=True); sys.exit(0)
 if child.returncode: print(json.dumps({'ok':False,'error':'python_unavailable'}),flush=True)
except OSError: print(json.dumps({'ok':False,'error':'python_unavailable'}),flush=True)
"""
        command = 'python3 -B -c ' + shlex.quote(bootstrap)
        stdin, stdout, stderr = client.exec_command(command, timeout=remaining())
        payload = {key: profile[key] for key in ('python_path', 'router_host', 'router_user', 'router_password', 'ca_file')}
        payload['_reader'] = source
        payload['_timeout'] = max(.001, min(45, remaining()-1))
        payload['inclusions'] = list(profile.get('inclusions', ()))
        if progress: payload['diagnostic'] = True
        if morosity is not None:
            payload['morosity'] = morosity
        remaining()
        stdin.channel.settimeout(remaining())
        stdin.write(json.dumps(payload)); stdin.flush(); stdin.channel.shutdown_write()
        channel = stdout.channel
        output = bytearray()
        received = 0
        deadline = end
        # Consumir ambos canales evita bloqueo y limita memoria. Nunca registrar stderr.
        while True:
            remaining()
            if channel.recv_ready():
                part = channel.recv(65536); received += len(part); output.extend(part)
            if progress:
                while b'\n' in output:
                    line, _, rest = output.partition(b'\n')
                    try: event = json.loads(line)
                    except (ValueError, UnicodeError): break
                    if not isinstance(event, dict) or 'event' not in event: break
                    # Solo aceptar transiciones esperadas del lector acotado.
                    transitions = {('reader','reader'): ('tls','reader_ready'), ('tls','tls'): ('api','tls_verified')}
                    transition = transitions.get((stage, event['event']))
                    if transition:
                        following, code = transition
                        report(stage, 'correcto', code); report(following, 'comprobando')
                    output = bytearray(rest)
            if channel.recv_stderr_ready(): channel.recv_stderr(65536)
            if received > 2_000_000:
                raise ConnectionFailure('La respuesta de la Raspberry excede el límite de lectura.')
            if channel.exit_status_ready() and not channel.recv_ready(): break
            if time.monotonic() > deadline: raise ConnectionFailure('La Raspberry no terminó la lectura a tiempo.')
            time.sleep(.01)
        remaining()
        try: result = json.loads(output)
        except (ValueError, UnicodeError):
            raise ConnectionFailure('No se pudo iniciar el lector Python en la Raspberry. Revisa el intérprete configurado.', stage=stage if progress else 'raspberry', code='python_unavailable' if stage == 'reader' else 'incomplete') from None
        if not isinstance(result, dict):
            raise ConnectionFailure('Respuesta del lector no compatible.', stage=stage, code='incomplete')
        if not result.get('ok'):
            error = result.get('error')
            messages = {'reader_missing': 'Raspberry conectada. Falta librouteros en el intérprete seleccionado.',
                'ca_missing': 'Raspberry conectada. No se encontró el certificado CA indicado.',
                'tls_failed': 'Raspberry conectada. El certificado del MikroTik no pasó la validación TLS.',
                'python_unavailable': 'Raspberry conectada. No se pudo ejecutar el intérprete Python indicado.',
                'router_unavailable': 'Raspberry conectada. No se pudo leer el MikroTik por API-SSL; revisa dirección, cuenta y permisos de lectura.',
                'client_changed': 'El cliente o el router cambió. Sincroniza y revisa su IP antes de continuar.',
                'restriction_ambiguous': 'La restricción es compartida, dinámica o duplicada. Debe revisarla el administrador en MikroTik.',
                'write_unconfirmed': 'No se pudo confirmar el cambio en Morosos. Sincroniza antes de reintentar; comprueba los permisos de escritura de la cuenta API. No se cambiaron permisos.'}
            codes = {'reader_missing':('reader','reader_missing'), 'python_unavailable':('reader','python_unavailable'),
                'ca_missing':('tls','ca_missing'), 'ca_invalid':('tls','ca_invalid'),
                'tls_failed':('tls','tls_failed'), 'tls_expired':('tls','tls_expired'),
                'tls_hostname':('tls','tls_hostname'), 'tls_untrusted':('tls','tls_untrusted'),
                'api_auth':('api','api_auth'), 'api_denied':('api','api_denied'),
                'router_unavailable':(stage,'communication'), 'remote_timeout':(stage,'timeout'),
                'api_refused':(stage,'refused'), 'incomplete':('api','incomplete')}
            failed_stage, code = codes.get(error, (stage, 'communication'))
            raise ConnectionFailure(messages.get(error, 'Raspberry conectada; lectura del MikroTik incompleta.'), stage=failed_stage if progress else 'router', code=code)
        if progress:
            if stage != 'api':
                raise ConnectionFailure('El lector no confirmó todas las etapas.', stage=stage, code='incomplete')
            report('api', 'correcto', 'api_read')
        return result['data']
    except ConnectionFailure: raise
    except paramiko.AuthenticationException:
        raise ConnectionFailure('La Raspberry rechazó el método de autenticación. Revisa el usuario y el acceso SSH en Configurar.', stage='auth', code='auth_rejected') from None
    except (paramiko.SSHException, OSError, socket.timeout, EOFError) as exc:
        raise ConnectionFailure('No se pudo completar la comunicación SSH. Revisa el acceso a la Raspberry.', stage=stage if progress else 'raspberry', code='timeout' if isinstance(exc, TimeoutError) or (progress and time.monotonic() >= stage_end) else 'communication') from None
    finally:
        client.close()
        if connection: connection.close()
