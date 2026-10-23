# Verificación del rework: SpicyOps para Windows

**Actualización 22/10/2026:** [auditoría vigente de Morosos, Analytics, inventario, plazos y coordinador](auditoria-20261022.md). La entrega aislada `dist/auditoria-20261022` tiene 98 pruebas correctas y verificación del EXE. Los resultados siguientes conservan su fecha y alcance históricos.

Fecha: 16/10/2026, America/Mexico_City. El usuario reemplazó la demo de alta manual por conexión Raspberry → MikroTik e importación automática. Aceptó un programa Windows para aprovechar su acceso SSH por LAN/Tailscale.

## Ampliación verificada: Morosos por cliente

Se añadieron **Suspender por adeudo** y **Quitar de morosos** por servicio individual, con confirmación de localidad, nombre e IP. La única escritura permitida es agregar/habilitar/deshabilitar la entrada IPv4 en la lista fija `Morosos`; el inventario se relee antes de escribir y la lista se relee después. No se modifican planes, contadores, reglas de firewall ni permisos. Un resultado incierto conserva los últimos datos observados y obliga a sincronizar antes de otra acción. Se reutiliza la exclusión de operaciones en curso por localidad.

Comprobaciones de esta ampliación:

- `manage.py test portal.tests --noinput`: **45 pruebas aprobadas**, incluidas las 36 anteriores. Nueve pruebas nuevas cubren suspensión/retiro y reactivación, idempotencia, aislamiento de localidades, confirmación y sesión/CSRF, identificadores obsoletos, localidad desconectada/ocupada, reconfiguración/desconexión concurrentes, resultado incierto, restricciones compartidas/dinámicas/duplicadas, permisos denegados, lectura posterior y transporte de la acción por SSH real en loopback. El acceso RouterOS de estas pruebas es simulado.
- Sintaxis del lector compatible con Python 3.11 mediante `ast.parse(feature_version=(3,11))`.
- Ejecutable reconstruido con `scripts/build_windows.py` y **comprobado con `scripts/smoke_windows.py`**: arranque, UI vacía, rutas/recursos, sesión, DPAPI, instancia única y persistencia. El test confirma además los botones y el formulario de Morosos en el ejecutable con una localidad sintética temporal, sin enviar operaciones al router.
- Revisión visual del HTML de Clientes con datos sintéticos: botones de ambas acciones, apertura/cancelación de confirmación y diálogo a 390 px. Evidencia local ignorada en `.local/morosity-qa/confirmacion.png` y `movil.png`. La vista no usó credenciales ni conexiones reales.
- ZIP actualizado mediante `scripts/package_windows.py`, sin perfiles ni estado privado.

No se ejecutó suspensión ni reconexión de clientes reales. Se requiere cuenta API con escritura y reglas de bloqueo existentes. La lista no demuestra corte físico: FastTrack, orden del firewall, conexiones abiertas o IPv6 pueden permitir tráfico. El control solo alcanza la IPv4 individual de la cola; no automatiza vencimientos ni registra pagos. Referencias: [Address lists de MikroTik](https://manual.mikrotik.com/docs/firewall-and-quality-of-service/firewall/address-lists/) y [Packet Flow / FastTrack](https://help.mikrotik.com/docs/spaces/ROS/pages/328227/Packet%2BFlow%2Bin%2BRouterOS).

Los apartados siguientes conservan los resultados del rework inicial de lectura.

## Qué cambió

- `portal/`: interfaz nueva con Analytics, Clientes y Conexiones; estado inicial vacío y formulario SSH/API-SSL. No importa ni muestra datos ficticios.
- `portal/connector.py` y `portal/remote_reader.py`: cliente SSH en Windows, huella de host validada y lector efímero que usa Python/librouteros ya existente en Raspberry. No instala archivos remotos ni cambia la red.
- `portal/telemetry.py`: normalización de colas, contadores y velocidades; cálculo por intervalo o aproximación explícita con uptime.
- `portal/store.py`: perfiles y lecturas cifrados; metadatos editables separados de los campos observados de MikroTik. Sin ORM, PostgreSQL ni migraciones para el producto vigente.
- `run_panel.py`, `SpicyOps.spec`, `scripts/build_windows.py`: aplicación Windows portable con ventana de Edge, reapertura/salida desde bandeja y una sola instancia por carpeta de datos. Incluye su runtime Python; no instala Python globalmente.
- `README.md`, `AGENTS.md` y `docs/encargo-panel-conectado.md`: alcance actualizado. Los documentos del primer encargo llevan aviso histórico. Se retiró `seed_demo` y se detuvieron/eliminaron el clúster y el estado simulado anteriores.

Las carpetas `config-mikro/` y `config-antenasyclientes/` permanecen intactas. No se accedió a sus secretos para autoconectar.

## Pruebas ejecutadas

Entorno de construcción: Windows 11 x64, Python 3.12.14, Django 5.2.18, Paramiko 4.0.0, PyInstaller 6.19.0 y Waitress 3.0.2.

`manage.py test portal.tests --noinput -v 1`: **36 pruebas aprobadas**, sin crear ni usar una base de datos. Los datos sintéticos están confinados a tests efímeros y no se incluyen como conexiones o clientes de la aplicación.

| Grupo | Cantidad | Alcance |
|---|---:|---|
| Telemetría y cálculos | 13 | RouterOS 6/7 normalizado; Mbps, bytes y tiempos; proyecciones 24 h/30 días; ausencia de datos; reinicios; resets de contador; infraestructura y colas ambiguas |
| Aplicación y persistencia | 18 | Navegación vacía; sesión de apertura firmada; CSRF; importación desde conector; errores sin clientes inventados; credenciales fuera de HTML/cookies; datos cifrados; notas por localidad; desconexión/reconexión; preservación exacta de contraseñas; cambio LAN/Tailscale conservando huella y notas |
| Conector | 5 | SSH real contra servidor efímero en **loopback**; autenticación y JSON cifrado por stdin; rechazo de huella desconocida/cambiada antes de autenticar; errores saneados; transporte RouterOS simulado limitado a `/print`, TLS 1.2 y validación de host |

La prueba SSH local acredita el protocolo del conector, no acceso a una Raspberry física. Los sockets se cierran deliberadamente en los casos de rechazo de huella; Paramiko puede imprimir avisos de cierre/reset del servidor de test. La suite debe tener permitido loopback; bajo bloqueo de red del sandbox, esos tres casos no pueden ejecutarse y no se deben presentar como fallos del router.

## Ejecutable comprobado

Se construyó `dist/SpicyOps/SpicyOps.exe`. `scripts/smoke_windows.py` ejecuta **el binario**, no las fuentes, con estado temporal dentro del proyecto. Comprobó:

1. Arranque del servidor embebido sin depender del Python externo ni de PostgreSQL.
2. Analytics/Clientes/Conexiones/formulario y recursos CSS disponibles.
3. Rechazo de apertura con firma falsa.
4. Clave de instalación protegida con **DPAPI** y ausencia del archivo de clave de texto en la versión empaquetada.
5. Una segunda apertura reutiliza la instancia y no crea otro servidor.
6. Un alias guardado en el estado cifrado aparece después de detener y reiniciar el ejecutable. Esa localidad es exclusiva del test y su carpeta se elimina al finalizar.

Resultado de la prueba del ejecutable: **OK**. La distribución solo incluye fuentes/recursos y dependencias permitidos por el `.spec`; no incluye `.local`, configuraciones reales, contraseñas, perfiles ni los tests del proyecto.

Se inició además el programa en modo de ventana/bandeja para revisar el resultado. La interfaz servida por el ejecutable se inspeccionó en navegador a tamaño de escritorio y ventana estrecha: navegación, ausencia de abonados de ejemplo, tabla de clientes, cambio Mbps ↔ MB/s y formulario SSH. Capturas en `.local/rework-qa/`, excluidas de Git. No se rellenaron ni enviaron contraseñas reales.

También se ejecutaron `manage.py check`, `pip check`, compilación de módulos y análisis de sintaxis Python 3.11 del lector remoto. No se ejecutó un intérprete 3.11 ni hardware ARMv6.

## Qué falta comprobar físicamente

No se ha abierto sesión en la Raspberry del usuario ni en un MikroTik real durante este rework. El usuario debe introducir su acceso en el formulario del programa; no se obtiene desde archivos sensibles ni desde el chat. Deben comprobarse entonces intérprete/librouteros, ruta del certificado, API-SSL, permisos y formato real de las estadísticas para cada localidad y versión.

El lector se diseñó para el esquema de **colas simples** RouterOS 6/7. No se afirma que detecte clientes PPPoE/RADIUS u otros esquemas sin adaptador. Tampoco una cola habilitada prueba acceso a internet en una vivienda. Los contadores ausentes/ambiguos aparecen como desconocidos.

Una caída visible del contador invalida su intervalo; un reset que suceda y vuelva a superar el valor anterior entre dos lecturas no es detectable solo con esos valores. Uptime no acredita la edad del contador. La proyección es a ritmo constante, no consumo mensual medido ni facturación.

No se ha publicado una web ni modificado la Raspberry, los permisos, el MikroTik, Tailscale, lighttpd o clientes reales. Las velocidades y contadores son de lectura; alias/contacto/ubicación/notas se editan solo en SpicyOps. La ejecución de pruebas físicas de escritura requiere autorización específica y comprobación en el cliente. Lulu y el portal cautivo conservan su cierre/prioridad anteriores.

Fuentes técnicas contrastadas: [colas de MikroTik](https://help.mikrotik.com/docs/spaces/ROS/pages/328088/Queues), [API librouteros](https://librouteros.readthedocs.io/en/latest/api_analysis.html) y [cliente/validación de host Paramiko](https://docs.paramiko.org/en/4.0/api/client.html). Los resultados de ejecución anteriores son evidencia local propia, no deducciones de esos manuales.

## Selector Todos — 19 de octubre de 2026

El selector superior incluye Todos y abre la lista conjunta de Clientes. Solo reúne perfiles conectados; cada fila indica localidad, fecha de su última lectura y errores de lectura si existen. No inicia conexiones ni sincronizaciones al consultar. Las localidades desconectadas conservan su consulta individual. Analytics mantiene el cálculo por localidad.

Verificación: `manage.py test portal.tests --noinput` completó 47 pruebas; `pip check` no encontró dependencias rotas. Los nuevos casos comprueban IP/ID repetidos entre localidades, exclusión de desconectadas, búsqueda, estado vacío, conservación de la selección y aislamiento de notas y Morosos. El conector de las acciones nuevas se sustituyó por respuestas de prueba; las pruebas SSH existentes usan loopback.

Se reconstruyó `dist/SpicyOps/SpicyOps.exe`. `scripts/smoke_windows.py` confirmó arranque, persistencia tras reiniciar y Todos con dos localidades activas y una desconectada en un estado temporal exclusivo de prueba. Se comprobó también que las plantillas, CSS y JavaScript empaquetados coinciden con las fuentes. Las pruebas de loopback y del ejecutable requirieron ejecución fuera del entorno restringido. No se consultaron ni modificaron equipos reales.

## Indicadores de conexión — 19 de octubre de 2026

La localidad lateral y las tarjetas de Conexiones comparten un indicador: punto verde y Activa para perfiles conectados sin error, ámbar y Error de conexión cuando la última operación falló, gris y Desconectada tras desconectar. El selector también muestra el estado en texto. Todos resume localidades activas y con error. La fecha de lectura permanece separada: el indicador refleja el estado registrado, sin comprobaciones continuas ni nuevas conexiones automáticas.

Las 24 pruebas de interfaz existentes pasaron. Se inspeccionó en navegador una vista temporal con los tres estados y lectura antigua, usando exclusivamente datos ficticios. La prueba del ejecutable incluye las tres variantes del indicador.

El ejecutable habitual se reemplazó tras cerrar la instancia abierta con autorización del usuario. Su prueba de arranque, persistencia e indicadores terminó correctamente; las plantillas y estilos de la distribución coinciden con las fuentes. No se realizaron conexiones físicas.

## Tabla compacta de Clientes — 19 de octubre de 2026

Morosidad se presenta como Suspender, con interruptor Sí/No que refleja la restricción observada y abre la confirmación antes de cualquier operación. Cancelar conserva su valor. Se mantiene el destino por localidad y los controles del servidor. Cola habilitada se muestra como Habilitada, incluso en lecturas guardadas anteriormente; los colores se conservan.

La tabla usa columnas de ancho limitado y ajuste de texto. Hasta 1050 px las filas se presentan como tarjetas con etiquetas. Se verificaron las vistas individual y Todos, nombres largos, restricción activa, cola deshabilitada y diálogos de suspensión/reactivación en navegador. No hubo desbordamiento horizontal a 1280, 1100 y 390 px en las vistas comprobadas. Las 24 pruebas de interfaz pasaron. La prueba del ejecutable habitual confirmó los recursos actualizados, el interruptor y el texto Habilitada. Solo se actualizaron plantillas y estilos de la distribución; no fue necesario recompilar su código. No se ejecutaron operaciones en equipos reales.


## Fechas en consumo entre lecturas — 19 de octubre de 2026

Cada barra muestra hora y fecha de cierre (día/mes), con tonos violeta y turquesa alternados al cambiar de día local. La unidad sigue siendo GB por intervalo. El texto al pasar el cursor incluye inicio y fin con año; la nota aclara que un intervalo puede abarcar varios días. En móvil se conserva el ancho legible mediante desplazamiento horizontal. No cambian los deltas ni las proyecciones.

Pasaron las 37 pruebas de interfaz y telemetría y la comprobación de dependencias. Una comprobación adicional con 12 intervalos sintéticos verificó el cruce de medianoche local, tres fechas consecutivas, agrupación de colores y el texto del intervalo completo. No se cargaron datos ficticios en la instalación del usuario. La inspección visual en navegador quedó bloqueada por la política que impide abrir archivos locales.

La suite completa ejecutó 47 pruebas: cuatro casos de SSH en loopback fallaron por conexión bloqueada; la revisión automática rechazó su repetición fuera de la restricción. No se verificaron equipos físicos ni se ejecutaron operaciones en la red real.

Se reconstruyó el ejecutable habitual y el ZIP portable. La prueba del ejecutable pasó fuera de la restricción, usando solo HTTP en loopback y estado temporal: arranque, rutas, recursos, DPAPI, persistencia y gráfica con dos lecturas sintéticas, fecha e intervalo completo. La plantilla y los estilos empaquetados coinciden byte por byte con las fuentes.


## Periodo analizado en estimaciones — 19 de octubre de 2026

La tabla distingue el contador actual del consumo observado en el periodo. Periodo analizado muestra inicio y fin con fecha, año y hora locales, además de la duración del historial válido. Los encabezados son Estimado diario y Estimado a 30 días; el botón se llama Actualizar y estimar. La nota explica que la duración no es la antigüedad de la última actualización. La selección de la primera referencia válida y las fórmulas permanecen iguales.

El modo uptime conserva su aviso aproximado y muestra Tiempo encendido; no inventa fechas de lecturas ni presenta el contador como consumo observado de un periodo confirmado. La tabla conserva desplazamiento horizontal en pantallas estrechas.

Pasaron 38 pruebas de interfaz y telemetría, incluida una referencia de 2 días y 20 horas con una lectura intermedia solo dos minutos anterior a la final. También se comprobó que los resets cambian la fecha de referencia y que uptime no recibe fechas observadas. La comprobación de dependencias terminó sin errores. No se hicieron conexiones a equipos físicos ni se repitió la suite SSH bloqueada anteriormente.

El ejecutable reconstruido pasó la prueba de arranque, persistencia y renderizado de Periodo analizado, fechas y consumo observado con dos lecturas sintéticas, usando estado temporal y HTTP en loopback. La plantilla y los estilos distribuidos coinciden con las fuentes. Se actualizó también el ZIP portable. No se inspeccionó visualmente el resultado en navegador en esta revisión.


## Retiro de estimaciones — 19 de octubre de 2026

Por confirmación expresa del usuario, se elimina Estimación por cliente, sus tarjetas diaria y a 30 días, tabla, selector y alternativa por uptime. Se retira también la función de proyección y la selección de modo en el servidor. Una sesión anterior o un parámetro mode ya no activa cálculos ni mensajes de estimación. Se conserva el historial existente exclusivamente para los datos observados; no se borran localidades ni lecturas.

Analytics muestra dos tarjetas (contador acumulado y clientes detectados), la gráfica titulada Consumo observado y el resumen del router. La gráfica conserva fechas, colores, GB y detalle del intervalo; no cambia la obtención de lecturas ni el filtrado de reinicios/resets. Se actualizan el README, el encargo y el LEEME de la distribución.

Pasaron 33 pruebas de interfaz y normalización. Se reemplazaron las pruebas de proyecciones retiradas por verificaciones del flujo de actualización sin estimaciones, rechazo de modos antiguos y conservación de la gráfica sin mezclar reinicios ni resets. La comprobación de dependencias terminó sin errores. No se consultaron equipos reales ni se repitieron las pruebas SSH bloqueadas anteriormente.

El ejecutable reconstruido pasó la verificación con estado temporal: arranque, persistencia, gráfica con fechas y ausencia de tabla, tarjetas y selector de estimaciones. La plantilla y CSS distribuidos coinciden con las fuentes. No se hizo una inspección visual en navegador en esta revisión.


## Flecha de datos en Clientes — 19 de octubre de 2026

El botón Ver datos se presenta como flecha vectorial diagonal hacia arriba a la derecha. Conserva el diálogo individual, el color y un área de pulsación de 40 px; title y aria-label mantienen su significado accesible. Pasaron las 25 pruebas de interfaz y la prueba del ejecutable con estado temporal. Se comprobó el renderizado de la flecha y su enlace al diálogo; plantilla y CSS distribuidos coinciden con las fuentes. Se actualizan los recursos del programa y el ZIP sin recompilar código Python. No se hicieron conexiones físicas.


## Aclaración: conservar lista de estimaciones — 19 de octubre de 2026

El usuario aclara que quiere conservar las tarjetas y la lista por cliente de estimados en 24 horas y 30 días. Esto sustituye la interpretación del retiro completo documentada antes. Se restauran usando exclusivamente el contador acumulado dividido entre el uptime del router, con aviso visible de aproximación y edad del contador no confirmada. No se restaura el selector, el promedio entre lecturas ni la columna de intervalo/periodo analizado. La gráfica y la flecha de datos en Clientes permanecen.

La función solo calcula por uptime; el historial permite descartar resets y colas nuevas conocidas, sin usarse para calcular el promedio. No hay proyección si el contador falta, la cola es ambigua o el uptime es menor de un minuto. Las 37 pruebas de interfaz y normalización pasaron, incluidos el cálculo por uptime, su diferencia con una proyección por delta, y los casos de exclusión. No se hicieron conexiones físicas.

El ejecutable reconstruido pasó la prueba de arranque, persistencia y recursos con estado temporal: lista y tarjetas de estimaciones presentes, aviso por uptime, sin selector ni periodo analizado. Se comprobaron las plantillas y CSS empaquetados contra las fuentes. La prueba usa solo HTTP en loopback. Se actualiza el ZIP portable; no se realizó inspección visual en navegador en esta revisión.
