"""Estado privado del servidor: perfiles cifrados y lecturas, nunca una base manual de clientes."""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import uuid
import math
from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet
from django.conf import settings

_mutex = threading.RLock()
_maintenance = threading.RLock()
_active_operations = 0
storage_warning = ""


@contextmanager
def operation():
    global _active_operations
    with _maintenance: _active_operations += 1
    try: yield
    finally:
        with _maintenance: _active_operations -= 1


@contextmanager
def maintenance():
    with _maintenance:
        if _active_operations:
            raise StateError('Espera a que terminen las operaciones antes de restaurar.')
        yield

@contextmanager
def locked():
    folder = Path(settings.STATE_DIR)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with _mutex, (folder / 'state.lock').open('a+b') as file:
        file.seek(0); file.write(b'1'); file.flush(); file.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            file.seek(0)
            if os.name == 'nt': msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(file, fcntl.LOCK_UN)

class StateError(ValueError):
    pass

FORMAT = 1
MAX_BYTES = 256 * 1024 * 1024
BACKUP_BYTES = 512 * 1024 * 1024
BACKUP_COUNT = 5


def validate(data):
    if not isinstance(data, dict) or type(data.get('format', 0)) is not int or data.get('format', 0) not in (0, FORMAT):
        raise StateError('Formato de datos incompatible. Conserva el archivo y usa una versión compatible.')
    if not isinstance(data.get('profiles'), dict) or not isinstance(data.get('login', {}), dict):
        raise StateError('La estructura del estado no es válida.')
    if len(data['profiles']) > 100: raise StateError('El respaldo supera las 100 localidades admitidas.')
    for key, profile in data['profiles'].items():
        if not isinstance(profile, dict) or profile.get('id') != key or not isinstance(profile.get('name'), str):
            raise StateError('La estructura de localidades no es válida.')
        if not isinstance(profile.get('metadata', {}), dict) or not isinstance(profile.get('history', []), list):
            raise StateError('Las notas o el historial no son válidos.')
        if not isinstance(profile.get('automatic', {}), dict) or len(profile.get('history', [])) > 1440:
            raise StateError('Las preferencias o el historial no son válidos.')
        for field in ('host', 'ssh_user', 'ssh_method', 'ssh_password', 'router_host', 'router_user', 'router_password', 'ca_file', 'python_path', 'key_file', 'fingerprint'):
            if field in profile and not isinstance(profile[field], str): raise StateError('El perfil de acceso no tiene una estructura válida.')
        for value in profile.get('metadata', {}).values():
            if not isinstance(value, dict) or any(not isinstance(v, str) for v in value.values()):
                raise StateError('Las notas guardadas no tienen una estructura válida.')
        config = profile.get('automatic', {})
        if ('interval' in config and config['interval'] not in (1, 5, 10, 15, 30, 60)) or ('enabled' in config and type(config['enabled']) is not bool):
            raise StateError('Las preferencias de actualización no son válidas.')
        for sample in profile.get('history', []):
            if not isinstance(sample, dict) or not isinstance(sample.get('timestamp'), (int, float)) or not isinstance(sample.get('clients'), list):
                raise StateError('El historial no es válido.')
            if not isinstance(sample.get('uptime'), (int, float)) or sample['uptime'] < 0 or not isinstance(sample.get('identity'), str):
                raise StateError('La identidad o el uptime guardados no son válidos.')
            for client in sample['clients']:
                if not isinstance(client, dict) or any(k not in client for k in ('id', 'ip', 'name', 'fingerprint', 'bytes', 'ambiguous')):
                    raise StateError('El inventario guardado no es válido.')
                for field in ('id', 'ip', 'name', 'fingerprint'):
                    if not isinstance(client[field], str): raise StateError('La identidad de una cola no es válida.')
                for field in ('bytes', 'upload_bytes', 'download_bytes'):
                    value = client.get(field)
                    if field not in client or (value is not None and (type(value) not in (int, float) or value < 0)):
                        raise StateError('Un contador guardado no es válido.')
                for field in ('plan_up_mbps', 'plan_down_mbps', 'rate_up_mbps', 'rate_down_mbps'):
                    if type(client.get(field)) not in (int, float) or client[field] < 0: raise StateError('Una velocidad guardada no es válida.')
                if type(client['ambiguous']) is not bool: raise StateError('El estado de una cola no es válido.')
    def finite_tree(value, depth=0):
        if depth > 64: raise StateError('La estructura de datos es demasiado profunda.')
        if isinstance(value, float) and not math.isfinite(value): raise StateError('Los datos contienen números inválidos.')
        if isinstance(value, dict):
            for item in value.values(): finite_tree(item, depth + 1)
        elif isinstance(value, list):
            for item in value: finite_tree(item, depth + 1)
    finite_tree(data)
    return data


def atomic(path, content):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.state-')
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(content); file.flush(); os.fsync(file.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


class Store:
    def __init__(self):
        self.path = Path(settings.STATE_DIR) / 'connections.enc'
        self.cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()))

    def decode(self, content):
        if len(content) > MAX_BYTES:
            raise StateError('El archivo supera el límite de 256 MiB.')
        try:
            return validate(json.loads(self.cipher.decrypt(content), parse_constant=lambda x: (_ for _ in ()).throw(ValueError())))
        except (InvalidToken, ValueError, TypeError, RecursionError, UnicodeError) as exc:
            if isinstance(exc, StateError): raise
            raise StateError('No se puede abrir el estado: archivo dañado o clave incorrecta. Restaura un respaldo válido; el original se conserva.') from None

    def _read(self):
        if getattr(settings, 'STATE_KEY_ERROR', False):
            raise StateError('No se puede abrir la clave de esta cuenta Windows. Usa la cuenta original o importa un respaldo portable con contraseña.')
        if not self.path.exists():
            return {'owner': None, 'profiles': {}, 'login': {}}
        return self.decode(self.path.read_bytes())

    def _backup(self):
        if not self.path.exists(): return
        content = self.path.read_bytes()
        self.decode(content)
        folder = self.path.parent / 'backups'
        folder.mkdir(exist_ok=True, mode=0o700)
        files = sorted(folder.glob('*.enc'), key=lambda p: p.name)
        # Como máximo un respaldo por hora; restaurar conserva además el original.
        if files and time.time() - files[-1].stat().st_mtime < 3600: return
        if len(content) > BACKUP_BYTES:
            raise StateError('No hay capacidad para crear el respaldo de seguridad.')
        while files and (len(files) >= BACKUP_COUNT or sum(p.stat().st_size for p in files) + len(content) > BACKUP_BYTES):
            files.pop(0).unlink()
        atomic(folder / (str(time.time_ns()) + '.enc'), content)

    def _write(self, data):
        validate(data)
        data['format'] = FORMAT
        encrypted = self.cipher.encrypt(json.dumps(data, allow_nan=False).encode())
        if len(encrypted) > MAX_BYTES: raise StateError('El estado supera el límite de 256 MiB. No se guardaron los cambios.')
        self._backup()
        atomic(self.path, encrypted)

    def restore(self, data):
        validate(data)
        with maintenance(), locked():
            try:
                current = self._read()
            except StateError:
                current = None
            if current and any(p.get('operation_active') or (p.get('busy_until') or 0) > time.time() for p in current['profiles'].values()):
                raise StateError('Espera a que terminen las operaciones antes de restaurar.')
            # Archivos originales sin rotación: nunca se eliminan automáticamente.
            archive = self.path.parent / ('original-' + str(time.time_ns()) + '-' + uuid.uuid4().hex[:8])
            archive.mkdir(mode=0o700)
            for name in ('connections.enc', 'secret.dpapi', 'secret.key'):
                original = self.path.parent / name
                if original.exists(): atomic(archive / name, original.read_bytes())
            data = json.loads(json.dumps(data))
            for profile in data['profiles'].values():
                profile.update(connected=False, operation_active=False, busy_until=0)
                profile.setdefault('automatic', {})['next_at'] = None
            data['format'] = FORMAT
            encrypted = self.cipher.encrypt(json.dumps(data, allow_nan=False).encode())
            if len(encrypted) > MAX_BYTES: raise StateError('El estado supera el límite de 256 MiB.')
            key_error = getattr(settings, 'STATE_KEY_ERROR', False)
            keypath = self.path.parent / 'secret.dpapi'
            previous_key = keypath.read_bytes() if keypath.exists() else None
            if key_error:
                from .secret import dpapi
                atomic(keypath, dpapi(settings.SECRET_KEY.encode()))
            try:
                atomic(self.path, encrypted)
            except OSError:
                if key_error:
                    if previous_key is None: keypath.unlink(missing_ok=True)
                    else: atomic(keypath, previous_key)
                raise
            settings.STATE_KEY_ERROR = False
            return archive.name

    def read(self):
        with locked(): return self._read()

    def schedule(self, previous=None):
        """Solo conserva programación sin historial ni credenciales entre ticks.

        La firma se obtiene bajo el mismo bloqueo que reemplaza el archivo;
        cambios de cualquier instancia invalidan la instantánea pequeña.
        """
        with locked():
            try:
                stat = self.path.stat()
                signature = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size, stat.st_ino)
            except FileNotFoundError:
                signature = None
            if previous is not None and previous[0] == signature:
                return previous
            profiles = [{**{k: p.get(k) for k in ('id', 'connected', 'operation_active', 'busy_until')},
                         'automatic': p.get('automatic', {})}
                        for p in self._read()['profiles'].values()]
            return signature, profiles

    def update(self, fn):
        global storage_warning
        try:
            with locked():
                data = self._read()
                result = fn(data)
                self._write(data)
                storage_warning = ''
                return result
        except OSError:
            storage_warning = 'No se pudo guardar en el almacenamiento. Comprueba espacio y permisos. Los últimos cambios pueden no estar guardados; vuelve a intentar la operación.'
            raise
