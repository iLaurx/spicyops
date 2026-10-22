"""Panel conectado: no necesita PostgreSQL, migraciones ni clientes precargados."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get('SPICYOPS_STATE_DIR', BASE_DIR / '.local' / 'portal'))
STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
keyfile = STATE_DIR / 'secret.key'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if os.environ.get('SPICYOPS_PUBLIC') == '1':
        raise RuntimeError('Configura DJANGO_SECRET_KEY antes de publicar.')
    protected_keyfile = STATE_DIR / 'secret.dpapi'
    if os.name == 'nt' and (getattr(sys,'frozen',False) or protected_keyfile.exists()):
        from portal.secret import dpapi
        import secrets
        if not protected_keyfile.exists():
            seed = keyfile.read_text() if keyfile.exists() else secrets.token_urlsafe(64)
            with protected_keyfile.open('xb') as file: file.write(dpapi(seed.encode()))
            keyfile.unlink(missing_ok=True)
        SECRET_KEY = dpapi(protected_keyfile.read_bytes(),decrypt=True).decode()
    elif not keyfile.exists():
        import secrets
        try:
            with keyfile.open('x') as file:
                file.write(secrets.token_urlsafe(64))
            keyfile.chmod(0o600)
        except FileExistsError:
            pass
    if not SECRET_KEY: SECRET_KEY = keyfile.read_text()
DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')
INSTALLED_APPS = ['django.contrib.staticfiles', 'portal']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_NAME = 'spicyops_portal'
SESSION_COOKIE_AGE = 43200
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
HTTPS_ONLY = os.environ.get('SPICYOPS_PUBLIC') == '1'
SESSION_COOKIE_SECURE = HTTPS_ONLY
CSRF_COOKIE_SECURE = HTTPS_ONLY
SECURE_SSL_REDIRECT = HTTPS_ONLY
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
ROOT_URLCONF = 'portal.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.request']}}]
DATABASES = {}
STATIC_URL = '/static/'
STATIC_ROOT = None
STATICFILES_DIRS = [BASE_DIR / 'portal' / 'static']
WHITENOISE_USE_FINDERS = True
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_TZ = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
