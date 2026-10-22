# Revisión de consultas y lecturas — 22 de octubre de 2026

Se revisó el producto Windows en `portal/`, siguiendo AGENTS.md, README y el encargo vigente. El único cambio de producción está en `portal/telemetry.py:estimate_uptime`. No se accedió al estado privado, credenciales, carpetas sensibles ni equipos reales. No se añadieron dependencias ni PostgreSQL.

## Problema comprobado y cambio

Antes, por cada cliente actual se recorría el historial hacia atrás y se buscaba su fingerprint secuencialmente en los clientes de cada lectura. En un inventario estable de C clientes y H lecturas, el trabajo era O(H × C²). Esto ocurría también en cada petición de actualización HTML de Analytics.

Ahora se recorre el historial una vez, de reciente a antiguo. Para cada lectura se crea un índice temporal por fingerprint y se comprueban únicamente las filas cuya estimación aún no fue descartada. Se libera el índice al avanzar: O(H × C) para inventarios de tamaño estable, con memoria adicional proporcional a una lectura, sin una caché histórica persistente. `setdefault` mantiene la primera coincidencia igual que la búsqueda anterior.

Se conservan el orden de clientes, la primera causa de exclusión encontrada, el límite de época de arranque, la comparación separada de subida/bajada y el mínimo de uptime. La fórmula sigue usando exclusivamente contador/uptime. No se modifican lecturas, historial ni metadatos. La gráfica conserva su recorrido independiente de las últimas 13 lecturas.

## Referencia reproducible

Baseline Git: `8b73d789e8ac63775bdeb4821aca9caa5208d19c`. Python 3.12.14 en Windows. Mediana de cinco ejecuciones tras calentamiento; ambos algoritmos usan exactamente los mismos objetos sintéticos. El script carga el algoritmo anterior desde Git y lo compara con las fuentes actuales. Los tiempos son observaciones locales sujetas a carga del equipo; el conteo de registros es determinista. No se acredita una mejora de latencia de red.

Resultados completos en [benchmark-lecturas.json](benchmark-lecturas.json):

| Clientes | Lecturas | Cálculo antes (ms) | Después (ms) | Registros recorridos antes | Después |
|---:|---:|---:|---:|---:|---:|
| 20 | 120 | 4.065 | 1.239 | 25 010 | 2 400 |
| 100 | 240 | 97.841 | 12.887 | 1 207 050 | 24 000 |
| 300 | 240 | 795.962 | 38.657 | 10 791 150 | 72 000 |
| 100 | 1440 | 866.694 | 78.058 | 7 267 050 | 144 000 |

Petición completa mediante el cliente de pruebas Django: dos localidades, cada una con 100 clientes y 240 lecturas. Incluye carga del archivo, descifrado, JSON, cálculos y renderizado. Cada petición lee el estado una vez y no llama al conector.

| Vista | Antes (ms) | Después (ms) | Bytes HTML después |
|---|---:|---:|---:|
| Analytics de una localidad | 328.720 | 196.023 | 49 928 |
| Clientes / Todos | 245.990 | 258.761 | 731 351 |
| Conexiones | 176.623 | 176.061 | 10 387 |

La mejora atribuible es la de Analytics (aproximadamente 40% en esta carga completa y 95% en el cálculo de 300 clientes). Clientes y Conexiones no ejecutan el algoritmo modificado: sus fluctuaciones no se presentan como mejoras ni como regresiones causadas por este cambio. El HTML anterior y posterior coincide byte por byte en las tres vistas, normalizando únicamente la máscara CSRF aleatoria de Django.

## Recorrido completo y decisiones

| Tramo / funciones | Hallazgo y decisión |
|---|---|
| `app.js:updatePanel` → vistas | Una petición HTML cada 5 segundos por ventana, con exclusión de peticiones solapadas. Se descarga y renderiza incluso si no cambió la revisión; el navegador descarta entonces el reemplazo. Hay transferencia local prescindible, especialmente en Clientes / Todos. Se conserva: una respuesta condicional requiere definir y probar una revisión que cubra todos los datos visibles y formularios; no se añade ese protocolo a este cambio acotado. No se disminuye la frecuencia. |
| `profiles_context`, `clients`, `connections` | Una lectura completa por petición normal. Clientes copia solo los clientes de la última lectura de cada localidad elegida y aplica metadatos/búsqueda. Conexiones usa los perfiles y puede recuperar un diagnóstico interrumpido mediante una actualización adicional. No se encontraron búsquedas cuadráticas del historial en estas vistas. |
| `analytics`, `estimate_uptime` | Búsqueda histórica cuadrática demostrada y corregida. Las barras ya indexaban la lectura anterior y solo usan hasta 12 intervalos; no se cambian. |
| `Coordinator.tick` | Lee todo el estado una vez cada segundo, incluso sin localidades automáticas vencidas. En el estado sintético: 177.485 ms por tick sin trabajo. Es un coste real que permanece. Evitarlo mediante caché o calendario propio exige invalidación de cambios de otras operaciones/procesos; no se introduce esa complejidad ni riesgo de usar configuración antigua. |
| `refresh_profile`, `_refresh_profile` | Una llamada al conector y dos lecturas/reescrituras de estado: reclamar la operación y persistir el resultado. La ejecución automática añade una lectura previa para revalidar conexión, preferencia y vencimiento. El benchmark confirma 2 y 3 lecturas respectivamente, con una llamada al conector en ambos casos. Se conservan exclusión, generación, límites y revalidaciones. |
| `connect`, diagnóstico, configuración, Morosos | Hay lecturas de perfil/pending/contexto y actualizaciones de progreso además del resultado final. Se mantienen las comprobaciones de operaciones en curso y generación. El diagnóstico no sustituye lecturas del inventario ni publica resultados como una sincronización. No se cambian estas rutas. |
| `Store._read`, `_write`, `update` | El JSON cifrado engloba todas las localidades e historiales: cada lectura descifra todo y cada actualización vuelve a serializar/cifrar/persistir todo bajo el bloqueo. Archivo sintético de 21 250 788 bytes: lectura completa 183.471 ms; actualización sin cambios 383.714 ms. Los tiempos incluyen E/S; no son mediciones aisladas de Fernet. Se conserva cifrado, bloqueo, fsync y reemplazo atómico. Particionar/migrar almacenamiento o reutilizar objetos mutables supone un alcance y riesgo mayor. |
| `connector.collect` | Una sesión SSH por operación, pin por localidad, autenticación, carga del lector y ejecución acotada por stdin. No se observó una segunda sesión para la sincronización normal. Se mantienen presupuesto, cierre, límite de respuesta y validación de huella. No se midió latencia Raspberry/Tailscale real. |
| `remote_reader.collect` | El doble de lecturas aparentes tiene propósito: configuración y estadísticas de colas se fusionan por ID; el test remoto comprueba estadísticas ausentes en configuración. Uptime antes/después detecta reinicio durante lectura. La API controlada confirma seis `/print`: recurso, identidad, colas/configuración, colas/stats, address-list, recurso/uptime. Una fila sintética produce 351 bytes de JSON. `.proplist` ya limita columnas. No se fusionan ni eliminan lecturas sin evidencia física de equivalencia RouterOS 6/7. |
| `normalize`, `change_morosity` | La normalización recorre restricciones por cliente y vuelve a interpretar redes: coste potencial O(clientes × restricciones), dependiente del inventario. No fue el cuello medido de Analytics. No se cambian las reglas de pertenencia ni se filtra la respuesta API en remoto, lo que requiere comparación propia de subredes, restricciones inválidas/compartidas y límites de inventario. Morosos conserva inventario reciente, confirmación y lectura posterior; esa lectura adicional no es redundante. |

No se ofrece una aceleración de sincronización SSH/API: el cambio afecta al procesamiento local posterior al guardar los datos. El archivo global y el HTML completo siguen limitando la escala; las mediciones se dejan disponibles sin introducir una reforma del almacenamiento o del protocolo de actualización.

## Verificación ejecutada

- 78 pruebas de `portal.tests`: correctas. Incluyen UI vacía, persistencia cifrada, aislamiento con IP repetidas, metadatos, resets, reinicios, exclusión de operaciones, concurrencia, reintentos y diagnósticos/Morosos contra adaptadores controlados o SSH loopback.
- Cuatro pruebas nuevas de estimaciones: orden y no mutación, prioridad de causa, límite de arranque y reset por dirección, contadores anteriores desconocidos y prioridad de ambigüedad.
- 161 comparaciones reproducibles con el algoritmo anterior: historias aleatorias de semilla fija y caso vacío, además de las cuatro cargas estables del benchmark. Se verifica igualdad exacta de filas/resumen y ausencia de mutación del historial.
- Comparación HTML de las tres vistas y conteos de lecturas manual/automática/API con estado sintético y mocks sin red externa.
- `pip check`: correcto. `git diff --check`: correcto.
- Construcción PyInstaller 6.19.0 en `dist/lecturas-optimizadas`, sin reemplazar salidas previas.
- `check_windows_sources.py`: módulos empaquetados iguales a fuentes, recursos iguales y ausencia de archivos privados.
- `smoke_windows.py` sobre el EXE real: arranque vacío, DPAPI, reapertura de instancia, persistencia, diagnóstico de puerto rechazado, actualización automática SSH loopback sin ventanas y preferencias tras reinicio. Correcto.
- ZIP aislado generado, 33.3 MB; sin perfiles ni estado privado.

La primera ejecución restringida de la suite no pudo usar sockets locales (`WinError 10013`); las pruebas se repitieron con permiso para loopback y terminaron correctamente. No se modificó el conector para ocultar esos fallos del entorno.

## Reproducir

Los comandos siguientes usan datos sintéticos y el benchmark elige su propio directorio temporal antes de cargar Django. La suite y construcción también usan una carpeta nueva con clave sintética, sin abrir el estado de desarrollo. El smoke usa carpetas temporales propias para el EXE y otra carpeta nueva para su proceso de pruebas; requiere sockets loopback.

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_portal_reads.py --baseline-ref 8b73d789e8ac63775bdeb4821aca9caa5208d19c --repeats 5 --output docs/benchmark-lecturas.json
$env:SPICYOPS_STATE_DIR = Join-Path (Get-Location) '.local/tmp/performance-tests'
$env:DJANGO_SECRET_KEY = 'isolated-synthetic-test-key'
.\.venv\Scripts\python.exe manage.py test portal.tests --noinput
.\.venv\Scripts\python.exe -m pip check
$env:SPICYOPS_STATE_DIR = Join-Path (Get-Location) '.local/tmp/performance-build'
.\.venv\Scripts\python.exe scripts/build_windows.py --dist-dir dist/lecturas-optimizadas --work-dir build/lecturas-optimizadas
.\.venv\Scripts\python.exe scripts/check_windows_sources.py --folder dist/lecturas-optimizadas/SpicyOps --workpath build/lecturas-optimizadas/SpicyOps
Remove-Item Env:DJANGO_SECRET_KEY
$env:SPICYOPS_STATE_DIR = Join-Path (Get-Location) '.local/tmp/performance-smoke-host'
.\.venv\Scripts\python.exe scripts/smoke_windows.py --exe dist/lecturas-optimizadas/SpicyOps/SpicyOps.exe
.\.venv\Scripts\python.exe scripts/package_windows.py --folder dist/lecturas-optimizadas/SpicyOps --archive dist/lecturas-optimizadas/SpicyOps-Windows.zip
```

Validación física Raspberry → API-SSL MikroTik pendiente. Los mocks de TLS/API y el SSH loopback no acreditan latencia de red, compatibilidad física RouterOS 7, estado de clientes reales ni cortes/reconexiones de internet.
