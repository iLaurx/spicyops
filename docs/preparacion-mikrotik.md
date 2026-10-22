# Preparación de MikroTik para SpicyOps

Guía de incorporación para RouterOS 6 y 7. Inicio: 16/10/2026. Se aplica paso a paso: inspección, cambio acotado y comprobación antes de avanzar. No ejecutar bloques de otra instalación sin adaptar direcciones, permisos y políticas.

## Requisitos de cualquier sitio

| Elemento | Requisito |
|---|---|
| Versión y equipo | Registrar RouterOS, arquitectura y recursos; probar el adaptador en la versión concreta |
| Conectividad local | El agente debe alcanzar la dirección de gestión del router por la LAN |
| Dirección del agente | Dirección estable y confirmada; no inferirla de una ruta Tailscale ni usar la IP de otro sitio |
| Hora | Fecha/hora correctas en router y agente para validar certificados y auditar cambios |
| API-SSL | Servicio habilitado; puerto por defecto TCP 8729; certificado de servidor con clave privada presente |
| Identidad TLS | Certificado vigente con SAN que coincida con IP o nombre usado por el agente; cadena de confianza instalada en el agente |
| Cuenta de integración | Usuario exclusivo, contraseña única almacenada fuera de documentación y permisos explícitos |
| Origen permitido | Servicio y cuenta limitados al agente cuando corresponda; firewall protege administración preservando acceso de mantenimiento |
| SSH | Opcional para mantenimiento; no es requisito del adaptador API. Verificar clave SSH si se utiliza |
| API 8728 | No requerida para la integración cifrada; deshabilitar tras validar API-SSL y revisar dependencias existentes |
| Reglas del abonado | Método de acceso identificado y política de velocidad/suspensión verificada; no copiar Morosos a una red con otra autoridad de acceso |
| Recuperación | Respaldo reciente, estado anterior de cada ajuste y vía de administración comprobada |

Ni REST, RouterOS 7, WWW, FTP ni un puerto público entrante son requisitos de este diseño. Tailscale facilita mantenimiento; el tramo Raspberry–MikroTik sigue requiriendo su propia protección. El panel recibe solicitudes salientes del agente por HTTPS.

## Secuencia y registro del piloto SpicyNet

| Paso | Actividad | Estado documentado |
|---|---|---|
| 0 | Inventariar y habilitar servicios necesarios | Export confirma v6.49.23; usuario compartió SSH 22, API 8728 y API-SSL 8729 habilitados. Certificado API-SSL `none`, ADDRESS vacío |
| 1 | Inspeccionar reloj, certificados, servicios y grupos | Completado por salida compartida: 16/10/2026 17:20:53, Mexico/General UTC−06 sin DST; lista de certificados vacía; grupos read/write/full predeterminados |
| 2 | Preparar certificado y asignarlo a API-SSL | Confirmado por salida del usuario: CA y servidor firmados con clave privada; API-SSL habilitado con spicyops-api y TLS only-1.2 |
| 3 | Preparar confianza TLS en Raspberry | Completado por salida compartida: CA legible, conexión TLSv1.2 a .1:8729, verificación de cadena/IP OK y cierre DONE |
| 4 | Crear grupo y usuario exclusivos de lectura | Confirmado por salida compartida: spicyops-read permite solo read,api; spicyops-agent habilitado y limitado a .90/32. Autenticación comprobada en paso 6 |
| 5 | Limitar orígenes y revisar firewall de administración | Paso 5a confirmado: servicio en .90/32, certificado spicyops-api, TLS only-1.2 y nueva prueba TLS correcta. Paso 5b: reglas activas confirmadas en orden permitir .90 y bloquear otros IPv4; TLS correcto. Prompt compartido sin indicador Safe Mode. Rechazo desde otro origen no probado |
| 6 | Probar lectura autenticada y TLS desde Raspberry | TLS verificado; Python 3.11.2 y entorno aislado listos según confirmación del usuario, sin versión de pip compartida. Instalación y pip check confirmados por usuario. Lectura autenticada OK: Main SN - La Playa, RouterOS 6.49.23 (stable), 15 colas |
| 7 | Deshabilitar API sin TLS si no hay dependencias | Completado por salida: api/8728 deshabilitado (X/I); API-SSL/8729 habilitado con .90/32, spicyops-api y TLS only-1.2 |
| 8 | Preparar pruebas de alta, suspensión/reactivación y velocidad | Canal API listo; usuario seleccionó .62, con estado inicial confirmado y sin observador en el cliente. Escritura del mismo límite confirmada, 2M/4M conservado; el primer retorno conservó write, y la corrección posterior !write ya quedó confirmada por salida. Ensayo cerrado a solicitud del usuario, sin más comandos. Portal secundario/aplazado por usuario; respuesta local documentada |

No marcar un paso como aplicado por haber entregado un comando. Registrar salida o comprobación del usuario, fecha, resultado y pendientes. La habilitación de los servicios procede de una salida compartida; no se probó acceso desde este chat.

## Paso 1: inspección de solo lectura

Ejecutar en la terminal de MikroTik, no en PowerShell ni en la Raspberry:

```routeros
/system clock print
/certificate print detail without-paging
/ip service print detail without-paging
/user group print detail without-paging
```

Estos comandos muestran configuración y metadatos; no crean certificados ni exportan claves privadas o contraseñas. No hace falta compartir contraseñas ni archivos `.key`, `.p12` o backups para esta etapa. Si aparecen dominios o direcciones que se prefiera reservar, se pueden ocultar manteniendo identificables los objetos relevantes.

Comprobar antes del siguiente paso:

- Fecha/hora razonables y coherentes con el sitio; conservar la zona horaria elegida salvo motivo para cambiarla.
- Si hay certificado apto para servidor: nombre, vigencia, SAN, usos, emisor y presencia de clave privada. Revisar la leyenda de banderas de la versión; un certificado público importado sin clave no basta para presentar identidad TLS.
- Estado real de API-SSL, certificado asignado, puerto y orígenes permitidos.
- Si ya existen grupos de integración; no sobrescribir grupos o cuentas usadas por otros sistemas.

Resultado compartido del paso 1: no existen certificados. Se confirma API-SSL habilitado en 8729 con `certificate=none`, `tls-version=any` y `address=""`. API 8728, SSH, FTP y WinBox están habilitados. El reloj muestra fecha/zona coherentes con el sitio; esto no verifica por sí mismo sincronización NTP ni precisión contra una fuente externa. Los grupos read/write/full tienen permisos adicionales: no reutilizar el grupo `read` predeterminado para la cuenta de integración.

## Paso 2: crear y asignar certificado API-SSL

Estado: ejecutado por el usuario y comprobado mediante la salida compartida de certificados y servicio. Se partió de la lista de certificados vacía comprobada. Los comandos se conservan como procedimiento; no volver a ejecutarlos en este router. En otra instalación revisar primero nombres y certificados existentes para evitar duplicados.

En el piloto el agente conectará a `192.168.8.1`. En otra instalación reemplazar la IP en `common-name` y `subject-alt-name`, y usar nombres propios del sitio. Si ya existe una CA administrada por el operador, evaluar esa cadena antes de crear otra. Esta CA local es una elección para el piloto, no un requisito universal de SpicyOps.

Ejecutar línea por línea en MikroTik, esperando a que termine cada firma:

```routeros
/certificate add name=spicyops-ca-template common-name=SpicyOps-Local-CA key-size=2048 days-valid=3650 key-usage=key-cert-sign,crl-sign
/certificate sign spicyops-ca-template name=spicyops-ca
/certificate set [find name="spicyops-ca"] trusted=yes
/certificate add name=spicyops-api-template common-name=192.168.8.1 subject-alt-name=IP:192.168.8.1 key-size=2048 days-valid=365 key-usage=digital-signature,key-encipherment,tls-server
/certificate sign spicyops-api-template ca=spicyops-ca name=spicyops-api
/certificate set [find name="spicyops-api"] trusted=yes
/ip service set [find name="api-ssl"] certificate=spicyops-api tls-version=only-1.2
```

La firma genera claves RSA y puede cargar temporalmente la CPU del router. No requiere reinicio; no se puede asegurar ausencia de impacto de CPU sobre tráfico en este hardware. Esperar el resultado y no repetir una firma mientras siga en curso. Si una línea produce error, detener las siguientes y compartir ese error junto con el estado de certificados.

Comprobar:

```routeros
/certificate print detail without-paging
/ip service print detail without-paging where name="api-ssl"
```

Resultado esperado: CA `spicyops-ca` y certificado `spicyops-api` firmados, con claves privadas presentes y sin marcas de expiración/revocación; certificado servidor con SAN `IP:192.168.8.1`. API-SSL debe mostrar `certificate=spicyops-api` y `tls-version=only-1.2`, sin bandera X/I. Revisar fechas reales de vigencia: servidor previsto para 365 días y CA para 3650; planificar renovación antes del vencimiento.

El paso no crea cuentas, restringe orígenes, modifica firewall ni deshabilita API 8728. La instalación de confianza en Raspberry y prueba de TLS se hacen después; marcar `trusted=yes` dentro del MikroTik no hace que la Raspberry confíe automáticamente en esta CA. No se exportan claves privadas en este paso.

Estado anterior registrado para reversión de la asignación: `certificate=none`, `tls-version=any`. Si es necesario deshacer exclusivamente ese ajuste, usar:

```routeros
/ip service set [find name="api-ssl"] certificate=none tls-version=any
```

Ese comando de reversión no es parte de la secuencia normal y restaura el estado previo sin identidad TLS validable; no usarlo como solución permanente a un error de validación. No eliminar la CA a ciegas: puede afectar certificados emitidos por ella. Antes de borrar certificados comprobar dependencias.

### Resultado comprobado del paso 2

Según la salida compartida por el usuario el 16/10/2026:

- `spicyops-ca`: RSA 2048, SHA-256, autoridad con clave privada y trusted=yes; vigencia del 16/10/2026 17:29:23 al 13/10/2036 17:29:23, según reloj del router.
- `spicyops-api`: RSA 2048, SHA-256, emitido por spicyops-ca, clave privada presente y trusted=yes; SAN `IP:192.168.8.1` y uso tls-server; vigencia del 16/10/2026 17:32:29 al 16/10/2027 17:32:29.
- API-SSL habilitado en 8729, `certificate=spicyops-api`, `tls-version=only-1.2`, `address=""`.

No se transcriben números de serie, huellas ni identificadores de claves. Programar renovación del servidor antes del 16/10/2027. La conexión TLS desde Raspberry se comprobó posteriormente en el paso 3; la restricción de origen del servicio sigue pendiente.

## Paso 3: exportar CA pública y preparar Raspberry

Primera parte: ejecutar en MikroTik:

```routeros
/certificate export-certificate spicyops-ca type=pem file-name=spicyops-ca
/file print where name="spicyops-ca.crt"
```

Exportar en PEM sin `export-passphrase` genera el certificado público `.crt`, sin exportar la clave privada. Descargar `spicyops-ca.crt` desde **WinBox > Files** mediante la sesión de administración ya utilizada. Conservar el archivo sin editar; no descargar ni transferir `.key` o `.p12`. El usuario confirmó la descarga y compartió una transferencia SCP finalizada al 100% (1147 bytes) hacia `/home/elex/spicyops-ca.crt`. La lectura y la prueba TLS se comprobaron después, según el resultado de este paso.

Segunda parte: en una terminal conectada a la Raspberry ejecutar estas lecturas para concretar traslado y prueba, sin instalar todavía paquetes ni modificar su servidor web:

```sh
whoami
cat /etc/os-release
uname -m
hostname -I
command -v openssl
date -Is
```

El usuario de Linux permitirá dar una instrucción de transferencia concreta sin asumir credenciales. Si `command -v openssl` no muestra ruta, no considerar OpenSSL instalado. No se solicita contraseña. Las direcciones pueden ocultarse salvo la IP LAN relevante. La CA ya se transfirió mediante SCP según salida compartida; se configurará su uso explícito en la prueba y en el agente; no es necesario instalarla globalmente en todos los servicios del sistema.

### Inventario de Raspberry confirmado por salida compartida

Usuario Linux `elex`, hostname `Spicy-RasPy`, Raspbian GNU/Linux 12 (bookworm), arquitectura reportada `armv6l`, LAN `192.168.8.90`, OpenSSL localizado en `/usr/bin/openssl`. El reloj mostró 16/10/2026 17:52:21 UTC−06. También se observan direcciones Tailscale, cuyos valores no son necesarios para esta guía. No se deduce el modelo exacto ni memoria disponible únicamente de ARMv6; sigue pendiente medir recursos.

ARMv6 debe considerarse al seleccionar paquetes y versiones del agente: no asumir compatibilidad de binarios ARMv7/ARM64. Para esta prueba ya existe OpenSSL; no se requiere instalar Python ni dependencias.

### Transferencia desde Windows

Usar una PowerShell local en la computadora que tiene el `.crt`, no la sesión SSH de Raspberry. Copiar la ruta completa del archivo desde el Explorador de Windows (opción “Copiar como ruta”) e introducirla cuando se solicite:

```powershell
$certSpicyOps = (Read-Host 'Pega la ruta completa de spicyops-ca.crt').Trim('"')
scp "$certSpicyOps" "elex@192.168.8.90:/home/elex/spicyops-ca.crt"
```

Se requiere cliente OpenSSH de Windows y acceso a la IP LAN por la red local o la ruta Tailscale existente. Si aparece una clave SSH de servidor desconocida, compararla con la identidad de la Raspberry por una vía ya confiable antes de aceptarla; no desactivar la verificación. La contraseña solicitada por scp es la de Raspberry y se escribe en el prompt local, no en el chat ni en los comandos guardados. Si la ruta local no existe o no hay conexión, detener y revisar el mensaje.

Transferencia del piloto confirmada por salida de PowerShell 7.6.7: archivo origen `C:\Users\ele\Documents\backup-mikro\spicyops-ca.crt`, destino `elex@192.168.8.90:/home/elex/spicyops-ca.crt`, 1147 bytes y progreso 100%. Esto acredita finalización del traslado, no validación del certificado. No se registró la contraseña.

### Prueba desde Raspberry

Ejecutar en Raspberry tras una transferencia exitosa:

```sh
openssl x509 -in "$HOME/spicyops-ca.crt" -noout -subject -issuer -dates
timeout 15s openssl s_client -connect 192.168.8.1:8729 -CAfile "$HOME/spicyops-ca.crt" -verify_ip 192.168.8.1 -verify_return_error -tls1_2 -brief </dev/null
```

La primera lectura debe identificar la CA SpicyOps-Local-CA y su vigencia, sin pedir ni mostrar una clave privada. La segunda debe negociar TLSv1.2 y mostrar `Verification: OK`. `-verify_ip` comprueba la identidad IP y `-verify_return_error` impide continuar como si un error de validación fuera aceptable. `timeout` limita esperas; un timeout o un error posterior al handshake requiere distinguir verificación del certificado y cierre de sesión, no marcar todo el paso como correcto sin revisar la salida.

Esta prueba comprueba transporte y certificado, sin enviar credenciales ni comandos RouterOS. No prueba permisos API ni operaciones sobre clientes. La CA se usa mediante `-CAfile`, sin cambiar el almacén global de confianza del sistema.

Resultado compartido por el usuario: CA con subject e issuer SpicyOps-Local-CA, vigencia en GMT equivalente a la registrada en el router; conexión establecida a 192.168.8.1:8729, TLSv1.2, ECDHE-RSA-AES256-GCM-SHA384, certificado CN 192.168.8.1, SHA256/RSA, `Verification: OK` y `DONE`. El comando incluyó `-verify_ip`, de modo que se comprobó identidad IP además de la cadena de confianza. Paso completado por evidencia compartida, sin prueba de autenticación API todavía.

Se mostró `Can't use SSL_get_servername` al conectar por IP sin nombre SNI. En esta ejecución fue informativo: la conexión, verificación y cierre finalizaron correctamente. No se deshabilitó ninguna validación para resolverlo.

Si falla, conservar la validación activa y diagnosticar fecha, CA, identidad y ruta. No basta con ver un socket abierto en 8729 ni usar una conexión sin validación como éxito de este paso. Los comandos y direcciones deben adaptarse para otro sistema.

## Paso 4: cuenta exclusiva de lectura

Estado: configuración comprobada por salidas del usuario. `spicyops-read` tiene únicamente `read,api` positivos; las demás políticas aparecen negadas. `spicyops-agent` aparece sin bandera X/E, con grupo spicyops-read y origen 192.168.8.90/32. La autenticación se comprobó después en el paso 6c. Los comandos siguientes se conservan para otras instalaciones: no repetir altas en el piloto. El límite de origen de esta cuenta no restringe por sí solo el servicio API-SSL para las otras cuentas.

En MikroTik, crear el grupo y la cuenta inicialmente deshabilitada:

```routeros
/user group add name=spicyops-read policy=read,api
/user add name=spicyops-agent group=spicyops-read address=192.168.8.90/32 disabled=yes comment="SpicyOps - lectura API desde Raspberry"
```

Si un objeto ya existe, detener y consultar sus propiedades en vez de sobrescribirlo. Elegir y guardar una contraseña nueva en un gestor de contraseñas. Para evitar problemas de escape al pegar en RouterOS, puede usarse una clave aleatoria de al menos 24 caracteres alfanuméricos. Sustituir el marcador antes de ejecutar; no enviar el comando con su contraseña al chat ni añadirlo al repositorio.

```routeros
/user set [find name="spicyops-agent"] password="REEMPLAZA_POR_TU_CLAVE_NUEVA"
/user enable [find name="spicyops-agent"]
```

Habilitar únicamente después de que la asignación de contraseña termine sin error. Si no se asignó, conservar deshabilitada la cuenta. No se cambia la cuenta admin ni los accesos existentes.

Comprobar y compartir solo estas salidas, sin contraseña:

```routeros
/user group print detail without-paging where name="spicyops-read"
/user print detail without-paging where name="spicyops-agent"
```

Se espera grupo con `read,api` permitidos y ninguna otra política positiva; puede mostrar otras políticas precedidas por `!`. Usuario habilitado, grupo correcto y `address=192.168.8.90/32`. Esto no acredita autenticación desde Raspberry: se verificará después con una lectura real sobre TLS. No probar con clientes ni ampliar a escritura aún.

Para revertir acceso de esta cuenta sin tocar administración: `/user disable [find name="spicyops-agent"]`. No borrar grupo/usuario si ya están en uso por otra integración. En otra red reemplazar dirección y nombres según su inventario.

## Paso 5a: restringir el servicio API-SSL

Estado: completado por salidas compartidas. El servicio muestra port=8729, address=192.168.8.90/32, certificate=spicyops-api y tls-version=only-1.2, sin banderas X/I. La nueva prueba desde Raspberry mostró TLSv1.2, Verification: OK y DONE. Valor anterior registrado para reversión: ADDRESS vacío. Se limita únicamente API-SSL; SSH y WinBox conservan su configuración para mantenimiento. Esta restricción afecta el acceso API-SSL de todas las cuentas, incluida admin, no solo spicyops-agent. En este piloto el único consumidor previsto es Raspberry .90; para otro sitio inventariar consumidores antes de restringirlo.

En MikroTik:

```routeros
/ip service set [find name="api-ssl"] address=192.168.8.90/32
/ip service print detail without-paging where name="api-ssl"
```

Se espera address=192.168.8.90/32, certificate=spicyops-api y tls-version=only-1.2, sin bandera X/I. Repetir después desde Raspberry:

```sh
timeout 15s openssl s_client -connect 192.168.8.1:8729 -CAfile "$HOME/spicyops-ca.crt" -verify_ip 192.168.8.1 -verify_return_error -tls1_2 -brief </dev/null
```

Se espera TLSv1.2, Verification: OK y cierre normal. El usuario compartió una nueva prueba exitosa y posteriormente confirmó ADDRESS .90/32 mediante la salida del servicio. No equivale a autenticación API. Un intento previo de ejecutar timeout/openssl en la terminal RouterOS produjo syntax error; el comando Linux no se ejecutó allí ni se deduce un cambio de configuración de ese error. Si se pierde acceso, inspeccionar mensaje e IP origen real antes de modificar firewall o ampliar redes permitidas.

Reversión exclusiva del filtro de origen del servicio al valor anterior, si hace falta diagnosticar desde administración:

```routeros
/ip service set [find name="api-ssl"] address=""
```

No ejecutarlo como parte de la secuencia normal. Sigue pendiente revisar el firewall vigente antes de añadir reglas en un paso 5b; el filtro ADDRESS no sustituye el firewall. API 8728 continúa habilitada hasta el paso de cierre previsto, con su propia configuración; restringir API-SSL no protege automáticamente ese otro servicio.

## Paso 5b: inspección del firewall y acceso administrativo

Estado: inspección completada mediante salidas del usuario. Se observan cinco reglas: cuatro forward para Morosos y una input que permite DNS UDP de Morosos. No hay filtro de puertos API en esa lista IPv4. Las sesiones admin aparecen desde 192.168.8.90 vía WinBox y vía telnet; ese dato de sesión no prueba que Telnet esté habilitado para conexiones externas ni justifica modificar la sesión actual. Antes de redactar reglas se revisó el orden vigente y la vía administrativa.

Ejecutar en MikroTik:

```routeros
/ip firewall filter print detail without-paging
/user active print detail without-paging
```

La primera salida permite localizar reglas input, condiciones y orden; la segunda muestra origen y método de las sesiones administrativas actuales. No muestran contraseñas. Estos comandos no añaden reglas ni cierran sesiones. La futura protección de API-SSL debe considerar reglas anteriores de aceptación y conservar mantenimiento por SSH/WinBox. No se diseñará un bloqueo general de administración sin evaluar esos accesos.

### Cambio acotado de firewall IPv4 para API

Estado: comprobado mediante lista compartida. Input contiene permiso DNS UDP de Morosos, seguido de accept TCP/8728,8729 desde .90 y drop TCP/8728,8729 para otros orígenes. Las dos reglas SpicyOps aparecen sin X/I y en orden correcto. El prompt compartido no muestra indicador Safe Mode; no se comprobó persistencia tras reinicio ni se necesita reiniciar para ello en este paso. La nueva prueba Raspberry mostró TLSv1.2, Verification: OK y DONE. El rechazo desde otra IP no se ha ensayado. Se incluyen 8728 y 8729 para limitar también la API sin TLS durante la transición; el cierre de 8728 sigue previsto después de comprobar autenticación cifrada. No constituye una revisión completa de seguridad del router ni un filtro IPv6.

En la terminal MikroTik, entrar en Safe Mode con Ctrl+X y comprobar que aparece su indicador. Ejecutar primero permitir y después bloquear:

```routeros
/ip firewall filter add chain=input action=accept protocol=tcp src-address=192.168.8.90/32 dst-port=8728,8729 comment="SpicyOps: permitir API desde Raspberry"
/ip firewall filter add chain=input action=drop protocol=tcp dst-port=8728,8729 comment="SpicyOps: bloquear API otros origenes"
/ip firewall filter print detail without-paging where chain=input
```

Se agregan al final porque, en las cinco reglas inspeccionadas, la única input anterior permite UDP/53, que no coincide con TCP/8728-8729. Las reglas forward no intervienen en el acceso al router. La regla permitir debe anteceder al bloqueo; no repetir las altas si se pierde la salida o ya existen comentarios iguales. En otra instalación, revisar reglas anteriores: una aceptación general previa puede anular el bloqueo y un descarte previo puede impedir el acceso del agente.

Desde la Raspberry repetir:

```sh
 timeout 15s openssl s_client -connect 192.168.8.1:8729 -CAfile "$HOME/spicyops-ca.crt" -verify_ip 192.168.8.1 -verify_return_error -tls1_2 -brief </dev/null
```

Tras verificar TLSv1.2 y Verification: OK y confirmar que la administración sigue funcionando, volver a la misma terminal MikroTik y pulsar Ctrl+X para salir de Safe Mode conservando cambios. No cerrar esa sesión antes de terminar. Si falla una línea o la prueba, detenerse y revisar; la pérdida anormal de la sesión Safe Mode revierte los cambios de su alcance. No garantiza reversión si ya se salió guardando.

Estas reglas no coinciden con WinBox/SSH ni el tráfico forward de clientes. Restringen origen IPv4, no identidad física del dispositivo. No se abrirán puertos en Starlink. Para revertir solo estas reglas, después de identificar inequívocamente que fueron las creadas por este paso, se pueden deshabilitar por sus comentarios:

```routeros
/ip firewall filter disable [find comment="SpicyOps: permitir API desde Raspberry"]
/ip firewall filter disable [find comment="SpicyOps: bloquear API otros origenes"]
```

La reversión no forma parte del procedimiento normal. Queda pendiente validar el rechazo desde otro origen antes de declarar comprobado el bloqueo, además de verificar contadores y configuración. No provocar esa prueba cambiando la IP de la Raspberry ni interrumpiendo su ruta de administración.

## Paso 6: preparar lectura autenticada de API

Estado: pendiente de autenticación; la prueba OpenSSL solo validó transporte y certificado. Antes de elegir versión de biblioteca, comprobar Python y herramientas en Raspberry ARMv6:

```sh
python3 --version
python3 -m pip --version
python3 -m venv --help
```

Son comprobaciones: el tercer comando muestra ayuda, sin crear un entorno. Si pip o venv no están disponibles, conservar el mensaje para decidir instalación compatible con Raspbian 12. No usar sudo pip, modificar Python del sistema ni crear todavía el agente. La prueba se hará después en un entorno separado con confianza explícita en la CA y contraseña introducida sin mostrarla ni guardarla en el historial. No pedir la contraseña en el chat.

### Paso 6a: entorno aislado de diagnóstico

Resultado del inventario compartido: Python 3.11.2; `python3 -m pip --version` devuelve No module named pip; `python3 -m venv --help` funciona. La ayuda no demuestra que ensurepip esté disponible, pero la ausencia de pip global tampoco demuestra que no pueda crearse un entorno con su propio pip.

Intentar en Raspberry, sin sudo y sin instalar paquetes todavía:

```sh
python3 -m venv "$HOME/spicyops-prueba/.venv"
```

Si termina sin error, comprobar:

```sh
"$HOME/spicyops-prueba/.venv/bin/python" -m pip --version
```

El primer comando crea un directorio de diagnóstico y su entorno; no instala el agente ni modifica servicios existentes. Se usa el intérprete por ruta explícita, sin activar el entorno. No usar --clear ni reutilizar un entorno de otra aplicación. Si la carpeta ya perteneciera a otra tarea, elegir un nombre nuevo antes de continuar.

Si falla, compartir el error y detener la instalación de bibliotecas. Un error de ensurepip puede requerir el paquete de distribución python3-venv/python3.11-venv; se decidirá a partir del mensaje real, sin recurrir a sudo pip ni alterar el Python del sistema. El usuario confirmó posteriormente que quedó listo tras los comandos de creación y comprobación. Se registra como confirmación verbal, sin salida de pip ni versión exacta compartida.

### Paso 6b: instalar biblioteca API en el entorno de diagnóstico

Estado: el usuario confirmó instalación y resultado esperado de pip check, sin log completo compartido. La conexión de biblioteca con el router se comprobó después en el paso 6c. Se selecciona `librouteros==4.2.2` para reproducibilidad del piloto. Consulta de PyPI el 16/10/2026: requiere Python >=3.10 y publica un wheel py3-none-any. Python 3.11.2 cumple el requisito y el paquete no requiere por sí mismo un binario ARMv7/ARM64; la importación y conexión reales en ARMv6 aún deben comprobarse.

Ejecutar en Raspberry, sin sudo y sin activar el entorno:

```sh
"$HOME/spicyops-prueba/.venv/bin/python" -m pip install "librouteros==4.2.2"
"$HOME/spicyops-prueba/.venv/bin/python" -m pip check
```

Si la instalación falla, detener y compartir el mensaje antes de ejecutar pruebas API. Se espera instalación exitosa y `No broken requirements found.` al revisar dependencias. No actualizar pip ni otras bibliotecas globales para este paso. Solo se modifica el entorno de diagnóstico, sin instalar el agente ni tocar servicios existentes. No se envían credenciales al router con estos comandos.

La versión se fija para esta prueba, no se prescribe como versión universal para todos los sistemas futuros. Conservar versiones resueltas y revisar compatibilidad antes de implementar el agente definitivo.

### Paso 6c: primera lectura autenticada

Estado: completado por salida compartida del usuario. La instalación y pip check se confirmaron verbalmente; la prueba posterior sí aporta salida de autenticación y consultas correctas. La versión solicitada fue 4.2.2; no se recibió una lectura separada de metadatos de versión instalada.

Ejecutar el bloque completo en la terminal de Raspberry. El código es diagnóstico temporal enviado por entrada estándar; no instala un agente, no guarda un archivo Python y no cambia configuración del router. getpass solicita la clave del usuario MikroTik spicyops-agent mediante la terminal, aunque Python lea el código desde el bloque. No es la contraseña Linux. No pegar la clave dentro del código ni compartirla.

```sh
"$HOME/spicyops-prueba/.venv/bin/python" - <<'PY'
from functools import partial
from getpass import getpass
from pathlib import Path
import ssl
from librouteros import connect

host = "192.168.8.1"
ctx = ssl.create_default_context(cafile=str(Path.home() / "spicyops-ca.crt"))
api = connect(
    host=host,
    port=8729,
    username="spicyops-agent",
    password=getpass("Clave de spicyops-agent: "),
    ssl_wrapper=partial(ctx.wrap_socket, server_hostname=host),
    timeout=10,
)
try:
    identity = list(api.path("system", "identity"))[0]
    resource = list(api.path("system", "resource"))[0]
    queues = list(api.path("queue", "simple"))
    print("Lectura API autenticada: OK")
    print("Router:", identity["name"])
    print("RouterOS:", resource["version"])
    print("Colas simples:", len(queues))
finally:
    api.close()
PY
```

Se mantiene validación de CA e identidad IP mediante SSLContext predeterminado y server_hostname. El login se transmite únicamente dentro de TLS validado. Timeout de socket de 10 segundos; la conexión se cierra al terminar las lecturas. Se consultan identidad, recursos y colas simples; solo se imprimen nombre, versión y cantidad de colas, sin listar clientes o credenciales.

Resultado esperado: Lectura API autenticada: OK, identidad del MikroTik, versión observada y cantidad de colas. La referencia documental anterior tiene 15 colas, pero un conteo diferente debe revisarse como cambio de estado, no asumirse error de conexión. Si aparece error, compartirlo sin incluir contraseña y detener la secuencia. No ampliar permisos por adelantado ni desactivar validación TLS.

Una lectura correcta confirma autenticación y esos permisos de lectura en el router probado; no valida operaciones de escritura, API en RouterOS 7 ni el efecto real de suspensión. El cierre de API sin TLS se confirmó después en el paso 7. La prueba desde otro origen continúa pendiente.

### Resultado comprobado del paso 6c

El usuario compartió:

```text
Lectura API autenticada: OK
Router: Main SN - La Playa
RouterOS: 6.49.23 (stable)
Colas simples: 15
```

Confirma que Python/librouteros funcionaron para estas lecturas en la Raspberry ARMv6 y que la cuenta spicyops-agent pudo autenticarse en 8729 con el contexto TLS validado del diagnóstico. El conteo coincide con el export. No se deduce compatibilidad de escritura, medidas de consumo o soporte probado de RouterOS 7. Tampoco prueba el rechazo de otro origen. El usuario sigue con solo read,api.

## Paso 7: cerrar la API sin TLS

Estado: completado por salida compartida. API/8728 aparece con X/I, y API-SSL/8729 sin X/I con address=192.168.8.90/32, certificate=spicyops-api y tls-version=only-1.2. El resultado acredita servicio sin TLS deshabilitado; no se recibió una nueva conexión autenticada después del cierre. El diagnóstico anterior ya utilizaba exclusivamente 8729 y su configuración permanece igual. La API 8728 fue habilitada durante la preparación, sin consumidor previo identificado en las fuentes. Para otro sitio confirmar primero que ninguna herramienta existente dependa de ese puerto.

En MikroTik:

```routeros
/ip service disable [find name="api"]
/ip service print detail without-paging where name~"^api"
```

Esperado: api/8728 con bandera X; api-ssl/8729 sin X/I, address .90/32, certificate spicyops-api y tls-version only-1.2. Se deshabilita el servicio de nombre exacto api, no api-ssl. Se conservan usuario y política api: esa política también es necesaria para API-SSL y no debe retirarse del grupo.

No requiere reinicio ni cambios en WinBox/SSH o reglas de clientes. Conservar por ahora las dos reglas IPv4 de firewall con 8728/8729; no es necesario reescribirlas para deshabilitar el servicio.

Si existe una dependencia no inventariada que obligue a revertir temporalmente, la reversión acotada es `/ip service enable [find name="api"]`; no ejecutarla como parte normal del procedimiento. Debe documentarse la dependencia y migrarla a TLS en lugar de dejar el puerto activo indefinidamente.

## Paso 8a: inspección de Morosos y portal sin cambios

Estado: comprobado por salidas del usuario: diez entradas Morosos con bandera X (.52–.55, .57–.62); NAT WAN, redirección DNS UDP/53 y dst-nat HTTP/80 hacia .90:80 activos. lighttpd muestra loaded/active/running y unidad /lib/systemd/system/lighttpd.service; hay sockets TCP escuchando en 0.0.0.0:80 y [::]:80. No se probó la página ni su acceso desde clientes. El canal de integración ya dispone de una lectura autenticada probada y API sin TLS deshabilitada. No elevar todavía permisos ni suspender abonados. La prueba de rechazo desde otro origen permanece abierta; una conexión Windows vía subnet router puede llegar con origen .90 por SNAT, por lo que no demuestra rechazo de otros clientes LAN.

En MikroTik:

```routeros
/ip firewall address-list print detail without-paging where list="Morosos"
/ip firewall nat print detail without-paging
```

En Raspberry:

```sh
systemctl show lighttpd -p LoadState -p ActiveState -p SubState -p FragmentPath --no-pager
ss -ltn '( sport = :80 )'
```

Son lecturas. La lista permite observar qué entradas participan realmente; NAT verifica reglas vigentes de redirección. systemctl show permite confirmar o descartar lighttpd sin iniciar/reiniciar el servicio; ss comprueba si hay un socket TCP escuchando en 80, sin probar por sí mismo qué página sirve ni su accesibilidad desde un abonado. Si LoadState=not-found, conservar la salida y buscar el servidor real en el siguiente diagnóstico; no instalar lighttpd por suposición.

Con esos resultados se documentó el servicio web existente. El usuario indicó después que el portal es secundario: las pruebas adicionales quedan aplazadas; la siguiente prioridad es identificar un equipo de laboratorio para control de acceso y velocidad. No agregar excepciones NAT/firewall ni limpiar conexiones globales basándose solamente en nombres de reglas. La cuenta spicyops-agent conserva read,api. No se ha validado alta, baja, cambio de velocidad ni efecto real de corte con este agente de diagnóstico.

## Paso 8b: respuesta HTTP del portal (secundario, revisión adicional aplazada)

Estado: comprobado mediante salida compartida. Host 192.168.8.90 devuelve 301 con redirección y sin Content-Type; portal.spicynet.local devuelve 200 text/html sin redirección; example.com devuelve 301 con redirección y sin Content-Type. No se leyó el destino de la redirección ni se probó el recorrido desde abonados. No hace falta continuar esta investigación para el MVP por indicación expresa del usuario. Antes de reparar forwarding o hairpin NAT comprobar que la página responde. Ejecutar en Raspberry:

```sh
python3 - <<'PY'
from http.client import HTTPConnection

for host in ("192.168.8.90", "portal.spicynet.local", "example.com"):
    connection = HTTPConnection("127.0.0.1", 80, timeout=5)
    try:
        connection.request("GET", "/", headers={"Host": host})
        response = connection.getresponse()
        print("Host:", host)
        print("HTTP:", response.status, response.reason)
        print("Tipo:", response.getheader("Content-Type"))
        print("Redirige:", response.getheader("Location") is not None)
        print()
    except Exception as error:
        print("Host:", host, "| Error:", type(error).__name__, str(error))
    finally:
        connection.close()
PY
```

Se hacen tres GET locales a 127.0.0.1:80, con Host de IP, dominio local y nombre externo de ejemplo. El tercer caso representa el encabezado que conservaría una petición HTTP redirigida, sin contactar a example.com ni modificar DNS. http.client no sigue redirecciones automáticamente. Solo se imprime estado, tipo de contenido y presencia de redirección, sin mostrar ni guardar contenido de la página.

Un HTTP 200 compatible con HTML sería señal de respuesta web; no demuestra que sea la página correcta ni que funcione a través de la política Morosos. Si aparecen 301/302, 403/404, errores o respuestas distintas según Host, revisar configuración antes de añadir reglas de red. No activar Morosos para ningún abonado durante esta prueba.

## Prioridad actual: piloto de control de clientes

El usuario indicó expresamente que el portal cautivo es secundario. Quedan aplazadas su reparación y pruebas de recorrido; no son requisito para dar por válido el control de clientes. No añadir reglas de portal ni dedicar más diagnóstico a su web salvo que se retome esa función.

Destino seleccionado posteriormente por el usuario: `011_Lulu Mendoza`, `192.168.8.62`, para un ensayo temporal y acotado. La captura muestra 2M/4M y cola habilitada. El [registro de la prueba](prueba-cliente-011.md) contiene alcance, consultas de estado inicial y restauración pendiente de preparar. No se ha modificado el cliente. Mantener protegidos gateway/AP .1–.6, Casa .50 y Raspberry .90. No reutilizar .51 por asumir que está libre: la baja comercial no acredita que la dirección sea reutilizable.

Se conserva el grupo read,api hasta preparar las pruebas con estado inicial y recuperación definidos. Para .62 la primera escritura propuesta reenvía el mismo límite 2M/4M y comprueba configuración, con elevación temporal y devolución a read,api. El usuario no tiene acceso local al cliente. Cambios efectivos de velocidad y suspensión/reactivación quedan para una etapa posterior con recuperación preparada. No crear una cola duplicada ni borrar el servicio para simular un alta; el alta nueva se verifica por separado. No se ha implementado panel ni agente permanente.

## Consideraciones para los pasos siguientes

Preparar un respaldo y documentar valores previos antes de cambiar servicios. No restringir SSH o WinBox a la Raspberry sin identificar primero la ruta de administración utilizada. Las reglas de firewall dependen del orden existente: inspeccionarlo antes de añadir permisos o bloqueos y usar Safe Mode en los cambios de acceso cuando corresponda. No reiniciar el router para cambios que no lo requieran.

Un grupo con `write` tiene alcance mayor que un único abonado; RouterOS no debe tratarse como si diera permisos por objeto del CRM. Compensar con origen restringido, operaciones admitidas en el agente y trazabilidad. No dar `full`, `policy`, `sensitive`, `reboot` o acceso SSH a la cuenta del agente por comodidad; añadir permisos solo si una operación comprobada los necesita y documentar el motivo.

En la red del compañero hay que inventariar primero IP de gestión, dirección de agente, método de clientes y reglas existentes. Una integración PPPoE/RADIUS puede necesitar otro adaptador; habilitar API-SSL por sí solo no la convierte en compatible con la política SpicyNet.

La renovación del certificado debe incluir fecha de vencimiento, responsable y prueba desde el agente antes de reemplazarlo. No solucionar errores de TLS desactivando validación de certificado o nombre. La reversión de un ajuste debe usar el valor anterior registrado, sin restaurar globalmente el router por un fallo de acceso individual.

## Fuentes

- [MikroTik: certificados](https://help.mikrotik.com/docs/spaces/ROS/pages/2555969/Certificates).
- [MikroTik: API y API-SSL](https://manual.mikrotik.com/docs/developer-guides/api/).
- [MikroTik: servicios y restricciones de origen](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services).
- [MikroTik: usuarios y políticas](https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User).
- [MikroTik: firewall filter y cadenas input/forward](https://help.mikrotik.com/docs/spaces/ROS/pages/48660574/Filter).
- [librouteros: conexión TLS](https://librouteros.readthedocs.io/en/latest/connect.html).
- [librouteros: lecturas con Path](https://librouteros.readthedocs.io/en/latest/path.html).
- [PyPI: librouteros y metadatos de versión](https://pypi.org/project/librouteros/4.2.2/).
- [Python 3.11: venv y arranque de pip](https://docs.python.org/3.11/library/venv.html).
- [OpenSSL: s_client y opciones de verificación](https://docs.openssl.org/3.0/man1/openssl-s_client/).

Los manuales incluyen funciones recientes; esta guía evita depender de propiedades exclusivas de v7. Los comandos entregados se contrastarán con las respuestas de RouterOS 6.49.23 antes de continuar.

## Estado más reciente del piloto de escritura

El usuario confirmó escritura API del mismo límite sobre .62, con plan 2M/4M conservado y Morosos sin modificar. El primer retorno a read,api conservó write positivo; la corrección policy=read,api,!write quedó confirmada por nueva salida: read,api positivos y !write. Ver prueba-cliente-011.md. El ensayo queda cerrado y la cuenta en lectura. El usuario pidió terminar la secuencia: no se requieren más comandos ahora. Las pruebas de efecto real, alta nueva y rechazo desde otro origen quedan como límites documentados, sin afirmar que se ejecutaron.
