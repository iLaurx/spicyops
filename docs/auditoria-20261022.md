# Auditoría corregida — 22 de octubre de 2026

Producto Windows vigente en `portal/`. Se leyeron AGENTS, README y el encargo conectado. El árbol estaba limpio al comenzar; no se descartaron cambios del usuario. No se implementó el punto 6, respaldos ni recuperación de archivos corruptos. No se leyeron las carpetas sensibles ni se usaron accesos existentes. Todo el inventario, las credenciales de pruebas y las restricciones son ficticios; SSH se probó únicamente en loopback.

## Correcciones

1. **Morosos:** `router_contract.py` interpreta IPv4, CIDR y rangos con extremos inclusivos. El mismo contrato se ejecuta en Windows y en el lector enviado por stdin. La normalización informa restricciones no interpretables; la validación previa y la confirmación posterior rechazan restricciones activas compartidas/dinámicas aplicables, desconocidas y duplicados individuales. Un rango de un solo elemento sigue siendo un rango y no puede modificarse. Solo se agrega/habilita/deshabilita una entrada individual estática de la lista fija `Morosos`. No se tocan subredes, rangos ni dinámicas. Un fallo de escritura, timeout o confirmación guarda error y bloquea otra acción hasta sincronizar. No hay reintentos de escrituras.

2. **Analytics:** compara cada dirección del contador con la lectura consecutiva, dentro de la misma identidad y época de arranque. `1000 → 100 → 1200` continúa invalidado. Se conserva el motivo en las siguientes lecturas para no olvidarlo al rotar las 1440 muestras. La primera lectura tras actualizar una instalación antigua revisa el historial retenido una vez; las siguientes trasladan la validez en O(clientes). Se mantienen exclusiones por identidad modificada/cola nueva, ambigüedad, falta de contador actual y mínimo de uptime. No se deduce una edad real: las cifras válidas siguen siendo aproximaciones por uptime. No se reconstruyen resets no observados o anteriores al historial disponible.

3. **Inventario:** en Clientes, **Revisar colas excluidas** muestra nombre/ID, IP/destino y motivo; **Incluir en Clientes** y **Revertir inclusión** cambian una excepción local. Solo se acepta una cola individual válida excluida por la heurística `RESERVED`. Se conserva el filtro predeterminado. La excepción cifrada se vincula a localidad, ID, IP y nombre de cola; otra identidad/dirección no la hereda. El formulario solo selecciona una huella y lectura observadas; la elegibilidad la decide el servidor. Se rechazan destinos compartidos/múltiples, IPv6, duplicados, colas inválidas/deshabilitadas y datos no válidos. Una excepción se aplica a Clientes/Analytics y viaja desde el perfil privado al lector, que revalida inventario y datos antes de Morosos. No se crea ningún cliente manual ni se inventan IP, planes o contadores. Las lecturas antiguas sin el detalle requieren sincronización.

4. **Conexión:** conectar, sincronizar, diagnosticar y Morosos comparten la resolución acotada, sockets ya resueltos y un plazo global de 60 s que incluye autenticación, ejecución, recepción y cierre. Diagnóstico conserva 8 s por etapa y 25 s de API, dentro del global. Cada dirección recibe parte del presupuesto disponible y se prueban las siguientes si falla. El bootstrap remoto recibe un plazo relativo al restante, con máximo de 45 s. La espera exterior incluye incluso un cierre SSH bloqueado; al expirar cancela la operación local y cierra el socket. Se limita a dos resolutores y cuatro trabajadores SSH daemon por proceso, sin cola creciente. Un trabajador irrecuperable conserva su cupo hasta terminar o salir del programa. La PC puede salir aunque DNS no vuelva. Se conservan huella SSH, CA/hostname TLS y ausencia de comandos libres del navegador.

5. **Coordinador:** cada tick consulta una instantánea pequeña de programación sin credenciales ni historial. La firma `(mtime_ns, ctime_ns, tamaño, identidad de archivo)` se verifica bajo el mismo bloqueo del estado. Un reemplazo/cambio del archivo invalida la instantánea, incluso si procede de otra instancia de Store. Solo el tick que detecta un cambio vuelve a descifrar. Antes de ejecutar se vuelve a leer y comprobar conexión, pausa, vencimiento y ocupación; la reclamación carga el perfil vigente. Se mantienen una operación por localidad, hasta dos lecturas automáticas concurrentes, generaciones, metadatos, historial y resultados.

## Medición antes/después

Primero se midió el comportamiento original con `benchmark_portal_reads.py`: [medición inicial](auditoria-antes.json). Después se comparó la misma carga sintética en `benchmark_audit.py`, usando como referencia fija `3aba44f62b7a1f91d80dd696765c3c7c9356feb3`. Medianas de cinco repeticiones, Python 3.12.14, sin red real. [Datos completos](auditoria-mediciones.json).

| Escenario idéntico | Antes | Después |
|---|---:|---:|
| Tick inactivo, 2 localidades × 100 clientes × 240 lecturas, archivo cifrado 21 250 636 bytes | 251,451 ms; 1 descifrado/tick | 1,496 ms; 0 descifrados tras cargar |
| Analytics: 20 clientes × 120 lecturas | 1,225 ms | 0,752 ms |
| Analytics: 100 clientes × 240 lecturas | 13,039 ms | 10,077 ms |
| Analytics: 300 clientes × 240 lecturas | 41,268 ms | 23,368 ms |
| Analytics: 100 clientes × 1440 lecturas | 74,970 ms | 45,473 ms |

Analytics conserva exactamente 2400/24000/72000/144000 visitas de clientes en esas cargas; no vuelve a una búsqueda cuadrática. Se comprueba igualdad de resultados para historias sin los fallos corregidos. Las regresiones de resets sí cambian deliberadamente el resultado.

**Coste que permanece:** el archivo cifrado sigue siendo único. La primera consulta y la primera posterior a cualquier cambio leen todo el archivo; las páginas y operaciones que requieren el estado completo también. Una actualización sin cambios costó 479,086 ms en esta carga. Guardar notas, progreso de diagnóstico o resultados todavía serializa/cifra/persiste todo bajo el bloqueo, y después invalida la instantánea. No se particionó el almacenamiento ni se añadió una base de datos o servicio. El detalle de inventario se conserva solo para candidatas de infraestructura, sin duplicar todos los clientes en cada muestra. Los tiempos son locales y variables; no acreditan menor latencia de Raspberry/Tailscale/API.

## Verificación

- **98 pruebas correctas** en `portal.tests`, sin PostgreSQL. Se agregaron 20 regresiones a las 78 existentes: rangos/extremos, individual más rango, CIDR, desconocidas, dinámicas/duplicados, confirmación sobrevenida, errores de escritura, resets por dirección y recuperación, límite de arranque/rotación, excepciones/persistencia/reversión/identidad/IP/localidad, POST falsificado/obsoleto, presupuesto global y cupos, DNS bloqueado, varias direcciones, autenticación/cierre bloqueados, salida del proceso con DNS permanentemente atascado e invalidación de programación. Las pruebas anteriores siguen cubriendo concurrencia automática y operaciones concurrentes de notas/configuración/Morosos.
- `pip check` correcto y revisión de diferencias sin errores de espacios. Sintaxis del contrato y lector comprobada con el parser Python 3.11.
- Revisión visual de Analytics, Clientes y Colas excluidas con estado sintético propio. Se verificó que el rango muestra restricción y deshabilita el cambio individual; la cola compartida ofrece revisión, sin botón de inclusión. El inventario se revisó en escritorio y en un marco de **390 px**, con tarjetas, texto ajustado y botones accesibles sin desplazamiento horizontal. El servidor auxiliar de QA se cerró al terminar.
- Construcción PyInstaller en una carpeta aislada. `check_windows_sources.py` verifica módulos compilados, plantillas, CSS/JS, lector y contrato compartido contra las fuentes, además de ausencia de estado privado y módulos de tests.
- `smoke_windows.py` ejecuta **el EXE**: instalación vacía, navegación/recursos, sesión/CSRF, instancia única, DPAPI, persistencia, inclusión/reversión mediante HTTP, diagnóstico de puerto rechazado, autolectura por SSH loopback sin ventanas y preferencias tras reiniciar. No envía escrituras a ningún router. DPAPI no estaba disponible en el primer entorno restringido; el smoke se repitió con ejecución local permitida y terminó correctamente, sin modificar el cifrado.

## Entrega y reproducción

Ejecutable: `dist/auditoria-20261022/SpicyOps/SpicyOps.exe`. ZIP portable: `dist/auditoria-20261022/SpicyOps-Windows.zip`. Se conserva `_internal` junto al ejecutable. Las distribuciones anteriores y las instancias del usuario no se sustituyeron ni se cerraron. El ZIP no contiene perfiles, lecturas, claves, configuración privada ni fixtures de tests.

Se compararon por SHA-256 los **4397 archivos** del ZIP contra la carpeta final y se comprobó la integridad de la compresión. ZIP de 34 922 441 bytes (33,3 MiB). [Registro de integridad y hashes del EXE/ZIP](auditoria-paquete.json).

```powershell
$env:SPICYOPS_STATE_DIR = Join-Path (Get-Location) 'build/audit-tests/bootstrap'
$env:DJANGO_SECRET_KEY = 'audit-synthetic-key'
.\.venv\Scripts\python.exe manage.py test portal.tests --noinput
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/benchmark_audit.py
.\.venv\Scripts\python.exe scripts/build_windows.py --dist-dir dist/auditoria-20261022 --work-dir build/auditoria-20261022
.\.venv\Scripts\python.exe scripts/check_windows_sources.py --folder dist/auditoria-20261022/SpicyOps --workpath build/auditoria-20261022/SpicyOps
Remove-Item Env:DJANGO_SECRET_KEY
$env:SPICYOPS_STATE_DIR = Join-Path (Get-Location) 'build/audit-tests/smoke-bootstrap'
.\.venv\Scripts\python.exe scripts/smoke_windows.py --exe dist/auditoria-20261022/SpicyOps/SpicyOps.exe
.\.venv\Scripts\python.exe scripts/package_windows.py --folder dist/auditoria-20261022/SpicyOps --archive dist/auditoria-20261022/SpicyOps-Windows.zip
```

**Pendiente físico:** conexión Raspberry → MikroTik real y resultado del bloqueo/restauración de tráfico con su firewall. No se conectaron equipos reales, no se reabrió Lulu, no se cambiaron permisos/reglas/servicios ni se instalaron archivos remotos. La pertenencia a Morosos sigue sin demostrar corte o reconexión física.
