# DESING.md — Encargo para crear la guía web de conexión de SpicyOps

Revisión: 24 de octubre de 2026.
Referencia visual: https://learn-arduino-red.vercel.app/es/

## 1. Objetivo del agente

Construir una **web educativa e interactiva en español** que enseñe a preparar Raspberry Pi, Tailscale, MikroTik y SpicyOps para Windows, desde la instalación inicial hasta una lectura correcta.

Este documento sustituye el encargo anterior: ahora se construye una web de instrucciones; no se rediseña el programa Windows. Entregar contenido completo, comandos, diagramas, verificaciones y solución de errores. No limitarse a una landing promocional o una maqueta.

Los comandos son material educativo para el administrador. No autorizan al agente a conectar equipos reales, instalar software en ellos, modificar routers, leer secretos o publicar la web. Construir y probar el sitio con datos ficticios y conservar los archivos ajenos al encargo.

SpicyOps no instala Tailscale/Python/certificados ni despliega un agente permanente. La preparación inicial se realiza por separado.

## 2. Arquitectura y contrato real del programa

```text
WINDOWS                          RASPBERRY PI                         MIKROTIK
SpicyOps + Tailscale ── SSH ─────> Tailscale + OpenSSH ── API-SSL ────> RouterOS
                       TCP 22     Python + librouteros     TCP 8729    colas simples
                       tailnet                            LAN         TLS validado
```

Windows llega a la IP Tailscale o nombre de Raspberry. El cliente SSH de SpicyOps ejecuta un lector efímero; Raspberry consulta su MikroTik por LAN.

- Utilizar **OpenSSH normal sobre Tailscale**. No habilitar Tailscale SSH en este recorrido.
- No hace falta instalar Tailscale en MikroTik, anunciar subredes, configurar exit nodes/Funnel ni abrir puertos en internet.
- API-SSL no es REST API, WebFig, WinBox ni SSH al MikroTik.
- SpicyOps verifica la huella SSH. El lector verifica CA, vigencia e identidad TLS.
- El puerto API actual está fijado en **8729**; el formulario del MikroTik acepta **IPv4**, no nombre DNS.
- El certificado de servidor necesita **SAN de tipo IP igual a esa IPv4**. Common-name no lo sustituye.
- Python y CA están en Raspberry; la clave privada SSH, si se utiliza, está en Windows.
- Varias localidades pueden repetir IP privadas: cada Raspberry consulta su router y cada perfil conserva su destino.

Contrato contrastado con `portal/forms.py`, `portal/connector.py` y `portal/remote_reader.py`. Al implementar, leer README y encargo vigente; documentos históricos no deben reactivar PostgreSQL, simulador ni alta manual de clientes.

## 3. Diseño visual

### Estilo y arte

Cuaderno técnico interactivo: papel crema, tinta navy, líneas beige, títulos condensados, código monoespaciado y acentos turquesa. Volúmenes isométricos mate con contornos oscuros y sombras de contacto suaves.

Se revisó visualmente el modo compacto de la referencia y se leyeron estilos CSS. El viewport observado fue 530 × 716; la estructura amplia se estudió mediante CSS, sin captura de escritorio. Las capturas están en `docs/design-reference/` si se dispone del repositorio; son consulta, no recursos para publicar.

Valores extraídos de la referencia:

| Uso | Color |
| --- | --- |
| Fondo | `#F6EDDD` |
| Fondo profundo | `#EFE3D1` |
| Navegación | `#E9DCCA` |
| Tarjeta | `#F9F2E5` |
| Código | `#F8F0E3` |
| Borde / divisor | `#CEC0AD` / `#E2D7C7` |
| Títulos / iconos | `#18213D` / `#24304A` |
| Texto / secundario | `#4F535B` / `#696D74` |
| Acento / selección | `#1AA3A1` / `#3F7F8E` |
| Pistas decorativas | `#D3BEA3` |

Fuentes: Barlow para lectura, Barlow Semi Condensed para títulos y JetBrains Mono para código/datos. Distribuir localmente con licencias; fallback Segoe UI/Consolas.

Propuesta para la web: título 32–40 px, sección 22–26 px, cuerpo 16 px, código 13–14 px, ayudas 14 px. Radios de 8 px en controles y 12–14 px en paneles, contorno fino y sombras cálidas leves. Estas medidas son recomendaciones, no mediciones de escritorio de la referencia.

Crear SVG originales de PC, Raspberry, router y cableado. Mantener perspectiva coherente, navy, azul pizarra, crema e indicadores turquesa. Etiquetar “SSH · 22” y “API-SSL · 8729”. No copiar logos/modelos Arduino. No hace falta WebGL.

Reservar cuadrícula y trazas a diagramas, nunca detrás del código o texto. Evitar neón, vidrio, grandes degradados y fondo oscuro predominante. No animar tráfico como si la web comprobara conexiones.

## 4. Estructura e interacción

Escritorio: índice lateral numerado, contenido central y panel auxiliar “Dónde ejecutar / Qué necesitas / Qué debes ver”. Encabezado “Conecta tu red con SpicyOps” y diagrama de tres equipos.

Móvil: una columna, selector de etapa y Anterior/Siguiente. Los bloques de código pueden desplazarse dentro de su contenedor; la página completa no debe desbordar.

Implementar:

- Anclas compartibles, búsqueda local, glosario y versión/fecha de revisión.
- Cada etapa indica equipo, terminal, privilegios, consulta/cambio, instrucciones, resultado esperado y errores.
- Bloques separados: Raspberry · Bash; Windows · PowerShell; MikroTik · RouterOS.
- Copiar sin prompts ni números de línea. Diferenciar consulta, instalación y configuración.
- Casillas “Ya lo comprobé”, con progreso local opcional. Son declaración del usuario, no telemetría real.
- Impresión con todos los pasos, incluso paneles cerrados.
- Teclado, foco visible, contraste y movimiento reducido.
- Sin consola remota, botones Ejecutar ni conexión del sitio a dispositivos.
- Sin formularios de contraseñas, auth keys, claves privadas o respaldos. Sin telemetría que capture comandos, IP o portapapeles.

Puede existir configurador **local** de datos no secretos: IP, nombres y rutas. Validarlos estrictamente según terminal; no interpolar texto arbitrario. No enviarlos ni persistirlos por defecto.

Los bloques con `<MARCADORES>` son plantillas: desactivar Copiar hasta resolverlos. Las contraseñas se introducen solo en terminal local, WinBox o SpicyOps; nunca en la web. No usar contraseñas predeterminadas.

Elegir una implementación estática con contenido versionado y recursos locales. No se necesita backend/base de datos. Crear proyecto separado o carpeta nueva; no sobrescribir el portal Django.

## 5. Prerrequisitos y ejemplo

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
| Usuario API | `spicyops-reader` |
| Python | `/home/operador/spicyops-venv/bin/python` |
| CA | `/home/operador/spicyops-certs/spicyops-ca.crt` |

La IP LAN de Raspberry no es su IP Tailscale: MikroTik normalmente ve la primera como origen de la API. No afirmar que la web detectó estos valores.


## 6. Paso 1 — Instalar Tailscale en Raspberry

**Raspberry · Bash.** Consultar primero:

```bash
cat /etc/os-release
uname -m
python3 --version
date -Is
ip -br address
ip route
```

Explicar cómo identificar distribución, arquitectura, IP y ruta. Python se prepara en el paso 4 si falta. No reinstalar el sistema ni borrar la microSD.

Para Raspberry Pi OS compatible con el instalador oficial:

```bash
sudo apt-get update
sudo apt-get install -y curl ca-certificates
curl -fsSL https://tailscale.com/install.sh -o /tmp/spicyops-tailscale-install.sh
less /tmp/spicyops-tailscale-install.sh
```

Explicar que `q` sale de `less`. Separar descarga/revisión de instalación:

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

## 7. Paso 2 — Tailscale en Windows y permisos

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

Para tailnets restrictivas, mostrar este **fragmento de grant**, que un administrador integra en la política existente:

```json
{
  "src": ["100.70.10.2"],
  "dst": ["100.70.10.1"],
  "ip": ["tcp:22"]
}
```

No es una política completa. No reemplazar toda la política ni dar acceso global. Los permisos son acumulativos: este fragmento no revoca otras reglas más amplias.

Usar OpenSSH normal; no habilitar Tailscale SSH. Si ya está habilitado en Raspberry, el administrador debe revisar esa configuración antes de continuar. La web no debe cambiarla automáticamente.

Fuentes: [Windows](https://tailscale.com/docs/install/windows), [grants](https://tailscale.com/docs/reference/syntax/grants), [ejemplos](https://tailscale.com/docs/reference/examples/grants). No fijar precios o límites de planes.

## 8. Paso 3 — OpenSSH y huella de Raspberry

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

Si faltan `ssh`/`scp`, explicar la característica opcional **Cliente OpenSSH** de Windows. SpicyOps incluye su cliente: esta característica es solo para pruebas/transferencias manuales.

Ruta básica: contraseña de cuenta existente si ya está permitida. Alternativa: clave privada Windows previamente autorizada en `authorized_keys`, sin sobrescribir claves anteriores. Enlazar el procedimiento oficial de preparación. No exigir contraseña en un equipo que funciona solo con claves.

Fuente: [acceso remoto de Raspberry Pi](https://www.raspberrypi.com/documentation/computers/remote-access.html).

## 9. Paso 4 — Python y librouteros

**Raspberry · Bash.** Entorno virtual, sin `--break-system-packages`:

```bash
sudo apt-get install -y python3 python3-venv python3-pip openssl
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

Fuentes: [librouteros 4.2.2](https://pypi.org/project/librouteros/4.2.2/), [conexión](https://librouteros.readthedocs.io/en/latest/connect.html). No copiar los ejemplos de esa biblioteca que desactivan verificación TLS.

## 10. Paso 5 — Inspeccionar MikroTik

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

Rutas que debe ofrecer la web:

1. **API-SSL y CA ya preparadas:** verificar IP/SAN, vigencia y acceso; reutilizar y saltar creación.
2. **Preparación nueva:** seguir los pasos de certificados, usuario y servicio.
3. **Servicio compartido:** revisar consumidores antes de reemplazar certificado, puerto u orígenes.

La sintaxis tradicional se usa habitualmente en RouterOS 6/7; el agente debe declarar las versiones que realmente comprobó. No afirmar compatibilidad física universal. Si un equipo antiguo rechaza propiedades o TLS, documentar el bloqueo sin degradar a API sin cifrar.

## 11. Paso 6 — Crear CA y certificado de servidor

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


## 12. Paso 7 — Usuario de lectura y API-SSL

Crear un grupo propio mínimo. El grupo predeterminado `read` contiene permisos adicionales y no debe reutilizarse como si fuera equivalente:

```routeros
/user group add name=spicyops-read policy=read,api
```

Plantilla **no copiable con marcadores pendientes**, con contraseña única elegida localmente:

```routeros
/user add name=spicyops-reader group=spicyops-read address=192.168.88.90/32 password="<CLAVE_UNICA_LOCAL>"
```

Alternativa obligatoria en la web: crear usuario en WinBox → System → Users, seleccionar grupo, origen y contraseña. La web nunca captura esa clave. Si se edita el comando localmente, respetar el escape de caracteres de RouterOS; WinBox evita errores de interpolación.

El origen es la IP LAN que ve MikroTik para Raspberry; revisar NAT intermedio si existe. No dar `full`, `sensitive`, `policy`, `reboot` ni `write` a la cuenta de consulta.

Tras preparar certificado y revisar consumidores existentes:

```routeros
/ip service set [find where name="api-ssl"] disabled=no port=8729 certificate=spicyops-api address=192.168.88.90/32 tls-version=only-1.2
/ip service print detail where name=api-ssl
```

`address=` **reemplaza** la lista de orígenes del servicio. En un servicio compartido, revisar y conservar los otros orígenes autorizados. No habilitar API 8728 sin TLS ni deshabilitar otros servicios administrativos como efecto lateral.

Fuentes: [usuarios/políticas](https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User), [servicios](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services), [API](https://manual.mikrotik.com/docs/developer-guides/api/).

## 13. Paso 8 — Firewall

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

## 14. Paso 9 — Transferir CA y validar TLS

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

Prueba equivalente con el Python configurado:

```bash
"$HOME/spicyops-venv/bin/python" - <<'PY'
import os
import socket
import ssl

ip = "192.168.88.1"
ctx = ssl.create_default_context(
    cafile=os.path.expanduser("~/spicyops-certs/spicyops-ca.crt")
)
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
with socket.create_connection((ip, 8729), timeout=8) as sock:
    with ctx.wrap_socket(sock, server_hostname=ip) as tls:
        print("TLS e identidad IP verificados:", tls.version())
PY
```

Fuente: [SSL de Python](https://docs.python.org/3.11/library/ssl.html). Mantener el criterio del lector: nunca `CERT_NONE`, desactivar `check_hostname` o ignorar el certificado.

## 15. Paso 10 — Login y lecturas API

La comprobación preferente es **Diagnosticar en SpicyOps**, tras completar el perfil del paso siguiente. Como opción avanzada, ofrecer descarga de este script para guardarlo **localmente en Raspberry** como `~/spicyops-check-api.py`.

No pasarlo por stdin: necesita una terminal interactiva para pedir la contraseña. No mostrar inventario ni guardar secretos.

```python
from functools import partial
from getpass import getpass
from pathlib import Path
import ssl
from librouteros import connect

ip = "192.168.88.1"
ctx = ssl.create_default_context(
    cafile=str(Path.home() / "spicyops-certs" / "spicyops-ca.crt")
)
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
api = connect(
    host=ip,
    port=8729,
    username="spicyops-reader",
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

Cero colas o Morosos vacío puede ser válido. No crear colas/clientes de prueba en producción para llenar pantallas. El agente debe verificar contrato de biblioteca y sintaxis; una revisión de código no acredita prueba física.

## 16. Paso 11 — Completar SpicyOps

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
| Usuario API del MikroTik | `spicyops-reader` |
| Contraseña API del MikroTik | Solo en SpicyOps |
| Certificado CA en Raspberry | `/home/operador/spicyops-certs/spicyops-ca.crt` |
| Python con librouteros en Raspberry | `/home/operador/spicyops-venv/bin/python` |

Las rutas CA/Python son de Raspberry; la clave privada SSH es de Windows. Completar el campo CA no transfiere archivos.

Comparar y confirmar huella SSH desde fuente confiable. Conectar y revisar resultado. Diagnosticar separa acceso, identidad SSH, autenticación, lector, TLS y API; no actualiza Clientes/Analytics ni modifica la red.

Sincronizar y revisar colas individuales en Clientes y fecha en Analytics. Las diferencias observadas necesitan intervalos válidos. Las aproximaciones por uptime no son consumo mensual medido.

La actualización automática es opcional y empieza desactivada. Requiere SpicyOps ejecutándose en Windows; una PC apagada no lee. No describirla como servicio instalado en Raspberry.

## 17. Morosos — Módulo avanzado opcional

No es requisito de conexión. El recorrido principal termina en lectura.

Si el propietario decide permitir suspensión/reactivación, el administrador puede preparar otra cuenta. Plantilla con clave local pendiente:

```routeros
/user group add name=spicyops-control policy=read,write,api
/user add name=spicyops-control group=spicyops-control address=192.168.88.90/32 password="<CLAVE_UNICA_LOCAL>"
```

`write` permite operaciones más amplias en RouterOS que las que usa SpicyOps. El grupo no restringe por sí mismo a la lista Morosos: el programa aplica su límite de acciones. No atribuir aislamiento de permisos por ruta.

Consulta:

```routeros
/ip firewall address-list print count-only where list=Morosos
```

No añadir reglas universales de corte, modificar FastTrack o probar suspensión con clientes. Morosos necesita un firewall previamente preparado/revisado según topología, IPv6 y sesiones existentes.

SpicyOps exige confirmación cliente/IP/localidad, valida inventario y agrega o habilita/deshabilita una entrada IPv4 individual; después vuelve a leer. No cambia planes ni corta por fecha. Un resultado incierto exige sincronizar. Pertenecer a Morosos no acredita corte físico.

## 18. Solución de errores

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

Enlazar cada error a su etapa e incluir resumen imprimible de qué dato pertenece a cada equipo.

## 19. Mantenimiento y localidades

Cada Raspberry necesita acceso Tailscale, intérprete/CA y perfil propio. Cada router requiere preparación acorde a su localidad. No anunciar subredes de clientes para esta arquitectura.

Recordar vigencia de certificados, reautenticación Tailscale según política, IP LAN estable y respaldo portable cifrado de SpicyOps. No desactivar expiración ni controles automáticamente. La web no accede a la tailnet ni al estado privado de la aplicación.

## 20. Implementación y aceptación del agente

1. Crear proyecto separado y contenido estructurado por etapas.
2. Componente de comandos con equipo, lenguaje, copia y marcadores pendientes.
3. Tokens visuales, diagramas originales y composición móvil/escritorio.
4. Recorrido completo en primera entrega, sin capítulos “próximamente”.
5. Revisar recetas contra fuentes oficiales para versiones elegidas y conservar enlaces/fecha.
6. Comprobar sintaxis Python, copia, búsqueda, enlaces, anclas, impresión y progreso.
7. Verificar 360, 430, 768, 1024 y 1440 px, zoom 200%, teclado, movimiento reducido y contraste normal mínimo 4.5:1.
8. Comprobar que no se envían datos del configurador ni existen ejecución remota o captura de secretos.
9. Conservar archivos ajenos. En este repositorio respetar AGENTS.md; no leer `config-mikro/` o `config-antenasyclientes/`.
10. Entregar fuentes, instrucciones reales de arranque/build, capturas escritorio/móvil, verificaciones y pendientes. Publicación requiere autorización aparte.

El visitante debe poder instalar Tailscale en ambos extremos, entrar por SSH, preparar Python, configurar CA/certificado/cuenta/API-SSL, entender el firewall, transferir CA pública, verificar TLS y llenar los campos reales de SpicyOps. Debe distinguir lectura básica de Morosos opcional.

**Estado de esta especificación:** contrastada con documentación oficial y código del formulario/conector. No se instalaron paquetes ni se ejecutaron cambios en Raspberry, Tailscale o MikroTik durante su redacción. Las recetas no acreditan pruebas físicas de conexión, firewall o compatibilidad de cada equipo. El agente debe conservar esa distinción al entregar.

