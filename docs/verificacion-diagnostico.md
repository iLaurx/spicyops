# Diagnóstico por etapas — 22 de octubre de 2026

Implementación en `portal/`, integrada en cada localidad de Conexiones. El diagnóstico reutiliza `connector.collect` y el lector efímero, con eventos estructurados para las siete etapas. No guarda muestras en Analytics o Clientes, no cambia el estado observado de conexión y no prueba escrituras. Las huellas nuevas remiten a la confirmación existente en Configurar; las cambiadas detienen el acceso.

Los resultados quedan cifrados dentro del estado privado, separados de sincronización. Incluyen fecha, estados por etapa, códigos seguros, orientación y resumen. Se conservan al navegar y reiniciar, se identifican como históricos y se marcan desactualizados al configurar o desconectar. Los diagnósticos interrumpidos se recuperan como error con sus dependencias no comprobadas.

Se comparte la exclusión de operaciones por localidad con lectura manual, coordinador automático, configuración, desconexión y Morosos. Diagnosticar no altera la programación automática. Una localidad ocupada no bloquea las demás. No se aceptan parámetros de conexión o comandos desde el botón del navegador.

## Pruebas ejecutadas

- `manage.py test portal.tests --noinput`: 73 pruebas aprobadas. Incluyen resolución fallida, puerto rechazado, timeout, huellas nuevas/cambiadas, autenticación, Python y dependencia ausentes, CA/TLS, rechazo API, formato incompleto, versión no contemplada, inventario vacío, contadores ausentes y colas ambiguas.
- Presupuestos de tiempo, etapas omitidas, cierre SSH/TLS/API, mensajes sin secretos, persistencia, recuperación, CSRF, duplicados, exclusión e independencia de localidades. Se ejecutó el bootstrap y lector reales contra un servidor SSH temporal en esta PC para los casos de intérprete y CA ausentes.
- `pip check`: dependencias compatibles. El lector se analizó con la gramática Python 3.11. Compilación de fuentes y `git diff --check` sin errores.
- Interfaz revisada en navegador local con respuestas controladas: progreso, botón deshabilitado mientras trabaja, error TLS, etapas dependientes no comprobadas y resumen. A 390 píxeles de ancho, el contenido no desborda horizontalmente. Evidencia en `output/diagnostico/conexiones-movil.png`; solo contiene datos ficticios de prueba.
- Ejecutable Windows: arranque vacío, rutas y recursos, apertura protegida, DPAPI, persistencia tras reinicio, sincronización automática con SSH temporal de loopback y diagnóstico de puerto rechazado en loopback. Se confirmó que el diagnóstico conserva historial y estado de conexión.
- `check_windows_sources.py`: módulos compilados, plantillas, recursos y lector coinciden con las fuentes finales. La distribución no contiene perfiles, claves de estado ni archivos privados.

Las advertencias de sockets cerrados durante las pruebas corresponden al servidor SSH efímero y a los rechazos o límites de tiempo intencionales.

## Distribución comprobada

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --distpath dist/diagnostico --workpath build/diagnostico-verificado SpicyOps.spec
.\.venv\Scripts\python.exe scripts/check_windows_sources.py --folder dist/diagnostico/SpicyOps --workpath build/diagnostico-verificado/SpicyOps
.\.venv\Scripts\python.exe scripts/smoke_windows.py --exe dist/diagnostico/SpicyOps/SpicyOps.exe
.\.venv\Scripts\python.exe scripts/package_windows.py --folder dist/diagnostico/SpicyOps --archive dist/SpicyOps-diagnostico-Windows.zip
```

La carpeta portable conserva `_internal` junto a `SpicyOps.exe`. Se construyó aparte sin interrumpir instancias del usuario.

## Límite de la verificación

Todas las conexiones de desarrollo fueron de loopback en esta PC. No se conectaron Raspberry ni MikroTik reales, ni se leyeron carpetas sensibles. No se ejecutaron acciones físicas de Morosos, instalaciones remotas, cambios de permisos, firewall, planes, contadores o reinicios. La compatibilidad y conexión física por localidad siguen pendientes. Un diagnóstico correcto acredita acceso y lectura Raspberry → MikroTik; no acredita internet para los clientes.
