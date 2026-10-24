"""Avisos desde metadatos y licencias instalados; sin atribuir licencia propia."""
from pathlib import Path
import importlib.metadata as metadata
import sys
import shutil
import zipfile
import json
ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'build'/'release-notices'
folder.mkdir(parents=True, exist_ok=True)
excluded = {'pip', 'setuptools', 'psycopg', 'psycopg-binary', 'librouteros'}
lines = ['SpicyOps: licencia propia, titular y soporte pendientes de decisión del propietario.',
         'Dependencias sin modificaciones. Este inventario usa los metadatos instalados.',
         'Se incluyen textos originales en licenses/ y fuentes LGPL instaladas en LGPL-sources.zip.',
         'librouteros se usa en la Raspberry existente; no se distribuye en el EXE.',
         'No se concede una licencia nueva ni se atribuye autoría sobre terceros.', '']
for dist in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
    name = dist.metadata['Name']
    if name.lower() in excluded: continue
    license_name = dist.metadata.get('License-Expression') or dist.metadata.get('License') or 'Ver textos originales'
    lines.append(f'{name} {dist.version}: {license_name}')
    for entry in dist.files or []:
        if any(token in entry.name.lower() for token in ('license', 'copying', 'notice', 'authors')) and '.dist-info' in str(entry):
            source = Path(dist.locate_file(entry))
            if source.is_file():
                target = folder/'licenses'/name/entry.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
python_license = Path(sys.base_prefix)/'LICENSE.txt'
if python_license.exists():
    shutil.copyfile(python_license, folder/'licenses'/'Python-LICENSE.txt')
lines += ['', 'Fuentes/proyectos oficiales:', 'https://github.com/paramiko/paramiko/tree/4.0.0',
          'https://github.com/moses-palmer/pystray/tree/v0.19.5',
          'https://pyinstaller.org/en/stable/license.html',
          'https://docs.python.org/3/license.html',
          'PyInstaller: GPL con excepción del bootloader; no sustituye licencias de dependencias.',
          'Paramiko declara LGPL-2.1; pystray declara LGPLv3 en metadatos.',
          'Revisar condiciones de redistribución con el propietario antes de publicar; no se ha decidido licencia propia.']
text = '\n'.join(lines)+'\n'
(ROOT/'docs'/'THIRD-PARTY-NOTICES.txt').write_text(text, encoding='utf-8')
with zipfile.ZipFile(folder/'LGPL-sources.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in ('paramiko', 'pystray'):
        import importlib.util
        spec = importlib.util.find_spec(name)
        source_root = Path(spec.origin).parent
        for source in source_root.rglob('*.py'):
            if 'tests' not in source.parts:
                archive.write(source, Path(name)/source.relative_to(source_root))
        for source in (folder/'licenses'/name).glob('*'):
            archive.write(source, Path(name)/source.name)
print('Avisos y textos de licencias recopilados desde dependencias locales.')
