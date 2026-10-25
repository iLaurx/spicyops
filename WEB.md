# WEB.md — Encargo unificado: guía web de conexión de SpicyOps

Revisión: 24 de octubre de 2026.
Referencia visual: [Aprende Arduino](https://learn-arduino-red.vercel.app/es/). Es una inspiración de composición y estilo, no un recurso para copiar.


## 0. Encargo, fuentes y decisiones de la fusión

**Entregar una web estática educativa completa, con diseño e instrucciones, preparada para Vercel y GitHub Pages.** Este archivo integra DESING.md y CONNECTION.md y es la especificación de trabajo del siguiente agente. Los originales se conservan intactos como antecedentes. No hace falta alternar entre dos recetas para construir el sitio.

Alcance de este encargo: implementar y verificar el sitio en una carpeta nueva `web/`, preparar build, documentación y archivos de despliegue. No migrar el programa Windows a Vercel ni reemplazar el portal Django. No publicar, crear repositorios remotos o modificar servicios/red por el mero hecho de preparar el sitio; el usuario está pidiendo un encargo para otro agente.

Las instrucciones históricas de AGENTS.md sobre un MVP simulado/PostgreSQL no corresponden a esta web. Conservar sus límites de datos y red. El producto Windows y el lector remoto se mantienen independientes del sitio educativo.

| Diferencia entre las fuentes | Decisión para esta web |
| --- | --- |
| Diseño orientado a lectura y CONNECTION con escritura | Ofrecer dos recorridos explícitos: consultar y consultar/controlar. Incluir de forma completa read,write,api y su retirada; conectar no exige escritura. |
| Ejemplos de IP y nombres distintos | Utilizar un solo escenario ficticio 192.168.88.0/24, usuario API spicyops-agent y rutas coherentes de la tabla del apartado 5. |
| Subnet router presente en CONNECTION | Anexo opcional para administración directa; no es requisito de SpicyOps. |
| Grupos spicyops-agent/read/control mezclados | Usuario único del ejemplo spicyops-agent; grupos dedicados por modo, sin cambiar cuentas compartidas. |
| CA de 1825 o 3650 días | Para ejemplo nuevo, CA 1825 días y servidor 365. No renovar ni reemplazar certificados existentes por uniformar números. |
| Instalar pip global o usar el del entorno | Usar python3-venv y pip del entorno; python3-pip global no es necesario para esta receta. |
| Mover reglas API al principio por defecto | Prevalece revisión de reglas y excepción limitada antes del descarte pertinente; no mover todo a posiciones fijas. |
| Regla genérica de Morosos en CONNECTION | Explicar el requisito y permitir plantilla deshabilitada solo para topología revisada. No prometer corte universal con FastTrack/IPv6. |
| Publicación sin proveedor decidido | Vercel + repositorio GitHub como primera opción; GitHub Pages como alternativa estática. Preparar ambos sin desplegar aún. |

La web enseña al administrador a preparar los equipos; no recibe contraseñas ni accede a los dispositivos. Los comandos son contenido educativo, no instrucciones que el agente de desarrollo deba ejecutar contra una red.

## 1. Objetivo del agente

Construir una **web educativa e interactiva en español** que enseñe a preparar Raspberry Pi, Tailscale, MikroTik y SpicyOps para Windows, desde la instalación inicial hasta una lectura correcta, incluyendo el recorrido administrativo de escritura por Morosos cuando el operador lo elija.

Este documento fusiona diseño y conexión: se construye una web de instrucciones; no se rediseña el programa Windows. Entregar contenido completo, comandos, diagramas, verificaciones y solución de errores. No limitarse a una landing promocional o una maqueta.

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

El diseño fuente documentó un viewport compacto de 530 × 716 y consulta de CSS; no acreditó una captura de escritorio. No atribuir esta revisión histórica al agente actual. Si existen capturas en `docs/design-reference/`, son consulta y no recursos para publicar; no depender de ellas para compilar el sitio.

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
| Usuario API | `spicyops-agent` |
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


## 12. Paso 7 — Usuario API, modo elegido y servicio cifrado

Mostrar al visitante dos opciones visibles: **Consultar datos** y **Consultar y controlar clientes**. Deben explicar qué permiso conceden. El recorrido de control cumple el objetivo de CONNECTION.md: queda documentado cómo dejar escritura habilitada, sin hacer al visitante descubrirlo en otro archivo.

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

No ejecutar ambos bloques sobre la misma cuenta. Si nombre/grupo ya existe, utilizar el recorrido existente del apartado 17 y revisar antes de editar. El grupo predeterminado read no es equivalente al grupo mínimo propio: incluye permisos adicionales.

### Contraseña y activación

La cuenta se crea deshabilitada para no dejar acceso sin contraseña. Ruta principal: **WinBox → System → Users → spicyops-agent**, establecer una contraseña única en Password/Confirm Password y habilitar tras guardarla. No cambiar otras cuentas. La página nunca pide ni genera esa contraseña.

Como referencia para quien prefiera terminal, mostrar esta plantilla **con Copiar deshabilitado permanentemente mientras contenga el marcador**. Se edita solo fuera del sitio, respetando escapes RouterOS:

```routeros
/user set [find where name="spicyops-agent"] password="<CLAVE_UNICA_LOCAL>"
/user enable [find where name="spicyops-agent"]
```

No habilitar si falló la asignación. El sitio no debe ofrecer un campo para resolver ese marcador. No usar contraseñas de demostración ni incluir secretos en historial de la web.

Comprobar usuario y el grupo del modo elegido:

```routeros
/user print detail where name="spicyops-agent"
/user group print detail where name="spicyops-control"
```

En modo consulta, sustituir el grupo por spicyops-read. Deben estar positivos read y api; para control también write. Otras políticas no deben concederse por comodidad. No dar full, sensitive, policy, reboot o SSH al MikroTik para esta integración.

El origen es la IP LAN que el router ve para Raspberry, no la IP Tailscale de Windows. Revisar NAT intermedio si existe. Write es una capacidad amplia de RouterOS: no limita por sí mismo las operaciones a Morosos ni a un abonado. El programa aplica su propio contrato de acciones permitidas.

### Asignar certificado y habilitar API-SSL

Tras preparar el certificado y revisar consumidores existentes:

```routeros
/ip service set [find where name="api-ssl"] disabled=no port=8729 certificate=spicyops-api address=192.168.88.90/32 tls-version=only-1.2
/ip service print detail where name="api-ssl"
```

`address=` reemplaza la lista de orígenes del servicio. En un servicio compartido conservar los otros orígenes autorizados según su política; no imponer el ejemplo sobre una instalación con consumidores adicionales. Reemplazar certificado/puerto también puede afectarles.

En preparación nueva o tras confirmar que no existen dependencias de API sin TLS, cerrar 8728:

```routeros
/ip service disable [find where name="api"]
/ip service print detail where name~"^api"
```

API-SSL debe estar habilitada sin X/I, con certificado, TLS 1.2 y orígenes correctos. API sin TLS debe quedar deshabilitada; no tocar WinBox/SSH u otros servicios como efecto lateral. No abrir ni redirigir puertos desde Starlink/internet.

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

La receta descargable se ejecuta desde una terminal interactiva. Debe abortar si no hay terminal disponible para pedir la clave sin mostrarla; no aceptar su ingreso en la web. No mostrar inventario ni guardar secretos.

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
| Usuario API del MikroTik | `spicyops-agent` |
| Contraseña API del MikroTik | Solo en SpicyOps |
| Certificado CA en Raspberry | `/home/operador/spicyops-certs/spicyops-ca.crt` |
| Python con librouteros en Raspberry | `/home/operador/spicyops-venv/bin/python` |

Las rutas CA/Python son de Raspberry; la clave privada SSH es de Windows. Completar el campo CA no transfiere archivos.

Comparar y confirmar huella SSH desde fuente confiable. Conectar y revisar resultado. Diagnosticar separa acceso, identidad SSH, autenticación, lector, TLS y API; no actualiza Clientes/Analytics ni modifica la red.

Sincronizar y revisar colas individuales en Clientes y fecha en Analytics. Las diferencias observadas necesitan intervalos válidos. Las aproximaciones por uptime no son consumo mensual medido.

La actualización automática es opcional y empieza desactivada. Requiere SpicyOps ejecutándose en Windows; una PC apagada no lee. No describirla como servicio instalado en Raspberry.

## 17. Control de Morosos y localidad ya preparada

No es requisito para leer. Sí es parte del contenido completo solicitado para administrar: incluir sus permisos, verificaciones y límites. No convertir este capítulo en investigación o reparación del portal cautivo.

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

La web debe enseñar un esquema input vs forward, explicar FastTrack/IPv6/sesiones existentes y que estado de lista no acredita corte físico. No incluir un botón Probar corte ni un cliente real preseleccionado.

Como material avanzado, si se muestra una plantilla de regla nueva, debe estar **deshabilitada**, con Copiar bloqueado hasta que el administrador resuelva interfaz e ID de posición. No es una receta universal:

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
5. Revisar recetas contra fuentes oficiales para versiones elegidas y conservar enlaces/fecha. La publicación del sitio no acredita que esos comandos se hayan probado físicamente.
6. Comprobar sintaxis Python, copia, búsqueda, enlaces, anclas, impresión y progreso.
7. Verificar 360, 430, 768, 1024 y 1440 px, zoom 200%, teclado, movimiento reducido y contraste normal mínimo 4.5:1.
8. Comprobar que no se envían datos del configurador ni existen ejecución remota o captura de secretos.
9. Conservar archivos ajenos. En este repositorio respetar AGENTS.md; no leer `config-mikro/` o `config-antenasyclientes/`.
10. Entregar fuentes, arranque/build reales, capturas escritorio/móvil, verificaciones y preparación de despliegue de los apartados 22–24. Este encargo no publica por sí mismo ni cambia visibilidad de repositorios.

El visitante debe poder instalar Tailscale en ambos extremos, entrar por SSH, preparar Python, configurar CA/certificado/cuenta/API-SSL, entender el firewall, transferir CA pública, verificar TLS y llenar los campos reales de SpicyOps. Debe distinguir lectura básica y control de Morosos con escritura explícita; ambos recorridos deben estar completos.

**Estado de esta especificación:** contrastada con documentación oficial y código del formulario/conector. No se instalaron paquetes ni se ejecutaron cambios en Raspberry, Tailscale o MikroTik durante su redacción. Las recetas no acreditan pruebas físicas de conexión, firewall o compatibilidad de cada equipo. El agente debe conservar esa distinción al entregar.

## 21. Anexos procedentes de CONNECTION.md

### A. Acceso directo opcional a la LAN mediante Tailscale

Separar este anexo del recorrido principal, dentro de “Administración avanzada”. El uso de SpicyOps no requiere forwarding ni anunciar subredes: Windows conecta a Raspberry, no directamente a la IP LAN del MikroTik.

Si el administrador necesita además WinBox o acceso directo a antenas desde Windows, explicar el subnet router. Para una Raspberry y rango ficticio de esta guía:

```bash
printf 'net.ipv4.ip_forward = 1\nnet.ipv6.conf.all.forwarding = 1\n' | sudo tee /etc/sysctl.d/99-spicyops-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-spicyops-tailscale.conf
sudo tailscale set --advertise-routes=192.168.88.0/24
```

Es una configuración adicional que modifica forwarding. Revisar firewall del dispositivo, autorizar rutas y acceso en la consola Tailscale. `--advertise-routes` establece la lista anunciada: conservar las rutas previas necesarias en el valor completo. No reemplazarla ciegamente. No habilitar exit node, Funnel ni rutas predeterminadas para este objetivo.

El comando de las imágenes `tailscale up --advertise-routes=...` combina inicio y anuncio en una instalación nueva. Para una Raspberry autenticada, la guía usa `tailscale set` para esa preferencia. Si ya funciona el acceso de mantenimiento, no repetir la preparación ni resetear Tailscale.

Windows suele recoger las rutas aprobadas. Las LAN idénticas de distintas localidades hacen ambiguo el acceso directo por IP; tratarlas mediante diseño específico. Los perfiles de SpicyOps continúan apuntando a cada Raspberry y no necesitan cambiar de subred o de tailnet al seleccionar localidad.

Fuente: [subnet routers de Tailscale](https://tailscale.com/docs/features/subnet-routers).

### B. Exportar configuración y respaldar antes de cambiar

Este apartado explica la extracción local solicitada en CONNECTION.md. No añadir campos para subir configuraciones, respaldos o salidas del router al sitio.

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

No capturar la contraseña en el sitio. Guardar el backup fuera del router, en almacenamiento privado. La guía no restaura backups ni importa exports para configurar otro router. No confundir respaldo binario con inventario saneado o con un instalador.

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

## 22. Implementación estática y organización

### Tecnología elegida

Recomendación de implementación: **Vite + TypeScript + HTML semántico + CSS propio**, sin backend. Diagramas en SVG original y comportamiento local ligero para índice, búsqueda, progreso y configurador. No hace falta React, Next.js, WebGL, base de datos ni funciones serverless para este alcance.

Todo el contenido de las etapas debe estar disponible en el HTML generado: mantener lectura e impresión utilizables sin depender de una conexión a una API. JavaScript mejora copia, filtros y navegación; no simula comprobaciones de dispositivos.

Vite produce una distribución estática apropiada para Vercel y GitHub Pages. Elegir una versión soportada y Node LTS compatible con esa versión y el proveedor; fijar versiones reales en lockfile y documentar el runtime elegido. No imponer al usuario instalaciones en Raspberry para desarrollar la web.

### Carpeta de trabajo propuesta

Crear una carpeta nueva, sin tocar el programa Windows:

```text
web/
  README.md
  package.json
  package-lock.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    main.ts
    styles.css
    content/
    components/
    illustrations/
  public/
    fonts/
    downloads/
  tests/
```

La estructura es propuesta, no archivos ya implementados. El agente puede ajustar componentes si conserva las responsabilidades. Solo incluir archivos públicos revisados en public; no copiar allí el repositorio raíz, AGENTS.md, datos del programa, perfiles cifrados, respaldos ni carpetas sensibles.

Los originales DESING.md y CONNECTION.md se conservan. El contenido público se extrae selectivamente de este encargo a un modelo estructurado de etapas; no publicar los documentos internos completos de forma automática. No empaquetar las capturas de referencia como arte propio.

### Navegación y contenido

Una guía con anclas estables evita necesitar reescrituras de SPA para cada etapa. Usar enlaces del tipo `#mikrotik-api`, `#raspberry-python` y `#modo-escritura`. Visitar/recargar una ancla debe mostrar la sección correcta. Progreso y búsqueda no deben cambiar el significado de un enlace compartido.

Incluir entrada **Ya tengo la localidad preparada**: resumen de campos y comprobaciones, enlace directo a activar/retirar write y acceso a Diagnosticar de SpicyOps explicado mediante instrucciones. No obligar a repetir todos los comandos.

Recursos descargables: guía del visitante saneada y script de comprobación de lectura. Generar el script a partir de la misma fuente que muestra la web para evitar diferencias. La descarga no lo ejecuta. No ofrecer un instalador SpicyOps ni un enlace de release inexistente; si el propietario aporta un destino verificable, incorporarlo después.

## 23. Comportamiento del configurador y de los comandos

### Modelo mínimo de cada etapa

Cada etapa y bloque de comando debe tener, de forma estructurada:

- Identificador/ancla, título, equipo de destino y terminal.
- Tipo de acción: consulta, instalación o cambio de configuración; privilegios requeridos.
- Prerrequisitos, texto del comando y variables permitidas.
- Resultado esperado, errores vinculados y límites de lo que verifica.
- Marcadores pendientes, condición que permite copiar y fuente técnica.
- Modo al que corresponde: consulta, control, ambos o anexo opcional.

Mostrar de forma visible **Raspberry · Bash**, **Windows · PowerShell** o **MikroTik · RouterOS** junto a cada bloque. Copiar devuelve únicamente texto ejecutable, nunca prompts como `[admin@...] >`, números de línea ni escapes añadidos por Markdown.

### Datos configurables sin secretos

Se pueden ajustar IP de router, IP LAN Raspberry, IP/nombre Tailscale, puerto SSH, usuario Linux/API y rutas. No se solicita contraseña, auth key, clave privada, token, backup o salida de consola. El nombre visible de localidad no se interpola como código.

Validar IPv4 de router/Raspberry con cuatro octetos válidos. El campo router no acepta URL, IPv6, CIDR o nombre DNS porque el producto actual exige IPv4. La dirección de Raspberry puede ser IP/nombre válido accesible desde Windows, sin comandos ni esquema de URL. Puerto SSH entero 1–65535. Los nombres y rutas tienen longitud acotada y gramática segura para el contexto de shell; rechazar controles, saltos de línea y metacaracteres en lugar de concatenarlos.

Una ruta de ejemplo simple puede limitarse a caracteres alfanuméricos, `/`, `.`, `_` y `-`, ser absoluta, y rechazar segmentos de traversal. Si se decide admitir espacios u otros caracteres, implementar escape correcto específico para cada terminal y comprobarlo. No usar una función genérica de escape para Bash, PowerShell, RouterOS y Python.

No enviar valores a servidor, analítica, parámetros de URL, logs o servicios externos. No persistir datos del configurador por defecto. Si se guarda progreso, solo IDs de etapas y versión del esquema en almacenamiento local, con botón para borrarlo. Una casilla completada significa “el visitante lo declaró”, no “la web probó conexión”.

### Copia y plantillas

Copiar solo tras una acción del visitante. Mostrar confirmación inline y breve con aria-live. Si falla Clipboard API, ofrecer selección manual del texto, sin alertas modales. Los bloques con marcadores pendientes deben tener Copiar deshabilitado y explicación del dato faltante.

Los marcadores de contraseña **no se resuelven en la web**: sus plantillas siguen sin copia directa. Ofrecer la vía WinBox y edición local; el sitio nunca termina generando comandos con credenciales del visitante. Para IDs de firewall, el administrador obtiene el destino real o usa GUI: no inventarlo desde una posición fija.

Escapar HTML al renderizar código y variables. Probar entradas con comillas, `$()`, backticks, punto y coma y saltos de línea para comprobar rechazo o escape seguro, sin ejecutar lo que contienen. No usar eval, terminal emulada o ejecución remota.

## 24. Despliegue: Vercel o GitHub Pages

### Decisión recomendada

**Primera opción: repositorio GitHub del sitio + Vercel.** GitHub almacena el código y Vercel lo construye/publica. Son complementarios, no dos formatos incompatibles. La web necesita únicamente archivos estáticos.

**Alternativa: GitHub Pages con GitHub Actions.** También sirve para esta guía y permite publicar el resultado del build sin servidor propio. El agente debe dejar preparada y documentada la alternativa, sin desplegar a dos destinos por defecto.

| Aspecto | Vercel | GitHub Pages |
| --- | --- | --- |
| Fuente | Repositorio GitHub autorizado | Repositorio GitHub con Pages disponible |
| Carpeta de proyecto | `web` si se conserva este monorepo | Build con working-directory web |
| Instalación | `npm ci` | `npm ci` |
| Build | `npm run build` | `npm run build` con base del sitio |
| Artefacto publicado | `dist` relativo a web | Solo `web/dist` |
| Base usual | `/` | `/<REPO_WEB>/` en sitio de proyecto; `/` en dominio/raíz correspondiente |
| Servidor Python/Raspberry | No se despliega | No se despliega |

### Preparación para Vercel

En la implementación, documentar importación del repositorio desde Vercel, Root Directory `web`, preset Vite, instalación `npm ci`, build `npm run build` y salida `dist`. Si se extrae el sitio a un repositorio independiente, la raíz de ese repositorio sustituye a web.

No agregar funciones, variables con secretos ni conexiones SSH al proveedor. La estructura propuesta usa anclas en una página y no necesita un rewrite global que oculte errores 404 de recursos.

El agente debe dejar archivos de configuración solo si son necesarios y comprobar el build real. Con la integración conectada, nuevos commits pueden generar despliegues: configurar qué rama se publica y distinguir previews de producción cuando se autorice conectar el sitio.

Repositorio privado y sitio público son decisiones diferentes. Verificar plan, propietario y acceso de integración antes de prometer compatibilidad: Vercel Hobby no despliega un repositorio privado perteneciente a una organización de GitHub. No solucionar eso haciendo público el repositorio completo de SpicyOps automáticamente.

Fuentes: [Vite en Vercel](https://vercel.com/docs/frameworks/frontend/vite), [integración Git](https://vercel.com/docs/git), [GitHub en Vercel](https://vercel.com/docs/git/vercel-for-github).

### Preparación para GitHub Pages

Pages aloja archivos estáticos. En GitHub Free está disponible para repositorios públicos; la disponibilidad desde privados depende del plan. Si se elige publicar el código de la guía, es preferible un repositorio separado con solo el sitio saneado, no cambiar visibilidad del proyecto de escritorio y sus documentos privados.

El agente preparará un workflow limitado al sitio, preferentemente `workflow_dispatch` como punto de inicio para el despliegue futuro. No activarlo/publicarlo durante esta redacción. Cuando se decida publicación continua se puede añadir el evento push y filtros de rutas adecuados.

El workflow debe instalar Node compatible, ejecutar npm ci y build desde web, usar Pages como fuente GitHub Actions, subir **solo web/dist** y desplegar con el mecanismo oficial. Permisos mínimos de publicación: contents read, pages write e id-token write. Usar versiones soportadas de las Actions oficiales verificadas al implementar y documentarlas; no copiar versiones obsoletas de otro proyecto.

La configuración de Vite debe admitir una base de compilación explícita, por ejemplo `SITE_BASE`. Para Vercel usar `/`; para `https://USUARIO.github.io/REPO_WEB/`, usar `/REPO_WEB/`. El agente implementará ese parámetro y probará assets, fuentes, enlaces y descargas bajo ambas bases. No asumir el nombre real del repositorio ni dejar el marcador en un workflow activado.

Fuentes: [qué es GitHub Pages y disponibilidad](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [workflows de Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [Vite: despliegue estático y base](https://vite.dev/guide/static-deploy).

### Privacidad del artefacto

Solo se publica el build del sitio. `.gitignore` no basta si un archivo privado ya estuviera versionado: inspeccionar los archivos elegidos para publicar y el contenido final de dist. No leer carpetas sensibles para este propósito; excluirlas por diseño y no copiarlas.

No incluir IP/nombres de abonados reales, credenciales, claves de estado, `.spicybackup`, `.backup`, `.rsc`, `.cfg`, datos de sesiones ni ejecutables del programa en el sitio. Los ejemplos deben seguir siendo ficticios. No añadir analítica que capture IP introducidas o texto copiado. Las fuentes/tipografías locales deben incluir licencia y no realizar solicitudes a terceros al leer la guía.

### Qué significa desplegado

Build local correcto significa **listo para desplegar**, no publicado. Preparar workflow/configuración tampoco crea una web pública. Si en una tarea posterior se autoriza publicar, verificar la URL resultante, HTTPS, assets, enlaces/anclas, descargas y una vista móvil antes de declarar el despliegue terminado. Registrar proveedor, rama, URL y revisión realmente publicada.

## 25. Criterios de aceptación consolidados

El siguiente agente debe trabajar hasta entregar fuentes y sitio local verificable. No basta otra planificación. Su entrega debe incluir:

1. Diseño de cuaderno técnico consistente con la paleta, fuentes, estructura y SVG originales de esta especificación. No una landing vacía.
2. Etapas 1–11 completas, recorridos consulta/control, localidad ya preparada, errores, glosario y anexos opcionales. Ningún comando exige exponer una contraseña en la web.
3. Escenario único coherente: direcciones, usuario API, rutas y SAN coinciden en tabla, comandos, descargables y formulario explicado.
4. Copia correcta por equipo/terminal, bloqueo de marcadores y pruebas de inyección/escape del configurador. No ejecución remota ni solicitud de secretos.
5. Búsqueda local, anclas, progreso declarado, borrado local, impresión completa, teclado y movimiento reducido funcionando.
6. Verificación visual real a 360, 430, 768, 1024 y 1440 px, zoom 200% y contraste. Registrar capturas propias del sitio, no la referencia como si fuera implementación.
7. Comprobar cada bloque Python descargable con análisis de sintaxis y comprobar que solo consulte. Probar lógica del sitio sin conectar Raspberry/MikroTik reales; distinguir esos límites en el reporte.
8. Instalar dependencias y ejecutar build real. Scripts de dev/build/preview/typecheck y tests del sitio existentes y documentados con sus resultados. No usar comandos del programa Windows como pruebas de esta web.
9. Build probado tanto en base `/` como en una subruta de proyecto ficticia. Fuentes, diagramas y descargas deben resolver en ambos casos. Sin errores de consola ni desbordamiento de toda la página en móvil.
10. Configuración Vercel y preparación GitHub Pages revisadas; README del sitio con instrucciones reales de arranque/build/publicación y limitaciones de plan/visibilidad. Mantener publicable únicamente el artefacto del sitio.
11. Revisar dist y solicitudes del navegador: sin datos privados, formularios secretos, scripts que contacten routers, telemetría o recursos remotos no acordados.
12. Final breve: archivos principales, pruebas efectivamente ejecutadas, cómo previsualizar el resultado y qué falta para publicar. No pedir al usuario que repita el laboratorio de red para terminar el desarrollo web.

## 26. Mensaje listo para iniciar el siguiente trabajo

> Construye la guía web de SpicyOps siguiendo WEB.md como encargo completo. Implementa el proyecto estático separado en web/, con diseño de cuaderno técnico, etapas completas, comandos por terminal, recorridos de consulta y escritura, búsqueda, diagramas y verificaciones. Conserva intacto el programa Windows y los dos Markdown originales. Prueba el sitio y los builds para Vercel y GitHub Pages con datos ficticios. Prepara los archivos de publicación, sin desplegar ni acceder a equipos reales. Trabaja de forma autónoma y entrega un sitio revisable, no otro plan.



## Ajuste de experiencia · 25 de octubre de 2026

Por petición del usuario, la guía implementada en `web/` prioriza conectar rápidamente. Para una localidad preparada, mostrar tres pasos sin comandos obligatorios: reunir accesos, completar perfil y comprobar/conectar desde SpicyOps verificando la huella. La preparación nueva permanece disponible en desplegables con un botón para abrir su recorrido completo. No imponer reinstalaciones ni certificados nuevos en redes funcionales.

La comprobación manual API es opcional; Diagnosticar en SpicyOps es la ruta principal. Se elimina la segunda receta TLS equivalente en Python. Mostrar solo la creación de cuenta del modo seleccionado y mantener escritura, retirada de permisos, diagnóstico y administración avanzada fuera de la ruta rápida. Conservar certificados y huella verificados. Los comandos son instrucciones para el administrador; esta simplificación no autoriza ejecutarlos en equipos reales.
