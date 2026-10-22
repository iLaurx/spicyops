# Construcción sin carpetas de configuración, estado local ni datos de red.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os
os.environ['DJANGO_SETTINGS_MODULE']='spicyops.portal_settings'

data = [('portal/templates', 'portal/templates'), ('portal/static', 'portal/static'),
        ('portal/remote_reader.py','portal')]
data += collect_data_files('django', includes=['conf/locale/es/**', 'conf/locale/es_MX/**'])
a = Analysis(['run_panel.py'], pathex=[], binaries=[], datas=data,
    hiddenimports=collect_submodules('django',filter=lambda name:not name.startswith(('django.contrib.gis','django.db.backends.postgresql')))+collect_submodules('portal',filter=lambda name:not name.startswith('portal.tests'))+['spicyops.portal_settings','spicyops.wsgi',
        'django.contrib.sessions.backends.signed_cookies','django.contrib.staticfiles','whitenoise.middleware'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=['psycopg','psycopg_binary','ops','agent','tests','portal.tests','tkinter','numpy','pandas','matplotlib','django.contrib.gis','django.db.backends.postgresql'])
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='SpicyOps',debug=False,bootloader_ignore_signals=False,
    strip=False,upx=False,console=False,icon='portal/static/portal/app.ico')
coll = COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='SpicyOps')
