import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Archivo de desarrollo generado localmente; nunca se versiona.
local = BASE_DIR / '.local' / 'settings.json'
LOCAL = json.loads(local.read_text()) if local.exists() else {}

def setting(name, default=None):
    return os.environ.get(name, LOCAL.get(name, default))

SECRET_KEY = setting('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('Falta DJANGO_SECRET_KEY; ejecutar scripts/local.ps1 setup o configurar entorno.')
DEBUG = setting('DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = setting('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
                  'django.contrib.messages', 'django.contrib.staticfiles', 'ops']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
              'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
              'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware']
ROOT_URLCONF = 'spicyops.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True,
              'OPTIONS': {'context_processors': ['django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'spicyops.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': setting('PGDATABASE', 'spicyops'),
    'USER': setting('PGUSER', 'spicyops'), 'PASSWORD': setting('PGPASSWORD', ''),
    'HOST': setting('PGHOST', '127.0.0.1'), 'PORT': setting('PGPORT', '55432'), 'CONN_MAX_AGE': 0}}
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = setting('HTTPS_ONLY', '0') == '1'
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_SSL_REDIRECT = SESSION_COOKIE_SECURE
DATA_UPLOAD_MAX_MEMORY_SIZE = 32768
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}]
