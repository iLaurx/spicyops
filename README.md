# SpicyOps 1.0.0 para Windows

Distribución oficial local: **`dist/SpicyOps-1.0.0-Windows/SpicyOps/SpicyOps.exe`**. ZIP: **`dist/SpicyOps-1.0.0-Windows/SpicyOps-1.0.0-Windows.zip`**. Extrae todo y conserva `_internal`. Paquete sin firma digital, preparado localmente; sin publicación remota. Las distribuciones anteriores se conservan como históricas.

[Guía pública](docs/guia-publica.md) · [Notas de versión](docs/release-1.0.0.md) · [Checklist](docs/checklist-release.md) · [Verificación final](docs/verificacion-release-1.0.0.md) · [Piloto pendiente](docs/aceptacion-piloto.md).

Recuperación y respaldo portable cifrado con contraseña desde **Respaldos** en el pie. El estado dañado o una clave no accesible abren recuperación; no se borran originales.

## Usar el programa

Abrir `dist/SpicyOps-1.0.0-Windows/SpicyOps/SpicyOps.exe`. Es una distribución portable: conservar la carpeta `_internal` junto al ejecutable. No necesita instalar Python, PostgreSQL, Docker ni crear una base de datos. La interfaz utiliza un tema oscuro en Analytics, Clientes y Conexiones, incluidos formularios y ventanas de datos. En Clientes, cada cliente se identifica visualmente con un icono vectorial de usuario. Las localidades y Conexiones muestran un punto verde con **Activa**, ámbar con **Error de conexión** o gris con **Desconectada**. El estado refleja la última operación y no caduca por la antigüedad de la lectura; su fecha se muestra por separado. La ventana usa Microsoft Edge; si no está disponible, se abre el navegador predeterminado. El icono de SpicyOps en la bandeja permite reabrir la ventana o salir.

1. **Conexiones → Nueva localidad**: dirección de Raspberry por red local/Tailscale, puerto y usuario SSH; contraseña o clave SSH de Windows. Completar acceso API-SSL de lectura y certificado CA del MikroTik. Confirmar la huella SSH del equipo.
2. Al conectar, comprobar Raspberry y MikroTik e importar automáticamente las colas individuales. Conectar y sincronizar solo leen; no se instalan servicios en Raspberry.
3. El selector superior incluye **Todos**: abre Clientes con los servicios de todas las localidades activas (conectadas), usando su última lectura guardada e indicando localidad y fecha por fila. Las desconectadas siguen disponibles al seleccionarlas individualmente. La búsqueda también acepta localidad; Ver datos y Suspender conservan el destino individual.
4. **Clientes**: consultar IP, plan en Mbps (o MB/s), contadores en GB y estado de configuración. La flecha diagonal **↗ (Ver datos)** permite guardar nombre visible, contacto, ubicación y notas, independientes de lo leído en MikroTik.
   **Revisar colas excluidas** muestra identificación, IP y motivo. **Incluir en Clientes** permite una excepción local para una cola IPv4 individual válida filtrada como infraestructura; **Revertir inclusión** restaura el filtro. Se conserva por localidad, ID, nombre de cola e IP. Un cambio de identidad/IP no hereda la excepción. No crea clientes manuales ni escribe en MikroTik; Morosos conserva su validación fresca y confirmación individual. Las lecturas antiguas sin detalle requieren sincronizar primero.
5. **Analytics → Actualizar lectura**: consultar los contadores actuales y la gráfica de consumo observado, y la lista por cliente con estimados de 24 horas y 30 días, calculados únicamente como aproximación desde encendido. No hay selector ni proyecciones entre lecturas. Cada barra conserva fecha y hora, colores por día y el detalle de inicio y fin al pasar el cursor. En pantallas estrechas se desplaza horizontalmente.

En **Clientes → Suspender**, un interruptor compacto muestra **Sí** cuando la restricción está activa y **No** cuando está desactivada. Pulsarlo abre la confirmación para suspender o reactivar; no cambia el estado hasta confirmar y leer el resultado. La tabla adapta las filas a tarjetas en pantallas estrechas. La confirmación muestra localidad, cliente e IP. Suspender agrega la IPv4 a la lista exacta `Morosos` o habilita su entrada existente; quitar deshabilita su entrada individual, sin borrarla. El programa vuelve a leer la lista para confirmar el estado y no cambia planes, contadores, reglas ni permisos.

Este control requiere una cuenta API con escritura y reglas de bloqueo de `Morosos` ya configuradas en MikroTik. Una cuenta de solo lectura permite consultar, pero rechazará cambios. Pertenecer a la lista no demuestra un corte físico: orden de reglas, FastTrack, sesiones abiertas e IPv6 pueden permitir tráfico. El control cubre la IPv4 de la cola simple, no dispositivos o servicios con otras direcciones. Las restricciones compartidas, dinámicas o duplicadas requieren revisión del administrador. Ante un resultado incierto hay que sincronizar antes de reintentar. No hay cortes automáticos por fecha ni registro de pagos.

Se reconocen direcciones individuales, CIDR y rangos IPv4 inclusivos. Una restricción activa compartida/dinámica aplicable o una entrada activa de Morosos que no pueda interpretarse bloquea el cambio individual. Nunca se modifican rangos, subredes ni entradas dinámicas. La misma interpretación se comprueba antes y después de escribir; una respuesta ambigua no confirma éxito.

Cada instalación guarda automáticamente sus localidades y datos en `%LOCALAPPDATA%/SpicyOps`. Las credenciales se cifran y la clave del programa empaquetado se protege con DPAPI de la cuenta Windows. No hay clientes ni conexiones precargados. No se deben compartir esos archivos privados para distribuir el programa.

## Actualización automática por localidad

En **Conexiones**, marca **Actualización automática**, elige **1, 5, 10, 15, 30 o 60 minutos** y pulsa **Guardar** en la localidad. Empieza desactivada, con 5 minutos seleccionados. Para pausar, desmarca y guarda; para reanudar, vuelve a marcar y guardar. La preferencia se conserva cifrada al reiniciar, junto con los accesos. Pausar conserva credenciales, lecturas y notas. Desconectar mantiene la preferencia, cancela la programación efectiva y retira las contraseñas como antes; reconectar permite retomarla.

Cada tarjeta muestra la última lectura exitosa, la próxima actualización y el estado: desactivada, programada, actualizando, esperando reintento o localidad desconectada. Los errores llevan fecha y conservan los últimos datos válidos. **Perfil conectado**, fecha de los datos y resultado de la última operación son señales diferentes: una lectura guardada no acredita disponibilidad actual.

La programación corre en el proceso de Windows, con un solo coordinador por instalación, aunque cierres todas las ventanas y SpicyOps siga en la bandeja. Abrir más ventanas reutiliza la misma instancia. Hay hasta dos lecturas automáticas concurrentes y una sola operación por localidad; si está ocupada, espera sin acumular ciclos. La lectura manual sigue disponible y programa el siguiente ciclo desde su finalización. Ante fallos espera 1, 2 y 4 minutos; después espacia los intentos al menos 15 minutos (o el intervalo elegido si es mayor). Al recuperarse vuelve al intervalo normal. La sincronización automática solo lee: nunca ejecuta Morosos.

Analytics, Clientes y Conexiones incorporan los cambios sin recargar la página completa. Se conserva la consulta de búsqueda, la unidad y la posición de desplazamiento. Mientras escribes, cambias un formulario sin guardar o mantienes una confirmación abierta, la vista espera para no sustituir el borrador; al terminar incorpora la última lectura disponible.

**PC apagada o suspendida:** no se ejecutan lecturas. **SpicyOps cerrado con “Salir de SpicyOps”:** tampoco; el cierre espera que terminen las lecturas en curso y persiste sus resultados. Al abrir de nuevo solo programa localidades conectadas y habilitadas, desde el intervalo elegido y con arranque espaciado. Al volver de suspensión omite ciclos vencidos y hace como máximo una lectura pendiente por localidad, sin reconstruir el historial perdido. No instala un servicio de Windows ni en Raspberry, y no arranca por sí solo al encender la PC.

## Desarrollo

### Diagnóstico de conexión

Conectar, sincronizar y Morosos comparten un presupuesto de **60 segundos** para DNS, conexión, autenticación, envío/ejecución, recepción y cierre SSH; también se comprueba el plazo al validar el inventario. El lector remoto recibe un presupuesto limitado al tiempo restante. Hay como máximo dos resoluciones DNS y cuatro trabajadores SSH pendientes en el proceso, todos daemon: un bloqueo no impide salir ni genera hilos sin límite. Nunca se reintenta una escritura automáticamente; un resultado no confirmado exige sincronizar.

En **Conexiones → Diagnosticar**, cada localidad comprueba acceso al puerto SSH, identidad del equipo, autenticación SSH, Python/librouteros, certificado TLS, lecturas API-SSL e inventario. El progreso aparece por etapa y termina con una orientación concreta. Si una etapa falla, las dependientes quedan como **No comprobada**. Una huella nueva se confirma en **Configurar**; una huella cambiada detiene el acceso y nunca se sustituye automáticamente.

El resultado permanece guardado aparte de la sincronización, con fecha y hora. Al volver a la vista se identifica como histórico; al cambiar la configuración aparece desactualizado. Un inventario vacío válido no es un fallo de conexión. Las colas ambiguas o sin contadores producen advertencias. Diagnosticar no actualiza Analytics ni Clientes, no cambia el estado de conexión y no elimina accesos. En una localidad desconectada puede ser necesario volver a introducir las credenciales retiradas.

El diagnóstico es exclusivamente de lectura: no prueba escrituras ni acredita internet para los clientes. Comparte la exclusión por localidad con sincronización manual/automática, configuración y Morosos. Las demás localidades pueden seguir trabajando. El presupuesto es de 8 segundos por etapa, 25 para las lecturas API y 60 en total; incluye cierre de SSH y recuperación de diagnósticos interrumpidos. La resolución del sistema se espera de forma acotada en un hilo sin credenciales.

Las pruebas controladas están en `portal/tests/test_diagnostics.py` y `portal/tests/test_connector.py`; no usan equipos reales. La validación física Raspberry → MikroTik sigue pendiente.

Dependencias de aplicación en `requirements.txt`; construcción en `requirements-build.txt`. Python usado para construir/probar: 3.12.14. El lector remoto mantiene sintaxis Python 3.11, sin dependencias binarias nuevas en Raspberry.

```powershell
# Ejecutar fuentes (abre la ventana y prepara su estado automáticamente):
.\.venv\Scripts\python.exe run_panel.py
# Tests vigentes; no crean ni usan PostgreSQL:
.\.venv\Scripts\python.exe manage.py test portal.tests --noinput
# Recopilar avisos de terceros antes de empaquetar:
.\.venv\Scripts\python.exe scripts/collect_notices.py
# Reconstruir Windows:
.\.venv\Scripts\python.exe scripts/build_windows.py
# Comprobar correspondencia entre fuentes y paquete oficial:
.\.venv\Scripts\python.exe scripts/check_windows_sources.py
# Distribución oficial aislada (salir de ella antes de reconstruir):
.\.venv\Scripts\python.exe scripts/build_windows.py --dist-dir dist/SpicyOps-1.0.0-Windows --work-dir build/release-1.0.0
.\.venv\Scripts\python.exe scripts/smoke_windows.py --exe dist/SpicyOps-1.0.0-Windows/SpicyOps/SpicyOps.exe
.\.venv\Scripts\python.exe scripts/package_windows.py --folder dist/SpicyOps-1.0.0-Windows/SpicyOps --archive dist/SpicyOps-1.0.0-Windows/SpicyOps-1.0.0-Windows.zip
```

`portal/` contiene interfaz, conector, cálculos y estado privado. `spicyops/portal_settings.py` es la configuración por defecto. Para pruebas de desarrollo se puede elegir otra carpeta privada con `run_panel.py --state-dir RUTA`; nunca usar una carpeta pública.

[Encargo vigente](docs/encargo-panel-conectado.md) · [Verificación del rework](docs/verificacion-panel-conectado.md) · [Guía de agentes](AGENTS.md).

Guía visual de localidades, Tailscale, SSH y API-SSL: [documento editable](docs/guia-visual-conexiones.md) · [PDF histórico con diagramas](output/pdf/SpicyOps-guia-visual.pdf).

## Alcance y estado real

No se ha publicado un sitio web ni se ha instalado el programa en Raspberry. El ejecutable incluye el cliente SSH; requiere acceso de red existente y la configuración de lectura de cada Raspberry/MikroTik. La importación viene de **colas simples RouterOS 6/7**; PPPoE, RADIUS y otros modelos requieren un adaptador distinto. No se acredita compatibilidad física v7 sin probarla.

La edad de una cola/contador no se deduce del uptime. La gráfica descarta comparaciones afectadas por reinicios o resets de contador; sus barras muestran diferencias observadas, no proyecciones ni facturación. No se inventan datos para llenar la interfaz.

Analytics compara subida y bajada entre lecturas consecutivas de la misma época de arranque. Un reset conocido sigue invalidando la aproximación aunque el contador recupere el valor anterior y aunque rote el historial retenido. Al cambiar de router/arranque se inicia otra época; esto no demuestra la edad real de los contadores.

La cuenta de Lulu y su ensayo siguen cerrados según la documentación previa. No se han elevado permisos ni reabierto escrituras. `config-mikro/` y `config-antenasyclientes/` se conservan intactas e ignoradas. El portal cautivo continúa fuera de alcance.

## Documentación histórica

El primer encargo, su arquitectura de tareas y sus verificaciones permanecen en `docs/encargo-mvp-local.md`, `docs/mvp-local.md` y `docs/verificacion-mvp-local.md`. El código `ops/`, `agent/` y la suite `tests/` de esa etapa no están expuestos por el producto nuevo. La base y el simulador ficticios se retiraron; no arrancan con SpicyOps. La suite histórica solo puede ejecutarse con PostgreSQL de pruebas explícito y `--settings=spicyops.settings` más `requirements-legacy.txt`.

Contexto real anterior: [arquitectura](docs/arquitectura.md), [adaptación SpicyNet](docs/adaptacion-spicynet.md), [preparación MikroTik](docs/preparacion-mikrotik.md) y [ensayo cerrado](docs/prueba-cliente-011.md). Son evidencia, no instrucciones para repetir comandos.

Instalación y actualización en Windows limpio: **excluidas expresamente por el usuario**. Se comprueba actualización local con estados temporales sintéticos. Titular, licencia del proyecto y canal de soporte requieren decisión del propietario.
