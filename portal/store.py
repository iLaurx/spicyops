"""Estado privado del servidor: perfiles cifrados y lecturas, nunca una base manual de clientes."""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
from cryptography.fernet import Fernet
from django.conf import settings

_mutex = threading.RLock()

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

class Store:
    def __init__(self):
        self.path = Path(settings.STATE_DIR) / 'connections.enc'
        self.cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()))

    def _read(self):
        if not self.path.exists():
            return {'owner': None, 'profiles': {}, 'login': {}}
        return json.loads(self.cipher.decrypt(self.path.read_bytes()))

    def _write(self, data):
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        fd, name = tempfile.mkstemp(dir=self.path.parent, prefix='.state-')
        try:
            with os.fdopen(fd, 'wb') as file:
                file.write(encrypted); file.flush(); os.fsync(file.fileno())
            os.chmod(name, 0o600)
            os.replace(name, self.path)
        finally:
            if os.path.exists(name): os.unlink(name)

    def read(self):
        with locked(): return self._read()

    def update(self, fn):
        with locked():
            data = self._read()
            result = fn(data)
            self._write(data)
            return result
