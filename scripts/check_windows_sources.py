"""Comprueba que el EXE corresponde a las fuentes que se van a entregar."""
import argparse
import marshal
from pathlib import Path
from PyInstaller.archive.readers import ZlibArchiveReader, CArchiveReader

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--folder', type=Path, default=root/'dist'/'SpicyOps')
parser.add_argument('--workpath', type=Path, default=root/'build'/'SpicyOps')
args = parser.parse_args()
executable = CArchiveReader(str(args.folder/'SpicyOps.exe'))
assert executable.extract('PYZ.pyz') == (args.workpath/'PYZ-00.pyz').read_bytes(), 'El EXE no contiene el archivo de módulos comprobado.'
entry = marshal.loads(executable.extract('run_panel'))
assert entry == compile((root/'run_panel.py').read_text(encoding='utf-8'), entry.co_filename, 'exec', optimize=0)
archive = ZlibArchiveReader(str(args.workpath/'PYZ-00.pyz'))
assert not any(name.startswith('portal.tests') for name in archive.toc)
for module in archive.toc:
    if not module.startswith('portal.') and module != 'spicyops.portal_settings':
        continue
    source = root/(module.replace('.', '/')+'.py')
    if source.is_file():
        code = archive.extract(module)
        expected = compile(source.read_text(encoding='utf-8'), code.co_filename, 'exec', optimize=0)
        assert code == expected, f'Reconstruir módulo desactualizado: {module}'
packaged = args.folder/'_internal'/'portal'
for folder in ('templates', 'static'):
    for source in (root/'portal'/folder).rglob('*'):
        if source.is_file():
            assert source.read_bytes() == (packaged/source.relative_to(root/'portal')).read_bytes(), source
assert (root/'portal'/'remote_reader.py').read_bytes() == (packaged/'remote_reader.py').read_bytes()
assert (root/'portal'/'router_contract.py').read_bytes() == (packaged/'router_contract.py').read_bytes()
for file in args.folder.rglob('*'):
    assert file.name not in {'secret.key', 'secret.dpapi', 'connections.enc', 'runtime.json'}
    assert not any(part in {'.local', 'config-mikro', 'config-antenasyclientes'} for part in file.parts)
print('OK: módulos, plantillas, recursos y lector corresponden a las fuentes finales; sin estado privado.')
