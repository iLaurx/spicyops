# Revisión para publicación · 25 de octubre de 2026

## Dictamen

Windows: candidato local, pendiente de corregir el mínimo de intervalo en Analytics y resolver los pendientes de lanzamiento indicados abajo. Guía web: comprobaciones locales aprobadas; falta elegir destino y verificar el despliegue público. No se publicó ninguno de los dos productos.

## Hallazgo reproducido

**Prioridad media: Analytics acepta intervalos insuficientes.** `portal/views.py`, función `analytics`, agrega barras siempre que `same_boot` sea verdadero. `portal/telemetry.py`, función `same_boot`, acepta cualquier intervalo positivo compatible con el uptime. Con dos lecturas ficticias separadas cinco segundos, uptime 100 → 105 y contadores 100/100 → 150/150, la vista devuelve una barra. README e interfaz indican esperar al menos un minuto; el encargo exige invalidar intervalos insuficientes. Antes de publicar, filtrar el intervalo en la gráfica sin cambiar la detección de reinicios utilizada por las estimaciones. Verificar los límites de menos de 60 segundos y de 60 segundos o más.

## Windows: verificación actual

- Dependencias instaladas: `pip check` sin incompatibilidades. `manage.py check` sin incidencias. No se realizó auditoría de vulnerabilidades Python.
- Compilación real con `scripts/build_windows.py`: correcta, Python 3.12.14 y PyInstaller 6.19.0. Avisos de importaciones opcionales/excluidas durante la construcción; no impidieron el arranque comprobado.
- Ejecutable real con `--no-open` y datos temporales aislados: arranque correcto; acceso sin sesión rechazado; Analytics, Clientes, Conexiones, formulario de nueva localidad y Respaldos responden correctamente; CSS y JS disponibles; clave protegida con DPAPI; salida ordenada con código cero. No se abrió la ventana Edge ni se ejercitó el menú nativo de bandeja en esta comprobación.
- Comprobaciones directas desde las fuentes con datos ficticios aislados: pantallas vacías, protección CSRF, persistencia cifrada, metadatos separados entre dos localidades, exportación/importación portable, rechazo de contraseña incorrecta, restauración desconectada, conservación del original y pantalla de recuperación ante corrupción.
- Se recopilaron avisos y licencias desde las dependencias instaladas. El script de empaquetado comprueba ZIP, manifiesto SHA-256 y exclusión de nombres de estado privado. La recopilación no sustituye una revisión jurídica de licencias.
- Empaquetado completado: ZIP de 35,668,855 bytes y 4,469 archivos, `testzip` correcto y cada entrada contrastada con el manifiesto. SHA-256 del ZIP: `d4c8faec771cd41d14b2d92a0d7df8fdb429e40e9bb1101643cf3293ebfe1a0d`. SHA-256 del EXE: `23e24ad835c1ece3095d52ad459271e0a5c1a103bcfda6afb02d0a26ee96578b`. Manifiesto: `dist/SpicyOps-1.0.0-Windows/integridad.json`. Es un candidato que conserva el hallazgo descrito, no una versión aprobada para lanzamiento.
- No se restauraron las suites ni los simuladores históricos retirados. No se repitió SSH en loopback, las acciones Morosos ni la matriz completa de cálculos. Las comprobaciones actuales son parciales.

El arranque inicial del EXE y Edge falló dentro del entorno restringido; ambos se comprobaron después fuera de esa restricción, con datos de prueba y servicios locales.

## Guía web: verificación actual

- `npm run build`: correcto; incluye TypeScript y distribución de producción con base `/`.
- `npm test`: siete pruebas aprobadas.
- `python scripts/check_python.py`: un bloque Python analizado; lector descargable limitado a cuatro rutas `/print` y validación TLS.
- `npm audit --omit=dev`: cero vulnerabilidades reportadas en la consulta de esta revisión. Las dependencias del proyecto están declaradas en `dependencies`.
- `node scripts/browser-check.mjs`: correcto en Edge con la distribución actual. Vistas de 360, 430, 768, 1024 y 1440 px; reflujo equivalente al 200%; búsqueda, anclas, progreso opcional, configurador, copiado, descargas, impresión, enlace de salto y contenido sin JavaScript. Sin errores de página, respuestas HTTP fallidas ni peticiones externas en el recorrido probado.
- Se adaptó la prueba de navegador a las secciones desplegables y a los conteos actuales: 17 secciones y 36 bloques. Se revisó visualmente la captura móvil de 360 px.
- Evidencia actual: `web/evidence/browser-results.json`, capturas y PDF. La evidencia de subruta de revisiones anteriores no se regeneró en esta revisión.

## Pendientes de lanzamiento

- Corregir y verificar el hallazgo de Analytics antes de considerar Windows listo.
- EXE sin firma digital. Definir distribución y canal de soporte. El repositorio mantiene cambios locales sin confirmar y archivos nuevos; fijar una revisión identificable para la entrega.
- Piloto físico Raspberry/MikroTik y efecto de las reglas Morosos sin verificar. Compatibilidad física de RouterOS 7 sin acreditar. No se contactaron equipos ni se leyeron carpetas sensibles.
- Windows limpio excluido por la documentación vigente; no se presenta como validado. Menú nativo, suspensión real, teléfono físico, lector de pantalla y otros navegadores no comprobados aquí.
- Web: elegir alojamiento, repositorio y URL. Publicar únicamente `web/dist`; la aplicación Windows es local y no debe hospedarse como portal público. El workflow Pages continúa como plantilla inactiva. Tras el despliegue, comprobar HTTPS, rutas, recursos, descargas y móvil en la URL final.

Los resultados no equivalen a una auditoría completa de seguridad, compatibilidad o accesibilidad.
