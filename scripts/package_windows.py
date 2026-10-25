from pathlib import Path
import argparse
import zipfile
import sys
import hashlib
import json
import shutil

root=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from portal.version import VERSION
release=root/'dist'/f'SpicyOps-{VERSION}-Windows'
parser=argparse.ArgumentParser()
parser.add_argument('--folder',type=Path,default=release/'SpicyOps')
parser.add_argument('--archive',type=Path,default=release/f'SpicyOps-{VERSION}-Windows.zip')
args=parser.parse_args()
folder=args.folder.resolve()
assert (folder/'SpicyOps.exe').is_file(),'Construir primero el programa.'
(folder/'LEEME.txt').write_text(f'''SpicyOps {VERSION} para Windows

Respaldos y traslado: abre Respaldos al pie de la aplicación.
Consulta GUIA.md y NOTAS-DE-VERSION.md. Paquete sin firma digital.

Abre SpicyOps.exe. Conserva la carpeta _internal junto al programa.
No necesitas instalar Python ni PostgreSQL.

Conexiones > Nueva localidad: indica el acceso SSH de tu Raspberry y el acceso
API-SSL de lectura de su MikroTik. Usa tu conexión LAN o Tailscale habitual.
Confirma la huella SSH de tu equipo. El programa no instala servicios remotos.

Conexiones > Diagnosticar comprueba por etapas el acceso de lectura, conserva
el resultado con fecha y muestra que revisar. No modifica Clientes ni Analytics
y no comprueba que los clientes tengan internet.

Clientes se genera desde las colas del router. Puedes guardar nombre visible,
contacto, ubicación y notas. Analytics muestra contadores y consumo observado
con fechas y estimaciones por cliente a 24 horas/30 días, aproximadas por uptime. Las velocidades se muestran en Mbps o MB/s.

Cada instalación guarda sus accesos y notas de forma privada en la cuenta Windows.
El icono de la bandeja permite volver a abrir la ventana o salir de SpicyOps.
Conexiones > Actualización automática: activar, elegir intervalo y guardar.
Empieza desactivada, con 5 minutos seleccionados. Desmarcar y guardar pausa.
Funciona con la ventana cerrada si el icono sigue en la bandeja. No hay lecturas
con la PC apagada/suspendida ni al salir de SpicyOps. No recupera ciclos perdidos.
La distribución comienza vacía y no cambia velocidades ni permisos.
Clientes > Suspender permite suspender o reactivar con un interruptor, previa
confirmación de cliente e IP. Es un cambio real a la lista Morosos: requiere
cuenta API con escritura y reglas de bloqueo existentes. No configura firewall.
El estado de la lista no acredita por sí solo corte o reconexión físicos.
Clientes > Revisar colas excluidas permite incluir una cola individual valida
filtrada por infraestructura y revertir la excepcion. No crea clientes manuales
ni escribe al router. Los rangos/subredes y restricciones activas ambiguas de
Morosos bloquean cambios individuales. Un resultado incierto exige sincronizar.
Las comunicaciones tienen un presupuesto total de 60 segundos, incluido DNS.
''',encoding='utf-8')
for file in folder.rglob('*'):
    if file.is_file():
        assert not any(part in ('.local','config-mikro','config-antenasyclientes','fixtures','tests','backups') or part.startswith('original-') for part in file.parts)
        assert file.name not in ('secret.key','secret.dpapi','connections.enc','runtime.json')
archive=args.archive.resolve()
for source, target in [('LICENSE', 'LICENSE'), ('docs/guia-publica.md', 'GUIA.md'), ('docs/release-1.0.0.md', 'NOTAS-DE-VERSION.md'), ('docs/THIRD-PARTY-NOTICES.txt', 'THIRD-PARTY-NOTICES.txt')]:
    shutil.copyfile(root/source, folder/target)
shutil.copytree(root/'build'/'release-notices'/'licenses', folder/'licenses', dirs_exist_ok=True)
shutil.copyfile(root/'build'/'release-notices'/'LGPL-sources.zip', folder/'LGPL-sources.zip')
# Comprimir después de incorporar las guías y avisos.
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as output:
    for file in sorted(folder.rglob('*')):
        if file.is_file(): output.write(file, Path('SpicyOps')/file.relative_to(folder))
entries = {}
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    for file in folder.rglob('*'):
        if file.is_file():
            name = (Path('SpicyOps')/file.relative_to(folder)).as_posix()
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            assert hashlib.sha256(zipped.read(name)).hexdigest() == digest
            entries[name] = digest
    assert set(zipped.namelist()) == set(entries)
report = {'version': VERSION, 'files': len(entries), 'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (folder/'SpicyOps.exe', archive)}, 'contents': entries}
(archive.parent/'integridad.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k,v in report.items() if k != 'contents'}, indent=2))
