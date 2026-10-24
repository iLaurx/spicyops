"""Traslado cifrado autenticado: scrypt + Fernet, independiente de DPAPI."""
import base64
import json
import os
from datetime import datetime
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from .store import Store, StateError, validate, MAX_BYTES, locked


def portable_key(password, salt):
    if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
        raise StateError('Usa una contraseña de 12 a 1024 caracteres. Consérvala fuera de SpicyOps.')
    return Fernet(base64.urlsafe_b64encode(Scrypt(salt=salt, length=32, n=32768, r=8, p=1).derive(password.encode())))


def export_data(data, password):
    validate(data)
    salt = os.urandom(16)
    token = portable_key(password, salt).encrypt(json.dumps(data, allow_nan=False).encode())
    return b'SPICYOPS-PORTABLE-1\n' + base64.urlsafe_b64encode(salt) + b'\n' + token


def import_data(content, password):
    if len(content) > MAX_BYTES: raise StateError('El respaldo supera el límite de 256 MiB.')
    try:
        header, encoded, token = content.split(b'\n', 2)
        if header != b'SPICYOPS-PORTABLE-1': raise StateError('Formato de respaldo portable incompatible.')
        salt = base64.b64decode(encoded, altchars=b'-_', validate=True)
        if len(salt) != 16: raise ValueError()
        plain = portable_key(password, salt).decrypt(token)
        return validate(json.loads(plain))
    except (InvalidToken, ValueError, TypeError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, StateError): raise
        raise StateError('Contraseña incorrecta o respaldo dañado. No se modificó el estado.') from None


@sensitive_post_parameters('password')
def recovery_page(request):
    store = Store()
    error = ''
    message = ''
    try:
        store.read()
        healthy = True
    except (StateError, OSError) as exc:
        healthy = False
        error = str(exc) if isinstance(exc, StateError) else 'No se puede acceder al almacenamiento. Comprueba espacio y permisos de tu cuenta Windows.'
    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            if action == 'export':
                content = export_data(store.read(), request.POST.get('password', ''))
                response = HttpResponse(content, content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename="SpicyOps-respaldo.spicybackup"'
                response['Cache-Control'] = 'no-store'
                return response
            if request.POST.get('confirmed') != 'yes':
                raise StateError('Confirma la restauración. Las localidades quedarán desconectadas hasta que las reconectes.')
            if action == 'restore':
                name = request.POST.get('backup', '')
                if name not in {p.name for p in (store.path.parent / 'backups').glob('*.enc')}:
                    raise StateError('Selecciona un respaldo local disponible.')
                with locked(): data = store.decode((store.path.parent / 'backups' / name).read_bytes())
            elif action == 'import':
                upload = request.FILES.get('backup_file')
                if upload is None or upload.size > MAX_BYTES: raise StateError('Selecciona un respaldo portable de hasta 256 MiB.')
                data = import_data(upload.read(MAX_BYTES + 1), request.POST.get('password', ''))
            else: raise StateError('Acción no válida.')
            archive = store.restore(data)
            healthy = True
            error = ''
            message = 'Restauración completada. Originales conservados en ' + archive + '. Reconecta cada localidad cuando estés listo.'
        except (StateError, OSError) as exc:
            error = str(exc) if isinstance(exc, StateError) else 'No se pudo guardar. Comprueba espacio y permisos; conserva los archivos originales y vuelve a intentar.'
    backups = []
    for path in sorted((store.path.parent / 'backups').glob('*.enc'), reverse=True):
        try:
            store.decode(path.read_bytes())
            label = datetime.fromtimestamp(path.stat().st_mtime, timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M')
            backups.append({'name': path.name, 'label': label})
        except (StateError, OSError): pass
    return render(request, 'portal/recovery.html', dict(page='connections', healthy=healthy, error=error, message=message, backups=backups))
