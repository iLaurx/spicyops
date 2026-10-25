# Conectar una localidad a SpicyOps

Guía de preparación para Raspberry Pi, Tailscale y MikroTik con acceso de lectura y escritura. Preparada el **24 de octubre de 2026** para SpicyOps para Windows. Puede utilizarse como contenido de una página de ayuda.

Los comandos son instrucciones para el administrador: no se ejecutaron al crear este documento. No contienen contraseñas reales ni configuran clientes de forma automática.

## Cómo funciona

```mermaid
flowchart LR
    PC[Windows con SpicyOps] -->|SSH por LAN o Tailscale| R[Raspberry de la localidad]
    R -->|API-SSL TCP 8729 con certificado validado| M[MikroTik local]
    M --> C[Colas y lista Morosos]
```

La aplicación abre SSH en la Raspberry y ejecuta un lector temporal con el Python disponible. Desde ahí accede al MikroTik. No necesita un servicio SpicyOps permanente en Raspberry ni publicar puertos en internet.

La API de MikroTik se utiliza con **usuario, contraseña y API-SSL**. No hay un token que debas extraer del router. La clave SSH de Raspberry y la contraseña API de MikroTik son accesos diferentes.

**Si la localidad ya está preparada**, utiliza la sección [Localidad existente](#localidad-existente) y la tabla [Datos que debes capturar](#datos-que-debes-capturar-en-spicyops). No vuelvas a crear certificados o usuarios existentes.

## Datos de ejemplo que debes adaptar

| Dato | Ejemplo de esta guía | Qué debes conservar |
|---|---|---|
| LAN de la localidad | `192.168.8.0/24` | Rango real de esa localidad |
| MikroTik desde Raspberry | `192.168.8.1` | IP real; también se usa en el SAN del certificado |
| Raspberry en la LAN | `192.168.8.90` | IP estable real, permitida en usuario y servicio API |
| Usuario Linux | El que muestre `whoami` | No confundir con usuario MikroTik |
| Raspberry desde Windows | IP Tailscale o nombre del dispositivo | Dirección accesible desde la PC |
| Puerto SSH | `22` | Puerto real de OpenSSH |
| Puerto API-SSL | `8729` | La versión actual de SpicyOps utiliza ese puerto |
| Usuario API | `spicyops-agent` | Cuenta dedicada del router |
| Grupo para instalación nueva | `spicyops-control` | Grupo dedicado con `read,write,api` |
| Lista de suspensión | `Morosos` | Nombre exacto utilizado por el programa |
| Interfaz de internet | `WAN` | Nombre real de la interfaz de salida, si preparas reglas |

**Sustituye las direcciones y marcadores antes de ejecutar.** Los ejemplos son para una LAN concreta, no valores universales. Usa una IP estable para Raspberry mediante la configuración/reserva apropiada de tu red; esta guía no cambia su dirección ni el servidor DHCP.

Cada bloque indica dónde ejecutarlo. `routeros` corresponde a **Terminal de WinBox/MikroTik**, `bash` a **Raspberry** y `powershell` a **Windows**. No pegues comandos Linux en la terminal del router.

## 1. Inventario y respaldo del MikroTik

**Dónde: MikroTik, con una cuenta de administrador.**

```routeros
/system resource print
/system clock print
/ip address print
/ip service print detail without-paging
/certificate print detail without-paging
/user group print detail without-paging
/ip firewall filter print detail without-paging
```

Confirma IP de gestión, versión, fecha/hora y políticas existentes. Esta guía utiliza funciones disponibles en RouterOS 6.49.x y 7; no requiere REST ni actualizar de versión.

Antes de cambiar servicios o firewall, conserva un respaldo. **Reemplaza la clave de respaldo; no uses literalmente el marcador.**

```routeros
/system backup save name=antes-spicyops password="REEMPLAZA_POR_CLAVE_DE_RESPALDO"
/export file=antes-spicyops
```

Descarga los archivos desde **WinBox → Files** y almacénalos de forma privada. El `.backup` permite recuperación y contiene información sensible. El `.rsc` es texto para inspección; la exportación normal oculta campos sensibles reconocidos, pero puede conservar secretos escritos dentro de scripts o comentarios. Revisa cualquier archivo antes de compartirlo y no publiques respaldos en la página de ayuda.

Mantén una sesión de administración disponible. Para cambios de acceso/firewall puedes activar **Safe Mode con Ctrl+X** en la terminal y salir con Ctrl+X después de comprobar el resultado. No cambies WinBox/SSH ni restaures todo el router para resolver un fallo individual de API.

Fuentes: [configuración y exportación](https://help.mikrotik.com/docs/spaces/ROS/pages/328155/Configuration%2BManagement), [respaldos de MikroTik](https://help.mikrotik.com/docs/spaces/ROS/pages/40992852/Backup).

## 2. Preparar Raspberry: SSH y Python

**Dónde: Raspberry.** Si ya dispone de estos componentes, consulta sus versiones y reutiliza el entorno existente.

```bash
whoami
cat /etc/os-release
uname -m
hostname -I
python3 --version
```

Para una instalación nueva en Raspberry Pi OS/Raspbian basado en Debian:

```bash
sudo apt update
sudo apt install -y curl openssh-server python3 python3-venv openssl
sudo systemctl enable --now ssh
```

Preparar un entorno separado requiere Python **3.10 o posterior** para la biblioteca elegida; el piloto anterior utilizó Python 3.11.2 en ARMv6. No reinstales el sistema operativo para seguir esta guía si el equipo ya funciona.

```bash
python3 -m venv "$HOME/spicyops/.venv"
"$HOME/spicyops/.venv/bin/python" -m pip install "librouteros==4.2.2"
"$HOME/spicyops/.venv/bin/python" -m pip check
"$HOME/spicyops/.venv/bin/python" -c 'from importlib.metadata import version; import librouteros; print("librouteros:", version("librouteros"))'
printf 'Python para SpicyOps: %s/spicyops/.venv/bin/python\n' "$HOME"
```

Conserva la ruta del entorno, por ejemplo `/home/operador/spicyops/.venv/bin/python`, para el formulario. No la sustituyas por `/usr/bin/python3` si solo instalaste librouteros dentro del entorno.

`pip check` debe indicar `No broken requirements found.`. No hace falta instalar pip global, activar el entorno ni usar `sudo pip`. Si falla `venv`, revisa que el paquete `python3-venv` corresponda al Python instalado; detente ante un error en lugar de continuar con una instalación incompleta.

Comprueba OpenSSH y obtiene su huella para compararla después desde Windows:

```bash
systemctl is-active ssh
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
```

Si el equipo no tiene clave de host ED25519, consulta la huella de la clave que realmente presente. La huella es pública, pero su comparación debe hacerse por una vía de administración confiable.

Fuentes: [Python y entornos virtuales](https://docs.python.org/3.11/library/venv.html), [librouteros 4.2.2](https://pypi.org/project/librouteros/4.2.2/).

## 3. Conectar Raspberry y Windows mediante Tailscale

**Dónde: Raspberry.** Para una instalación nueva:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
tailscale status
```

Abre el enlace de autenticación que muestre Tailscale y registra el equipo en la tailnet administrada. En Windows instala el [cliente oficial de Tailscale](https://tailscale.com/download/windows), inicia sesión con acceso autorizado a esa Raspberry y comprueba que ambos equipos aparezcan.

La política de acceso de la tailnet y el firewall de Raspberry deben permitir **Windows → Raspberry TCP/22**. Pertenecer a una tailnet no sustituye esos permisos. Esta guía usa **OpenSSH normal sobre Tailscale** con contraseña o clave; no necesitas habilitar `--ssh` de Tailscale para ese método.

**Dónde: PowerShell de Windows.** Reemplaza los dos marcadores por los datos reales:

```powershell
Test-NetConnection IP_TAILSCALE_RASPBERRY -Port 22
ssh USUARIO_RASPBERRY@IP_TAILSCALE_RASPBERRY
```

Compara la huella antes de aceptar la primera conexión. La contraseña solicitada aquí es la de **Raspberry**. No la publiques ni la escribas en la página.

Si ya usas Tailscale y SSH funciona, omite la instalación. No ejecutes `tailscale up --reset` ni borres rutas existentes para conectar SpicyOps.

Fuente: [instalar Tailscale en Linux](https://tailscale.com/docs/install/linux).

### Opcional: acceso directo a la subred, como en las imágenes

**SpicyOps no necesita anunciar la LAN completa** cuando puede entrar por SSH a Raspberry: la consulta al MikroTik se hace desde esa Raspberry. Esta sección permite además acceder directamente desde Windows al MikroTik o a antenas de la LAN.

**Dónde: Raspberry.** Usar un archivo dedicado evita añadir las mismas líneas repetidas en cada ejecución:

```bash
printf 'net.ipv4.ip_forward = 1\nnet.ipv6.conf.all.forwarding = 1\n' | sudo tee /etc/sysctl.d/99-spicyops-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-spicyops-tailscale.conf
sudo tailscale set --advertise-routes=192.168.8.0/24
```

`--advertise-routes` establece la lista de rutas anunciadas: si ya anuncia otras, incluye todas las que deban conservarse. En el panel administrativo de Tailscale aprueba la ruta y verifica la política que permite usarla. Anunciarla por sí solo no acredita que esté autorizada. Revisa también el firewall de forwarding del dispositivo.

En una localidad nueva, el comando de las imágenes `sudo tailscale up --advertise-routes=192.168.8.0/24` combina inicio y anuncio. Con una Raspberry ya autenticada, `tailscale set` cambia esa preferencia sin tener que repetir todas las demás.

Para varias localidades, crea un perfil por Raspberry usando su IP/nombre de Tailscale. Las LAN pueden repetir direcciones porque cada Raspberry consulta localmente su router. El acceso directo por rutas de subred repetidas sí requiere resolver la ambigüedad; no anuncies LAN idénticas suponiendo que la misma IP seleccionará automáticamente la localidad deseada.

Fuente: [subnet routers de Tailscale](https://tailscale.com/docs/features/subnet-routers).

## 4. Crear certificado para API-SSL

**Dónde: MikroTik.** Revisa primero `/certificate print detail`. Si ya tienes una CA y certificado válido que cubra la IP del router, reutilízalos. No repitas estos `add` sobre una instalación preparada.

Para una instalación nueva con MikroTik `192.168.8.1`:

```routeros
/certificate add name=spicyops-ca-template common-name=SpicyOps-Local-CA key-size=2048 days-valid=3650 key-usage=key-cert-sign,crl-sign
/certificate sign spicyops-ca-template name=spicyops-ca
/certificate set [find name="spicyops-ca"] trusted=yes
/certificate add name=spicyops-api-template common-name=192.168.8.1 subject-alt-name=IP:192.168.8.1 key-size=2048 days-valid=365 key-usage=digital-signature,key-encipherment,tls-server
/certificate sign spicyops-api-template ca=spicyops-ca name=spicyops-api
/certificate set [find name="spicyops-api"] trusted=yes
```

Ejecuta una línea a la vez y espera a que finalicen las firmas. Generar claves carga temporalmente la CPU; no necesita reinicio. Cambia tanto `common-name` como `subject-alt-name` si tu router tiene otra IP.

La CA del ejemplo dura 3650 días y el servidor 365 días. Registra vencimiento y responsable de renovación; una CA confiable dentro de MikroTik todavía debe trasladarse y verificarse en Raspberry.

Fuente: [certificados de MikroTik](https://help.mikrotik.com/docs/spaces/ROS/pages/2555969/Certificates).

## 5. Crear usuario API con escritura

**Dónde: MikroTik.** Para una instalación nueva se utiliza un grupo dedicado. `spicyops-agent` es un usuario del router, no una cuenta Linux.

```routeros
/user group add name=spicyops-control policy=read,write,api
/user add name=spicyops-agent group=spicyops-control address=192.168.8.90/32 disabled=yes comment="SpicyOps - API desde Raspberry"
```

**Reemplaza el marcador antes de ejecutar.** Guarda una contraseña nueva y única. Para evitar escapes de caracteres en la terminal puedes usar una clave aleatoria de al menos 24 caracteres alfanuméricos; también puedes establecerla desde los campos de contraseña de **WinBox → System → Users**, sin escribirla en el historial de comandos.

```routeros
/user set [find name="spicyops-agent"] password="REEMPLAZA_POR_UNA_CLAVE_NUEVA"
/user enable [find name="spicyops-agent"]
/user group print detail without-paging where name="spicyops-control"
/user print detail without-paging where name="spicyops-agent"
```

Habilita la cuenta solo si la asignación de contraseña terminó sin errores. Si el usuario/grupo ya existe, no dupliques ni cambies su contraseña por repetir esta guía: utiliza [Localidad existente](#localidad-existente).

Resultado requerido: usuario habilitado, grupo con `read,write,api` positivos y origen de cuenta `192.168.8.90/32`. Las otras políticas deben estar negadas o no concedidas. `read` permite consultar, `write` modificar configuración y `api` iniciar sesión por API, incluida API-SSL. No hace falta `full`, `policy`, `sensitive` o SSH del MikroTik para el conector actual.

**El permiso `write` es amplio en RouterOS**, no se limita por cliente o por lista. SpicyOps restringe sus operaciones a agregar/habilitar/deshabilitar entradas individuales IPv4 en la lista fija `Morosos`, con confirmación del operador. El administrador conserva la responsabilidad sobre la cuenta.

Fuente: [usuarios y políticas de RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User).

## 6. Habilitar API-SSL y restringir el acceso

**Dónde: MikroTik.** Adapta la IP al origen LAN real de Raspberry:

```routeros
/ip service set [find name="api-ssl"] disabled=no port=8729 certificate=spicyops-api tls-version=only-1.2 address=192.168.8.90/32
/ip service disable [find name="api"]
/ip service print detail without-paging where name~"^api"
```

Debe aparecer `api-ssl` habilitada con el certificado, TLS 1.2 y origen permitido; `api` sin TLS debe estar deshabilitada. `certificate=none` no es la configuración final válida para este conector.

La cuenta y el servicio se limitan a la **IP LAN de Raspberry**, porque es ella quien se conecta al router. No pongas aquí la IP Tailscale de Windows. No habilites HTTP/REST, FTP o SSH del MikroTik solo para conectar SpicyOps. No abras ni redirijas 8729 desde Starlink hacia internet.

Fuentes: [API y API-SSL](https://manual.mikrotik.com/docs/developer-guides/api/), [servicios de RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services).

### Complemento: firewall IPv4 de la API

Antes de agregar reglas, inspecciona el filtro actual. Si ya existen reglas equivalentes activas, no las dupliques. Los comentarios siguientes deben ser únicos.

```routeros
/ip firewall filter print detail without-paging
```

Para una preparación controlada, con la administración por WinBox/terminal y la IP de Raspberry confirmada, permitir antes de bloquear:

```routeros
/ip firewall filter add chain=input action=accept protocol=tcp src-address=192.168.8.90/32 dst-port=8728,8729 comment="SpicyOps: permitir API desde Raspberry"
/ip firewall filter move [find comment="SpicyOps: permitir API desde Raspberry"] destination=0
/ip firewall filter add chain=input action=drop protocol=tcp dst-port=8728,8729 comment="SpicyOps: bloquear API otros origenes"
/ip firewall filter move [find comment="SpicyOps: bloquear API otros origenes"] destination=1
/ip firewall filter print detail without-paging where chain=input
```

La regla de permiso debe quedar antes del descarte y de otras reglas que impidan ese acceso. Estos movimientos colocan al principio reglas **solo para los dos puertos API**; revisa su encaje con la política del sitio. Conserva la sesión de administración y comprueba desde Raspberry antes de salir de Safe Mode guardando cambios. No se modifican puertos WinBox/SSH ni se sustituye el firewall completo.

Este complemento filtra IPv4; no acredita una auditoría IPv6 o de todos los servicios del router. API sin TLS permanece deshabilitada aunque el filtro incluya su puerto.

Fuente: [cadenas y reglas de firewall](https://help.mikrotik.com/docs/spaces/ROS/pages/48660574/Filter).

## 7. Exportar la CA pública y copiarla a Raspberry

**Dónde: MikroTik.**

```routeros
/certificate export-certificate spicyops-ca type=pem file-name=spicyops-ca
/file print where name="spicyops-ca.crt"
```

Descarga `spicyops-ca.crt` desde **WinBox → Files**. PEM sin `export-passphrase` exporta aquí el certificado público; no necesitas transferir una clave privada `.key` ni un `.p12` a Raspberry.

**Dónde: PowerShell de Windows.** Los valores se solicitan al ejecutar para usar el usuario y la IP Tailscale reales:

```powershell
$RaspUser = Read-Host 'Usuario SSH de Raspberry'
$RaspHost = Read-Host 'IP o nombre Tailscale de Raspberry'
$CaPath = (Read-Host 'Ruta completa al archivo spicyops-ca.crt descargado').Trim('"')
scp "$CaPath" "${RaspUser}@${RaspHost}:spicyops-ca.crt"
```

Usa el puerto SSH real. Si es diferente de 22, añade `-P PUERTO` a `scp`. Compara la huella SSH si se solicita; la contraseña de esa transferencia es la de Raspberry. No desactives la verificación de identidad para evitar un aviso.

**Dónde: Raspberry.**

```bash
openssl x509 -in "$HOME/spicyops-ca.crt" -noout -subject -issuer -dates
printf 'CA para SpicyOps: %s/spicyops-ca.crt\n' "$HOME"
printf 'Python para SpicyOps: %s/spicyops/.venv/bin/python\n' "$HOME"
```

Conserva estas dos rutas para el formulario. Si reutilizas otro entorno ya instalado, indica la ruta de ese entorno; no lo recrees solo para que coincida con el ejemplo.

Fuente: [exportación de certificados](https://help.mikrotik.com/docs/spaces/ROS/pages/2555969/Certificates).

## 8. Verificar TLS y lectura API

**Dónde: Raspberry.** Sustituye las dos apariciones de la IP si el router utiliza otra:

```bash
timeout 15s openssl s_client -connect 192.168.8.1:8729 -CAfile "$HOME/spicyops-ca.crt" -verify_ip 192.168.8.1 -verify_return_error -tls1_2 -brief </dev/null
```

Debe negociar TLS 1.2 y mostrar `Verification: OK`. La opción `-verify_ip` comprueba identidad, no solo cifrado. Un aviso SNI al utilizar una IP no invalida por sí mismo una ejecución que sí termina con verificación correcta. No uses `CERT_NONE` ni desactives comprobación de nombre para continuar.

Para verificar además contraseña y lecturas, pega este bloque completo. Usa la contraseña **API de MikroTik**, introducida en el prompt oculto:

```bash
"$HOME/spicyops/.venv/bin/python" - <<'PY'
from functools import partial
from getpass import getpass
from pathlib import Path
import ssl
from librouteros import connect

host = "192.168.8.1"
context = ssl.create_default_context(cafile=str(Path.home() / "spicyops-ca.crt"))
api = connect(host=host, port=8729, username="spicyops-agent",
              password=getpass("Clave API de MikroTik: "),
              ssl_wrapper=partial(context.wrap_socket, server_hostname=host), timeout=10)
try:
    identity = list(api.path("system", "identity"))[0]
    resource = list(api.path("system", "resource"))[0]
    queues = list(api.path("queue", "simple"))
    entries = list(api.path("ip", "firewall", "address-list"))
    print("Lectura API autenticada: OK")
    print("Router:", identity["name"])
    print("RouterOS:", resource["version"])
    print("Colas simples:", len(queues))
    print("Entradas Morosos:", sum(e.get("list") == "Morosos" for e in entries))
finally:
    api.close()
PY
```

Esta comprobación no modifica clientes. Los permisos de escritura se verifican en el grupo del paso 5; no es necesario suspender un cliente para terminar la preparación. Una lectura correcta tampoco acredita que una suspensión corte internet: eso depende de la política del siguiente apartado.

Fuentes: [OpenSSL s_client](https://docs.openssl.org/3.0/man1/openssl-s_client/), [conexión librouteros](https://librouteros.readthedocs.io/en/latest/connect.html).

## 9. Requisito para suspender y reactivar: política Morosos

SpicyOps agrega o habilita una **IPv4 individual** en `Morosos` al suspender; deshabilita su entrada individual al reactivar. No instala reglas de bloqueo. No cambia planes ni velocidades en la versión actual. Conectar y sincronizar siguen siendo lecturas aunque la cuenta tenga escritura.

**Dónde: MikroTik.** Revisa antes de habilitar control operativo:

```routeros
/queue simple print detail without-paging
/ip firewall address-list print detail without-paging where list="Morosos"
/ip firewall filter print detail without-paging
```

Los servicios deben tener colas individuales con IPv4 inequívoca. No agregues rangos compartidos de infraestructura a Morosos para preparar el sistema. El programa rechaza casos ambiguos, duplicados o restricciones compartidas/dinámicas que impidan un cambio individual seguro.

### Si ya tienes una política de corte

Consérvala y comprueba su orden. Una entrada en la lista solo tiene efecto si las reglas usan `src-address-list=Morosos` en el recorrido del tráfico. La inspección de la lista acredita estado de configuración, no un corte físico por sí sola.

### Ejemplo mínimo para una red nueva sin política de corte

Solo aplica al tráfico **IPv4 que atraviesa ese MikroTik hacia una interfaz de salida concreta**. Cambia `WAN` por su nombre real. No lo agregues si ya hay una política equivalente; no es un reemplazo universal para redes con otros gateways o FastTrack.

Se crea deshabilitado para poder revisar las entradas activas antes de ponerlo en servicio:

```routeros
/ip firewall filter add chain=forward action=drop src-address-list=Morosos out-interface=WAN disabled=yes comment="SpicyOps: corte IPv4 Morosos"
/ip firewall filter move [find comment="SpicyOps: corte IPv4 Morosos"] destination=0
```

Después de revisar que las IP activas de Morosos son las que realmente se desea restringir, el administrador habilita la política:

```routeros
/ip firewall filter enable [find comment="SpicyOps: corte IPv4 Morosos"]
```

**Habilitarla afecta a las IP que ya estén activas en la lista.** El ejemplo bloquea salida IPv4 a internet y conserva acceso local; no implementa aislamiento de capa 2, portal cautivo o bloqueo IPv6.

FastTrack puede omitir el filtrado y las colas, incluso si se reordenan reglas; las sesiones existentes necesitan consideración específica. Adapta su tratamiento al diseño del sitio antes de dar por probado el corte. No vacíes globalmente connection tracking ni deshabilites aceleración de todos los clientes como parte de esta guía. Si el abonado dispone de IPv6 o un camino alterno, se necesita una política adicional diseñada para ello.

El portal cautivo es opcional y no es requisito de SpicyOps. No se incluyen redirecciones DNS/HTTP ni pruebas sobre un abonado real durante esta preparación. El control operativo se realiza desde el programa, confirmando localidad, cliente e IP.

Fuentes: [firewall](https://help.mikrotik.com/docs/spaces/ROS/pages/48660574/Filter), [FastTrack y conexiones](https://help.mikrotik.com/docs/spaces/ROS/pages/130220087/Connection%2Btracking).

## Datos que debes capturar en SpicyOps

Abre **Conexiones → Nueva localidad**:

| Campo | Valor |
|---|---|
| Nombre de localidad | Nombre identificable de esa red |
| Dirección de Raspberry | IP/nombre Tailscale de esa Raspberry, o IP LAN si estás local |
| Puerto SSH | Normalmente `22` |
| Usuario Raspberry | Resultado de `whoami`, por ejemplo `operador` |
| Autenticación SSH | Contraseña o clave SSH de Windows |
| Contraseña o frase de clave | Secreto correspondiente a esa autenticación SSH |
| IP MikroTik | Ejemplo `192.168.8.1`, comprobada desde esa Raspberry |
| Usuario API MikroTik | `spicyops-agent` u otro usuario dedicado preparado |
| Contraseña API MikroTik | Contraseña elegida en el router, distinta del acceso SSH |
| Python con librouteros | Ejemplo `/home/operador/spicyops/.venv/bin/python` |
| Certificado CA | Ejemplo `/home/operador/spicyops-ca.crt` |

Las rutas de Python y CA pertenecen a **Raspberry**. Si utilizas un archivo de clave privada SSH, su ruta pertenece a **Windows**. No pongas la ruta de Windows del `.crt` en el campo CA remoto.

Aunque la aplicación permite descubrir la IP del router a partir del gateway si el campo está vacío, para la preparación es preferible escribir la IP confirmada y cubierta por el certificado.

Pulsa **Comprobar y conectar**, compara la huella SSH y confirma solo si coincide. El programa leerá las colas e importará los servicios individuales válidos. No crea usuarios manuales ni instala software en Raspberry. Usa **Diagnosticar** si falla una etapa.

Para aplicar una suspensión/reactivación, selecciona un servicio válido en **Clientes** y confirma la acción. La credencial debe conservar `read,write,api`; el programa lee de nuevo el estado resultante. No hace falta escribir comandos en la web ni habilitar permisos de administrador completos.

Referencia de la implementación: [README del proyecto](README.md).

## Localidad existente

Si SSH, CA, Python y API-SSL ya funcionan, no repitas instalación ni emisión de certificados. Comprueba el usuario y su grupo:

```routeros
/user print detail without-paging where name="spicyops-agent"
```

En la preparación histórica el grupo se llamó `spicyops-read`. Para **ese grupo existente**, habilitar escritura y comprobar:

```routeros
/user group set [find name="spicyops-read"] policy=read,write,api
/user group print detail without-paging where name="spicyops-read"
```

Si tu cuenta utiliza `spicyops-control` u otro grupo, utiliza su nombre real. Cambiar un grupo afecta a todos sus usuarios; si es compartido con otras herramientas, prepara uno dedicado en lugar de alterar el compartido.

Debe aparecer `write` positivo. No es necesario cambiar la contraseña ni habilitar API 8728. La receta anterior documenta cómo habilitarlo, no confirma el estado actual de un equipo sin consultar su salida.

Para volver a lectura, retirando escritura explícitamente:

```routeros
/user group set [find name="spicyops-read"] policy=read,api,!write
/user group print detail without-paging where name="spicyops-read"
```

La consulta debe mostrar `!write`. En ese modo la lectura del programa seguirá disponible, pero suspender/reactivar no podrá escribir.

Si se conserva el entorno de diagnóstico anterior, la ruta de Python puede ser `/home/USUARIO/spicyops-prueba/.venv/bin/python` y la CA `/home/USUARIO/spicyops-ca.crt`; utiliza los archivos realmente presentes, no recrees todo para seguir el ejemplo nuevo.

## Comprobación final y solución de fallos

| Resultado | Qué comprobar |
|---|---|
| SSH de Windows a Raspberry no conecta | Tailscale, dirección, TCP/22, política de la tailnet, firewall y servicio ssh |
| Huella SSH distinta | Verificar identidad por una vía confiable; no aceptarla automáticamente |
| `No module named librouteros` | Que el formulario use el Python del entorno donde se instaló |
| CA no encontrada | Ruta remota real y permiso de lectura del usuario SSH |
| Certificado inválido/expirado o IP no coincide | Fecha de ambos equipos, vigencia, CA y SAN del certificado |
| API rechaza conexión | Servicio api-ssl, puerto 8729, origen LAN de Raspberry y firewall input |
| Falla usuario/contraseña API | Cuenta MikroTik habilitada, contraseña correcta y política api |
| Lee clientes pero no puede escribir | Grupo con read,write,api positivos, origen de cuenta y restricciones de la operación |
| Cambió Morosos pero el cliente sigue navegando | Reglas forward, FastTrack, sesiones, IPv6 y caminos alternos; no confundir configuración con efecto real |
| Faltan clientes en el panel | Colas individuales, destinos válidos y sección Revisar colas excluidas |

Preparación lista cuando: SSH identifica la Raspberry correcta, el Python remoto importa librouteros, API-SSL valida CA/IP, la lectura devuelve el router esperado, la cuenta está habilitada con escritura y existe una política de Morosos adecuada al sitio. La prueba física de suspensión requiere un servicio controlado y observación desde ese abonado; no se acredita por preparar esta guía.

Esta documentación no modifica los equipos, no renueva certificados automáticamente y no publica la aplicación. Conserva contraseñas, claves privadas, respaldos y exportaciones fuera del contenido público de la página.
