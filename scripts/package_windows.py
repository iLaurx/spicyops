from pathlib import Path
import argparse
import zipfile

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--folder',type=Path,default=root/'dist'/'SpicyOps')
parser.add_argument('--archive',type=Path,default=root/'dist'/'SpicyOps-Windows.zip')
args=parser.parse_args()
folder=args.folder.resolve()
assert (folder/'SpicyOps.exe').is_file(),'Construir primero el programa.'
(folder/'LEEME.txt').write_text('''SpicyOps para Windows

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
        assert not any(part in ('.local','config-mikro','config-antenasyclientes') for part in file.parts)
        assert file.name not in ('secret.key','secret.dpapi','connections.enc','runtime.json')
archive=args.archive.resolve()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as output:
    for file in folder.rglob('*'):
        if file.is_file():output.write(file,Path('SpicyOps')/file.relative_to(folder))
print(f'Distribución Windows creada: {archive.stat().st_size/1024/1024:.1f} MB. Sin perfiles ni estado privado.')
