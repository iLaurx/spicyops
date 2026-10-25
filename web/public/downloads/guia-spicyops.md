# Conecta tu red con SpicyOps

Revisión: 25 de octubre de 2026. Ejemplos ficticios.

## Conectar en 3 pasos

Para una localidad que ya tiene SSH, Python con librouteros, CA y API-SSL preparados. **No repitas la instalación: puedes conectar sin ejecutar comandos.**

1. **Ten los accesos a mano.** Dirección y usuario SSH de Raspberry, usuario API del MikroTik, contraseñas o clave autorizada, IP del router y rutas de Python y CA en Raspberry. Si entras desde fuera, conecta Windows a tu Tailscale habitual. En LAN no hace falta VPN.
2. **Abre SpicyOps → Conexiones → Nueva localidad.** Completa los campos del [resumen del perfil](#completar-spicyops). Las contraseñas se introducen en el programa, nunca aquí.
3. **Pulsa Comprobar y conectar.** Compara la huella SSH con la del administrador y confirma si coincide. Si aparece un error, usa Diagnosticar y abre únicamente el apartado que corresponda.

**¿Quieres suspender o reactivar clientes?** Además necesitas una cuenta con `read,write,api` y una política Morosos ya revisada. Si solo falta ese permiso, ve a [activar escritura sin reinstalar](#modo-escritura). Conectar no prueba una suspensión.

**¿Es una red nueva?** Abre la preparación desde cero. Instala únicamente lo que falte. No necesitas anunciar subredes, habilitar forwarding, instalar un agente permanente ni configurar un portal para conectar SpicyOps.

## Antes de empezar

Requerir Raspberry Pi OS compatible, alimentación estable, internet/DNS y acceso inicial local o SSH LAN; usuario existente, sin asumir `pi`; acceso administrativo autorizado a MikroTik; conectividad LAN entre ambos; hora correcta en los tres equipos e IP LAN estable de Raspberry, preferiblemente reserva DHCP preparada por el administrador.

Registrar SO, arquitectura y RouterOS. ARMv6 no equivale a ARMv7/ARM64. La guía no reinstala el SO, crea abonados ni modifica planes. SpicyOps importa colas simples IPv4 individuales existentes.

Escenario completamente ficticio:

| Dato | Valor |
| --- | --- |
| Localidad | Localidad de ejemplo |
| MikroTik LAN | `192.168.88.1` |
| Raspberry LAN | `192.168.88.90` |
| Raspberry Tailscale | `100.70.10.1` |
| Windows Tailscale | `100.70.10.2` |
| Usuario Linux | `operador` |
| Usuario API | `spicyops-agent` |
| Python | `/home/operador/spicyops-venv/bin/python` |
| CA | `/home/operador/spicyops-certs/spicyops-ca.crt` |

La IP LAN de Raspberry no es su IP Tailscale: MikroTik normalmente ve la primera como origen de la API. Son ejemplos; esta guía no detecta tus equipos.

## 1. Instalar Tailscale en Raspberry

**Raspberry · Bash.** Consultar primero:

```bash
cat /etc/os-release
uname -m
python3 --version
date -Is
ip -br address
ip route
```

Identifica distribución, arquitectura, IP y ruta en la salida. Python se prepara en el paso 4 si falta. No reinstalar el sistema ni borrar la microSD.

Para Raspberry Pi OS compatible con el instalador oficial:

```bash
sudo apt-get update
sudo apt-get install -y curl ca-certificates
curl -fsSL https://tailscale.com/install.sh -o /tmp/spicyops-tailscale-install.sh
less /tmp/spicyops-tailscale-install.sh
```

Pulsa `q` para salir de `less`. Tras descargar y revisar, instala:

```bash
sh /tmp/spicyops-tailscale-install.sh
sudo systemctl enable --now tailscaled
sudo tailscale up
```

El instalador puede pedir privilegios. Abrir en navegador la URL de autenticación que devuelve y registrar el dispositivo en la tailnet autorizada. No pegar esa URL en chats ni almacenarla en la web.

Verificar:

```bash
tailscale version
tailscale ip -4
tailscale status
systemctl is-active tailscaled
```

Resultado: servicio activo, autenticación completada e IP Tailscale asignada. Si requiere aprobación del dispositivo, completarla en la consola administrativa.

Si el instalador no soporta SO/arquitectura, detener la receta y dirigir al selector oficial. No descargar binarios ARM al azar ni prometer cualquier Raspberry antigua. No usar `--ssh`, `--advertise-routes` o `--advertise-exit-node`.

Fuentes: [Linux](https://tailscale.com/docs/install/linux), [paquetes estables](https://pkgs.tailscale.com/stable/).

## 2. Tailscale en Windows y permisos

Instalar desde el sitio oficial, iniciar sesión y comprobar que Windows y Raspberry pertenecen a la misma tailnet o tienen acceso compartido autorizado. Estar en la misma tailnet no garantiza permiso TCP 22.

**Windows · PowerShell:**

```powershell
tailscale status
tailscale ping 100.70.10.1
Test-NetConnection 100.70.10.1 -Port 22
```

Si no encuentra `tailscale`, reabrir terminal o usar la ruta instalada, normalmente:

```powershell
& "$env:ProgramFiles\Tailscale\tailscale.exe" status
```

El ping VPN no sustituye SSH. TCP 22 puede fallar todavía porque OpenSSH no esté habilitado hasta el paso siguiente.

Para tailnets restrictivas, este **fragmento de grant** se integra por el administrador en la política existente:

```json
{
  "src": ["100.70.10.2"],
  "dst": ["100.70.10.1"],
  "ip": ["tcp:22"]
}
```

No es una política completa. No reemplazar toda la política ni dar acceso global. Los permisos son acumulativos: este fragmento no revoca otras reglas más amplias.

Usar OpenSSH normal; no habilitar Tailscale SSH. Si ya está habilitado en Raspberry, el administrador debe revisar esa configuración antes de continuar. Revísala desde una sesión administrativa confiable.

Fuentes: [Windows](https://tailscale.com/docs/install/windows), [grants](https://tailscale.com/docs/reference/syntax/grants), [ejemplos](https://tailscale.com/docs/reference/examples/grants). Consulta las condiciones vigentes del proveedor.

## 3. OpenSSH y huella de Raspberry

**Raspberry · Bash**, desde consola inicial o acceso LAN existente:

```bash
sudo apt-get install -y openssh-server
sudo systemctl enable --now ssh
systemctl is-active ssh
sudo sshd -t
ss -ltn 'sport = :22'
```

La cuenta de SpicyOps no necesita sudo para ejecutar el lector; necesita sesión SSH y lectura de su entorno/CA. Conservar la autenticación acordada por el administrador. No habilitar root o contraseñas globalmente como arreglo genérico.

Si existe firewall local, permitir únicamente el acceso necesario desde la PC autorizada por `tailscale0` al puerto SSH. No activar, vaciar o reemplazar UFW/nftables como receta universal. Política Tailscale y firewall Linux son controles distintos.

Desde consola confiable, obtener huellas:

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
sudo ssh-keygen -lf /etc/ssh/ssh_host_ecdsa_key.pub -E sha256
sudo ssh-keygen -lf /etc/ssh/ssh_host_rsa_key.pub -E sha256
```

Un archivo puede no existir. Comparar con la huella del **mismo tipo de clave**; OpenSSH y Paramiko pueden negociar tipos distintos. No aceptar huellas sin verificar ni borrar `known_hosts` ante un cambio.

**Windows · PowerShell:**

```powershell
ssh -p 22 operador@100.70.10.1
```

Si faltan `ssh`/`scp`, instala la característica opcional **Cliente OpenSSH** de Windows. SpicyOps incluye su cliente: esta característica es solo para pruebas/transferencias manuales.

Ruta básica: contraseña de cuenta existente si ya está permitida. Alternativa: clave privada Windows previamente autorizada en `authorized_keys`, sin sobrescribir claves anteriores. Enlazar el procedimiento oficial de preparación. No exigir contraseña en un equipo que funciona solo con claves.

Fuente: [acceso remoto de Raspberry Pi](https://www.raspberrypi.com/documentation/computers/remote-access.html).

## 4. Python y librouteros

**Raspberry · Bash.** Entorno virtual, sin `--break-system-packages`:

```bash
sudo apt-get install -y python3 python3-venv openssl
python3 --version
python3 -m venv "$HOME/spicyops-venv"
"$HOME/spicyops-venv/bin/python" -m pip install "librouteros==4.2.2"
"$HOME/spicyops-venv/bin/python" -m pip check
"$HOME/spicyops-venv/bin/python" -c "import ssl, librouteros; from importlib.metadata import version; print(version('librouteros')); print(ssl.OPENSSL_VERSION)"
printf '%s\n' "$HOME/spicyops-venv/bin/python"
```

Guardar la ruta absoluta del ejecutable dentro del venv. No resolver el enlace simbólico y poner el Python del sistema: perdería la biblioteca del entorno.

Python 3.11 es la base contemplada por el lector. Si falta, revisar compatibilidad antes de seguir; no actualizar remotamente el SO sin un plan. librouteros 4.2.2 es una base explícita, no una promesa de validación de todos los routers/arquitecturas.

`python3` también debe estar en el PATH de la sesión SSH: el conector lo utiliza para iniciar el intérprete elegido. No hace falta activar el venv en cada sesión, instalar Django en Raspberry ni crear servicio SpicyOps.

Si ya existe entorno funcional, verificarlo y reutilizar su ruta. Registrar versiones reales; disponibilidad de paquetes no acredita prueba física ARMv6.

Fuentes: [librouteros 4.2.2](https://pypi.org/project/librouteros/4.2.2/), [conexión](https://librouteros.readthedocs.io/en/latest/connect.html). Conserva la verificación TLS, incluso si otros ejemplos de la biblioteca la desactivan.

## 5. Inspeccionar MikroTik

**MikroTik · WinBox → New Terminal o consola administrativa confiable.** No pegar RouterOS en PowerShell o Bash.

```routeros
/system resource print
/system clock print
/ip address print
/ip service print detail where name=api-ssl
/certificate print detail
/user group print
/ip firewall filter print detail where chain=input
/ip firewall raw print
/queue simple print count-only
```

Consultar localmente, sin pedir subir las salidas. Registrar estado previo de servicio, certificado y reglas. Guardar respaldo privado mediante los procedimientos administrativos existentes y tener vía de recuperación antes de cambios remotos.

Elige según el estado de tu localidad:

1. **API-SSL y CA ya preparadas:** verificar IP/SAN, vigencia y acceso; reutilizar y saltar creación.
2. **Preparación nueva:** seguir los pasos de certificados, usuario y servicio.
3. **Servicio compartido:** revisar consumidores antes de reemplazar certificado, puerto u orígenes.

La sintaxis tradicional se usa habitualmente en RouterOS 6/7; esta guía no acredita compatibilidad física universal ni una versión probada del equipo. Si un equipo antiguo rechaza propiedades o TLS, documentar el bloqueo sin degradar a API sin cifrar.

## 6. Crear CA y certificado de servidor

**Modifica MikroTik; solo preparación nueva.** Comprobar que los nombres no existan. Ejecutar por bloques y esperar que termine cada firma.

Crear CA:

```routeros
/certificate add name=spicyops-ca-template common-name=SpicyOps-Local-CA key-size=2048 days-valid=1825 key-usage=key-cert-sign,crl-sign
/certificate sign spicyops-ca-template name=spicyops-ca
/certificate set [find where name="spicyops-ca"] trusted=yes
```

Crear certificado para la IP **real** del MikroTik:

```routeros
/certificate add name=spicyops-api-template common-name=SpicyOps-API subject-alt-name=IP:192.168.88.1 key-size=2048 days-valid=365 key-usage=digital-signature,key-encipherment,tls-server
/certificate sign spicyops-api-template ca=spicyops-ca name=spicyops-api
/certificate print detail where name=spicyops-api
```

Comprobar firma, clave privada del servidor, vigencia y SAN. Common-name no sustituye SAN de IP. Cambiar la IP utilizada por el programa puede requerir otro certificado válido.

Exportar **solo la CA pública**:

```routeros
/certificate export-certificate spicyops-ca type=pem file-name=spicyops-ca
/file print where name~"spicyops-ca"
```

No añadir `export-passphrase` ni exportar claves privadas. Descargar `spicyops-ca.crt` de Files de WinBox por sesión confiable. La clave privada de CA y la del servidor permanecen bajo control del administrador del router.

No confiar en archivos de origen no verificado. Registrar emisor, huella y vencimiento; incluir recordatorio de renovación.

Fuentes: [certificados/SAN](https://manual.mikrotik.com/docs/authentication-authorization-accounting/certificates/), [exportación PEM](https://help.mikrotik.com/docs/spaces/ROS/pages/2555969/Certificates).

## 7. Usuario API, modo elegido y servicio cifrado

Elige **Consultar datos** (read,api) o **Consultar y controlar clientes** (read,write,api). El control exige permisos de escritura y una política Morosos revisada.

### Solo consulta

Crear grupo nuevo dedicado:

```routeros
/user group add name=spicyops-read policy=read,api
/user add name=spicyops-agent group=spicyops-read address=192.168.88.90/32 disabled=yes comment="SpicyOps API desde Raspberry"
```

### Consulta y control de Morosos

Para una instalación nueva, en lugar del bloque anterior:

```routeros
/user group add name=spicyops-control policy=read,write,api
/user add name=spicyops-agent group=spicyops-control address=192.168.88.90/32 disabled=yes comment="SpicyOps API desde Raspberry"
```

Ejecuta solamente el bloque de tu modo sobre la cuenta dedicada. Si nombre/grupo ya existe, utilizar el recorrido de [escritura sin reinstalar](#modo-escritura) y revisar antes de editar. El grupo predeterminado read no es equivalente al grupo mínimo propio: incluye permisos adicionales.

### Contraseña y activación

La cuenta se crea deshabilitada para no dejar acceso sin contraseña. Ruta principal: **WinBox → System → Users → spicyops-agent**, establecer una contraseña única en Password/Confirm Password y habilitar tras guardarla. No cambiar otras cuentas. La página nunca pide ni genera esa contraseña.

Esta plantilla se edita únicamente fuera del sitio, respetando escapes RouterOS. Copiar permanece deshabilitado por contener una contraseña pendiente:

```routeros
/user set [find where name="spicyops-agent"] password="<CLAVE_UNICA_LOCAL>"
/user enable [find where name="spicyops-agent"]
```

No habilitar si falló la asignación. Resuelve ese marcador únicamente en tu equipo, nunca en esta guía. Utiliza una contraseña única y mantenla fuera de esta web.

Comprobar usuario y el grupo del modo elegido:

```routeros
/user print detail where name="spicyops-agent"
/user group print detail where name~"^spicyops-(read|control)$"
```

Revisar el grupo asignado a la cuenta. Deben estar positivos read y api; para control también write. Otras políticas no deben concederse por comodidad. No dar full, sensitive, policy, reboot o SSH al MikroTik para esta integración.

El origen es la IP LAN que el router ve para Raspberry, no la IP Tailscale de Windows. Revisar NAT intermedio si existe. Write es una capacidad amplia de RouterOS: no limita por sí mismo las operaciones a Morosos ni a un abonado. El programa aplica su propio contrato de acciones permitidas.

### Asignar certificado y habilitar API-SSL

Tras preparar el certificado y revisar consumidores existentes:

```routeros
/ip service set [find where name="api-ssl"] disabled=no port=8729 certificate=spicyops-api address=192.168.88.90/32 tls-version=only-1.2
```

`address=` reemplaza la lista de orígenes del servicio. En un servicio compartido conservar los otros orígenes autorizados según su política; no imponer el ejemplo sobre una instalación con consumidores adicionales. Reemplazar certificado/puerto también puede afectarles.

En preparación nueva o tras confirmar que no existen dependencias de API sin TLS, cerrar 8728:

```routeros
/ip service disable [find where name="api"]
/ip service print detail where name~"^api"
```

API-SSL debe estar habilitada sin X/I, con certificado, TLS 1.2 y orígenes correctos. API sin TLS debe quedar deshabilitada; no tocar WinBox/SSH u otros servicios como efecto lateral. No abrir ni redirigir puertos desde Starlink/internet.

Fuentes: [usuarios/políticas](https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User), [servicios](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services), [API](https://manual.mikrotik.com/docs/developer-guides/api/).

## 8. Firewall

La restricción del servicio no sustituye al firewall. El destino es el propio router: corresponde a **input**, no forward.

Si la política actual bloquea el flujo, añadir una aceptación limitada a Raspberry LAN y TCP 8729 **antes del descarte pertinente**. Plantilla:

```routeros
/ip firewall filter add chain=input action=accept protocol=tcp src-address=192.168.88.90/32 dst-address=192.168.88.1 dst-port=8729 place-before=<ID_REGLA_INPUT_QUE_BLOQUEA> comment="SpicyOps API-SSL desde Raspberry"
```

El administrador obtiene el ID de la configuración vigente; el configurador no lo adivina. Alternativa: crear en IP → Firewall → Filter Rules y ubicar antes del descarte adecuado. Si la política ya permite ese flujo, no añadir una regla por costumbre.

No vaciar reglas, cambiar políticas globales, insertar indiscriminadamente en posición cero, permitir cualquier origen, crear NAT hacia internet o alterar FastTrack. Revisar raw si descarta antes del filtro. No presentar esta excepción como auditoría del firewall completo.

```routeros
/ip firewall filter print stats where comment="SpicyOps API-SSL desde Raspberry"
```

Ese contador no acredita login API. La conexión TLS se comprueba desde Raspberry en el paso siguiente.

Fuente: [seguridad del router y orden de reglas](https://manual.mikrotik.com/docs/getting-started/securing-your-router/).

## 9. Transferir CA y validar TLS

**Raspberry · Bash:**

```bash
mkdir -p "$HOME/spicyops-certs"
```

**Windows · PowerShell**, desde la carpeta donde se descargó la CA por WinBox:

```powershell
Get-FileHash -Algorithm SHA256 .\spicyops-ca.crt
scp -P 22 .\spicyops-ca.crt operador@100.70.10.1:/home/operador/spicyops-certs/spicyops-ca.crt
```

**Raspberry · Bash:**

```bash
sha256sum "$HOME/spicyops-certs/spicyops-ca.crt"
openssl x509 -in "$HOME/spicyops-certs/spicyops-ca.crt" -noout -subject -issuer -dates -fingerprint -sha256
ip route get 192.168.88.1
openssl s_client -connect 192.168.88.1:8729 -CAfile "$HOME/spicyops-certs/spicyops-ca.crt" -verify_ip 192.168.88.1 -verify_return_error < /dev/null
```

Comparar hashes en ambos equipos: verifica la copia, no sustituye la confianza del canal de obtención de CA. Revisar la dirección de origen LAN de la ruta.

Resultado esperado: cadena válida e IP verificada, normalmente `Verify return code: 0 (ok)`. Aún no se ha probado login API. Si falla, corregir CA, SAN, vigencia, reloj, certificado asignado o acceso de red.

Esta comprobación manual es opcional: si SpicyOps ya conecta y lee, no necesitas repetir TLS por terminal. El lector valida la CA y la identidad del router.

Fuente: [SSL de Python](https://docs.python.org/3.11/library/ssl.html). Mantener el criterio del lector: nunca `CERT_NONE`, desactivar `check_hostname` o ignorar el certificado.

## Diagnóstico API manual · opcional

La comprobación preferente es **Diagnosticar en SpicyOps**, tras completar el perfil del perfil. Como opción avanzada, descarga el script desde Recursos y guárdalo **localmente en Raspberry** como `~/spicyops-check-api.py`.

La receta descargable exige una terminal interactiva para pedir la clave sin mostrarla. No muestra inventario ni guarda secretos.

```python
from functools import partial
from getpass import getpass
from pathlib import Path
import ssl
import sys
from librouteros import connect

if not sys.stdin.isatty():
    raise SystemExit("Ejecuta este archivo desde una terminal interactiva.")

ip = "192.168.88.1"
ctx = ssl.create_default_context(
    cafile=str(Path.home() / "spicyops-certs" / "spicyops-ca.crt")
)
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
api = connect(
    host=ip,
    port=8729,
    username="spicyops-agent",
    password=getpass("Contraseña API (no se muestra): "),
    ssl_wrapper=partial(ctx.wrap_socket, server_hostname=ip),
    timeout=8,
)
try:
    for path, properties in [
        ("/system/identity/print", "name"),
        ("/system/resource/print", "uptime,version,board-name"),
        ("/queue/simple/print", ".id,name,target,bytes"),
        ("/ip/firewall/address-list/print", ".id,list,address,disabled"),
    ]:
        count = sum(1 for _ in api(path, **{".proplist": properties}))
        print(path, "OK; registros:", count)
finally:
    api.close()
```

Ejecutar desde terminal interactiva de Raspberry:

```bash
"$HOME/spicyops-venv/bin/python" "$HOME/spicyops-check-api.py"
```

Solo consulta e imprime cantidades. La última ruta cuenta todas las entradas de address-list, no únicamente Morosos. No confundirlo con cantidad de clientes suspendidos.

Cero colas o Morosos vacío puede ser válido. No crear colas/clientes de prueba en producción para llenar pantallas. Una revisión de código no acredita prueba física.

## Completar el perfil en SpicyOps

Extraer el paquete Windows completo, conservando `_internal` junto a `SpicyOps.exe`. Abrir **Conexiones → Nueva localidad**.

| Campo real | Qué introducir |
| --- | --- |
| Nombre de la localidad | Nombre elegido por el operador |
| Dirección de la Raspberry | `100.70.10.1` o nombre Tailscale autorizado |
| Puerto SSH | `22`, salvo configuración distinta |
| Usuario de Raspberry | `operador` o cuenta existente |
| Autenticación SSH | Contraseña o Clave SSH de Windows |
| Contraseña o frase de clave | Solo en SpicyOps |
| Archivo de clave privada en Windows | Ruta local si se usa; no la clave de host de Raspberry |
| IP del MikroTik | `192.168.88.1`; explícita para evitar otra puerta de enlace |
| Usuario API del MikroTik | `spicyops-agent` |
| Contraseña API del MikroTik | Solo en SpicyOps |
| Certificado CA en Raspberry | `/home/operador/spicyops-certs/spicyops-ca.crt` |
| Python con librouteros en Raspberry | `/home/operador/spicyops-venv/bin/python` |

Las rutas CA/Python son de Raspberry; la clave privada SSH es de Windows. Completar el campo CA no transfiere archivos.

Comparar y confirmar huella SSH desde fuente confiable. Conectar y revisar resultado. Diagnosticar separa acceso, identidad SSH, autenticación, lector, TLS y API; no actualiza Clientes/Analytics ni modifica la red.

Sincronizar y revisar colas individuales en Clientes y fecha en Analytics. Las diferencias observadas necesitan intervalos válidos. Las aproximaciones por uptime no son consumo mensual medido.

La actualización automática es opcional y empieza desactivada. Requiere SpicyOps ejecutándose en Windows; una PC apagada no lee. No describirla como servicio instalado en Raspberry.

## Control de Morosos y localidad ya preparada

La escritura no es requisito para leer. Actívala únicamente para el control de Morosos con permisos y política revisados.

### Activar escritura sin repetir la instalación

Primero consultar la cuenta y su grupo actual:

```routeros
/user print detail where name="spicyops-agent"
```

Si la cuenta dedicada ya utiliza el grupo spicyops-read de la preparación anterior:

```routeros
/user group set [find where name="spicyops-read"] policy=read,write,api
/user group print detail where name="spicyops-read"
```

Si utiliza spicyops-control, consultar/modificar ese grupo real. No aplicar a un grupo compartido con otros usuarios sin revisar su alcance; preparar uno dedicado si corresponde. El nombre de un grupo no determina sus permisos: comprobar write positivo.

Para retirar escritura en el grupo histórico:

```routeros
/user group set [find where name="spicyops-read"] policy=read,api,!write
/user group print detail where name="spicyops-read"
```

Comprobar !write, no dar por completada la retirada solo porque el comando no reportó error. No repetir emisión de CA, cambiar contraseñas o instalar otro Python si ya están preparados.

### Política que debe existir en el router

```routeros
/ip firewall address-list print detail where list="Morosos"
/ip firewall filter print detail where chain=forward
```

Las reglas deben usar la lista exacta Morosos y controlar el recorrido real del abonado. SpicyOps no las instala. Write permite operaciones mucho más amplias que el programa: la aplicación solo agrega/habilita/deshabilita una entrada IPv4 individual validada y exige confirmación de cliente, IP y localidad. No cambia planes ni corta por fecha. Si la escritura o su confirmación son inciertas, sincronizar antes de reintentar.

Input controla el tráfico dirigido al propio router (API-SSL); forward controla el tráfico que atraviesa el router (abonados). FastTrack, IPv6 y sesiones existentes requieren revisión independiente: el estado de la lista no acredita corte físico.

Plantilla avanzada **deshabilitada**: requiere resolver interfaz e ID de posición fuera de la web. No es una receta universal:

```routeros
/ip firewall filter add chain=forward action=drop src-address-list=Morosos out-interface=<INTERFAZ_WAN_REAL> disabled=yes place-before=<ID_REGLA_FORWARD_A_REVISAR> comment="SpicyOps politica Morosos pendiente de revision"
```

Alternativa GUI: crear regla deshabilitada en IP → Firewall → Filter Rules y ubicarla según la política revisada. La activación se hace en una ventana operativa, comprobando previamente qué IP ya están activas en Morosos. No dar un comando genérico que habilite la regla y afecte a abonados por copiar toda la página.

No modificar FastTrack globalmente, vaciar connection tracking o inventar reglas IPv6 para una topología desconocida. Si hay esos caminos, explicar que falta su tratamiento antes de acreditar suspensión efectiva. No instalar portal ni redirecciones como condición del control.

### Verificaciones y significado del resultado

- Grupo/cuenta habilitados acreditan configuración de permisos; no una escritura efectuada.
- Diagnosticar y sincronizar acreditan solo las lecturas implementadas.
- Estado posterior de Morosos acredita configuración leída; no garantiza ausencia de internet por todos los caminos.
- La prueba física de corte/reactivación requiere un destino controlado y observación desde el abonado, en otro procedimiento. El sitio educativo no la ejecuta.

Fuentes: [usuarios](https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User), [firewall](https://help.mikrotik.com/docs/spaces/ROS/pages/48660574/Filter), [FastTrack](https://help.mikrotik.com/docs/spaces/ROS/pages/130220087/Connection%2Btracking).

## Solución de errores

| Síntoma | Revisar | Evitar |
| --- | --- | --- |
| Tailscale no instala | SO, arquitectura y paquetes oficiales | Binarios ARM al azar |
| Raspberry no aparece | Login, aprobación, tailscaled | Abrir SSH en WAN |
| VPN responde, TCP 22 no | Grant, OpenSSH, puerto, firewall Linux | Confundir ping con SSH |
| Autenticación SSH falla | Cuenta Linux o clave autorizada | Usar contraseña API |
| Huella cambió | Identidad por canal confiable | Aceptar/borrar automáticamente |
| Python no inicia | python3 en PATH y ruta del venv | Python Windows |
| Falta librouteros | Importar con el ejecutable configurado | Instalar en otro entorno |
| CA no encontrada | Archivo legible y ruta Raspberry | Ruta Windows |
| API timeout/refused | IP LAN, 8729, origen y firewall | API sin TLS |
| CA no confiable | Cadena y CA correctas | Desactivar validación |
| IP mismatch | SAN IP igual al destino | Cambiar solo common-name |
| Certificado vencido | Vigencia y relojes | Ignorar el error |
| Login API rechazado | Usuario, clave, grupo y origen | Permisos full |
| Conecta, cero clientes | Colas individuales y exclusiones | Inventar clientes |
| Sin gráfica histórica | Lecturas válidas, intervalos y resets | Inventar continuidad |
| Morosos rechaza | Cuenta de lectura o caso ambiguo | Reintentar sin sincronizar |
| Antes funcionaba | IP LAN de Raspberry cambió | Ampliar acceso a toda la red |

Utiliza el índice para volver a la etapa correspondiente. Puedes imprimir la guía completa con el resumen de campos del resumen del perfil.

## Mantenimiento y localidades

Cada Raspberry necesita acceso Tailscale, intérprete/CA y perfil propio. Cada router requiere preparación acorde a su localidad. No anunciar subredes de clientes para esta arquitectura.

Recordar vigencia de certificados, reautenticación Tailscale según política, IP LAN estable y respaldo portable cifrado de SpicyOps. No desactivar expiración ni controles automáticamente. La web no accede a la tailnet ni al estado privado de la aplicación.

## Administración avanzada

### A. Acceso directo opcional a la LAN mediante Tailscale

Anexo opcional de administración avanzada. El uso de SpicyOps no requiere forwarding ni anunciar subredes: Windows conecta a Raspberry, no directamente a la IP LAN del MikroTik.

Si el administrador necesita además WinBox o acceso directo a antenas desde Windows, explicar el subnet router. Para una Raspberry y rango ficticio de esta guía:

```bash
printf 'net.ipv4.ip_forward = 1\nnet.ipv6.conf.all.forwarding = 1\n' | sudo tee /etc/sysctl.d/99-spicyops-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-spicyops-tailscale.conf
sudo tailscale set --advertise-routes=192.168.88.0/24
```

Es una configuración adicional que modifica forwarding. Revisar firewall del dispositivo, autorizar rutas y acceso en la consola Tailscale. `--advertise-routes` establece la lista anunciada: conservar las rutas previas necesarias en el valor completo. No reemplazarla ciegamente. No habilitar exit node, Funnel ni rutas predeterminadas para este objetivo.

`tailscale up --advertise-routes=...` combina inicio y anuncio en una instalación nueva. Para una Raspberry autenticada, la guía usa `tailscale set` para esa preferencia. Si ya funciona el acceso de mantenimiento, no repetir la preparación ni resetear Tailscale.

Windows suele recoger las rutas aprobadas. Las LAN idénticas de distintas localidades hacen ambiguo el acceso directo por IP; tratarlas mediante diseño específico. Los perfiles de SpicyOps continúan apuntando a cada Raspberry y no necesitan cambiar de subred o de tailnet al seleccionar localidad.

Fuente: [subnet routers de Tailscale](https://tailscale.com/docs/features/subnet-routers).

### B. Exportar configuración y respaldar antes de cambiar

Conserva configuraciones, respaldos y salidas del router únicamente en almacenamiento privado.

**MikroTik · Terminal administrativa:**

```routeros
/export file=antes-spicyops
/file print where name~"antes-spicyops"
```

Descargar `.rsc` desde WinBox → Files. La exportación normal oculta campos sensibles reconocidos, pero un secreto escrito literalmente en un script/comentario puede permanecer. Tratar el archivo como privado, revisarlo antes de compartirlo y no incluirlo en los recursos descargables de la web.

Para respaldo binario de recuperación, ruta principal por GUI con contraseña de respaldo elegida localmente; también se puede mostrar esta plantilla con Copiar bloqueado:

```routeros
/system backup save name=antes-spicyops password="<CLAVE_RESPALDO_LOCAL>"
```

Introduce la contraseña solo en WinBox o en tu terminal local. Guardar el backup fuera del router, en almacenamiento privado. La guía no restaura backups ni importa exports para configurar otro router. No confundir respaldo binario con inventario saneado o con un instalador.

Fuentes: [configuración y exports](https://help.mikrotik.com/docs/spaces/ROS/pages/328155/Configuration%2BManagement), [backup](https://help.mikrotik.com/docs/spaces/ROS/pages/40992852/Backup).

### C. Resumen de lo que debe quedar preparado

| Capa | Lectura | Consulta y control |
| --- | --- | --- |
| Windows → Raspberry | Tailscale/LAN, OpenSSH, identidad verificada | Igual |
| Raspberry | python3 en PATH, entorno con librouteros, CA legible | Igual; no necesita un servicio permanente SpicyOps |
| MikroTik | API-SSL 8729, certificado con SAN IPv4 correcto, origen permitido | Igual |
| Cuenta API | read,api | read,write,api, con alcance amplio de write explicado |
| Reglas de clientes | No necesarias para consultar colas | Morosos debe tener política previamente revisada para el sitio |
| Formulario | Accesos y rutas reales, introducidos solo en SpicyOps | Igual; la acción exige confirmación del operador |
| Evidencia | TLS, login y lecturas | Lo anterior más permisos; el efecto físico de una suspensión se verifica aparte |