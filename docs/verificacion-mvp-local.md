> ARCHIVO HISTÓRICO DEL PRIMER ENCARGO. El usuario sustituyó el producto manual/simulado por SpicyOps para Windows. Ver [encargo vigente](encargo-panel-conectado.md) y [README](../README.md). Las pruebas anteriores no acreditan la conexión física ni describen la interfaz actual.

# Verificación del primer MVP local

Ejecutada el **16/10/2026**, zona America/Mexico_City, en este equipo Windows. Todo el trabajo fue local y con datos ficticios. No son resultados de la red SpicyNet.

## Entorno comprobado

| Componente | Versión / uso |
|---|---|
| Python | 3.12.14, entorno `.venv` del proyecto |
| Django | 5.2.18 |
| psycopg | 3.3.6, binario para Windows del servidor central |
| PostgreSQL | 18.6, binarios ya instalados; clúster nuevo en `.local/pgdata` |
| Agente | Biblioteca estándar; modo simulador, proceso independiente |
| Router simulado | Configuración y reportes en SQLite persistente |
| Red de pruebas | HTTP exclusivamente loopback; PostgreSQL 127.0.0.1:55432 |

## Suite ejecutada

Comando real: `.\.venv\Scripts\python.exe manage.py test tests --noinput -v 1`.

Resultado final: **39 pruebas, 93.699 segundos, OK**, con creación/migración/eliminación de la base PostgreSQL independiente `test_spicyops`. Sin pruebas omitidas. Hubo una primera ejecución con errores de limpieza de archivos SQLite en Windows; se corrigió el cierre de conexiones del simulador y las repeticiones posteriores finalizaron correctamente.

| Grupo | Cantidad | Evidencia |
|---|---:|---|
| Unitarias del simulador/contrato | 10 | Repetición de acciones, protección de destinos, unicidad/objetos ajenos, revisiones, política, orden/burst no cero, HTTPS y bloqueo físico |
| Integración PostgreSQL | 18 | Transacción intención/tarea, dos consumidores en conexiones reales distintas, SKIP LOCKED, exclusión por router, recuperación de concesión, revisiones, vencimiento, reportes y permisos |
| Panel + API HTTP + procesos de agente | 11 | Alta administrativa desde vista, cuatro acciones mediante agente CLI real, reinicios/fallos del proceso, bandeja durable, CSRF, login, aislamiento, IP duplicada y validación local independiente de inventario |

Los bloqueos **no** se acreditaron con SQLite ni mocks. La prueba concurrente abre dos conexiones PostgreSQL, comprueba distintos `pg_backend_pid()` y exige una sola concesión válida. Otra prueba mantiene el router bloqueado desde una conexión y verifica que la segunda lo omite.

La prueba HTTP usa servidor Django real de pruebas y subprocess del agente. Las cuatro acciones se solicitan desde las vistas del panel; cada resultado observado se compara con una lectura del estado persistente del simulador. La alta administrativa crea cliente y servicio separados.

Fallos comprobados: antes de escribir (sin falso observado); después de escribir (reintento sin duplicar); salida abrupta del proceso después de commit y antes de guardar reporte (vencimiento y nuevo intento); reinicio con reporte en bandeja (lectura nueva antes de reenviar); cambio del simulador mientras hay reporte pendiente (no acreditar estado antiguo); reporte repetido y reporte cambiado.

## Recorrido visible y reinicio completo adicional

Se inició el panel en `http://127.0.0.1:8000/` y el agente simulado en segundo plano. En el navegador se inició sesión con el usuario ficticio y se ejecutaron sobre **Marina Ejemplo / 198.51.100.20**:

| Revisión | Operación | Resultado leído y persistido |
|---:|---|---|
| 1 | Alta técnica | Activo, 2000/4000 kbps |
| 2 | Suspensión | Suspendido, conserva 2000/4000 kbps |
| 3 | Reactivación | Activo, 2000/4000 kbps |
| 4 | Cambio a Ampliado | Activo, 5000/10000 kbps |

Se observó primero cada intención pendiente con el estado observado anterior; solo tras reportar el agente apareció “Verificada”. El historial conserva actor, motivo y eventos. Se revisó la disposición de escritorio y una vista de **390 px** en iframe: tarjetas apiladas, controles táctiles, textos y banner de simulación. Esto es revisión del navegador, no una prueba en teléfono físico. Capturas locales ignoradas por Git: `.local/qa/escritorio.png`, `.local/qa/mobile.png` y `.local/qa/estado-verificado.png`.

Después se detuvo el agente, se creó una tarea pendiente para **Recuperación Ejemplo / 198.51.100.22**, y se detuvieron/reiniciaron los **tres procesos: PostgreSQL, Django y agente** mediante `local.ps1 stop` y `local.ps1 demo`. La comprobación posterior exigió:

- PID de PostgreSQL distinto, sin borrar ni recrear datos.
- Los cuatro resultados y el observado de Marina idénticos a la referencia anterior.
- La tarea que estaba pendiente recuperada y verificada.
- Resultado central igual a lectura del mismo archivo persistente del simulador.

Resultado: **OK**. La evidencia estructurada está en `.local/restart-proof.json`, sin credenciales. Los procesos locales del panel y agente quedan iniciados para revisión; no se instaló ningún servicio de sistema.

También se ejecutaron `manage.py check` (sin problemas), `makemigrations --check --dry-run` (sin cambios), compilación de módulos y `pip check` (sin dependencias rotas). Se comprobó el arranque de un paso, parada y nuevo arranque mediante `scripts/local.ps1`. El agente se analizó con la gramática Python 3.11; no se ejecutó un intérprete 3.11 ni hardware ARMv6.

## Límites explícitos

No se hizo despliegue público, copia/restauración de backup PostgreSQL, instalación systemd, prueba de RAM en Raspberry, conexión TLS física RouterOS, escritura en equipos ni prueba de tráfico/velocidad desde un cliente. El adaptador físico tiene transporte/lectura preparados, pero la aplicación de cambios continúa bloqueada y pendiente de implementación/verificación autorizada. No hay evidencia física de compatibilidad v7.

No se accedió a las carpetas sensibles ni se copiaron secretos reales. `.local/`, `.venv/` y ambas carpetas de configuración están excluidas de Git; el estado de estas exclusiones se comprobó. El portal cautivo no se intervino.

