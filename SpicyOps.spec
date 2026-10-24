# Construcción sin carpetas de configuración, estado local ni datos de red.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os
from pathlib import Path
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
version_scope = {}
exec(Path("portal/version.py").read_text(), version_scope)
version = version_scope["VERSION"]
version_tuple = tuple(map(int, version.split("."))) + (0,)
version_info = VSVersionInfo(ffi=FixedFileInfo(filevers=version_tuple, prodvers=version_tuple, mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)), kids=[StringFileInfo([StringTable("040904B0", [StringStruct("FileDescription", "SpicyOps para Windows"), StringStruct("FileVersion", version), StringStruct("ProductName", "SpicyOps"), StringStruct("ProductVersion", version), StringStruct("OriginalFilename", "SpicyOps.exe")])]), VarFileInfo([VarStruct("Translation", [1033, 1200])])])
os.environ['DJANGO_SETTINGS_MODULE']='spicyops.portal_settings'

data = [('portal/templates', 'portal/templates'), ('portal/static', 'portal/static'),
        ('portal/remote_reader.py','portal'), ('portal/router_contract.py','portal')]
data += collect_data_files('django', includes=['conf/locale/es/**', 'conf/locale/es_MX/**'])
a = Analysis(['run_panel.py'], pathex=[], binaries=[], datas=data,
    hiddenimports=collect_submodules('django',filter=lambda name:not name.startswith(('django.contrib.gis','django.db.backends.postgresql')))+collect_submodules('portal',filter=lambda name:not name.startswith('portal.tests'))+['spicyops.portal_settings','spicyops.wsgi',
        'django.contrib.sessions.backends.signed_cookies','django.contrib.staticfiles','whitenoise.middleware'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=['librouteros','psycopg','psycopg_binary','ops','agent','tests','portal.tests','tkinter','numpy','pandas','matplotlib','django.contrib.gis','django.db.backends.postgresql'])
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='SpicyOps',debug=False,bootloader_ignore_signals=False,
    strip=False,upx=False,console=False,version=version_info,icon='portal/static/portal/app.ico')
coll = COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='SpicyOps')
