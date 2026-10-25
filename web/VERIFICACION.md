# Verificación local — 24 de octubre de 2026

## Entrega

Guía estática implementada en `web/`: once etapas completas, 16 secciones, 37 bloques de código, dos recorridos, configurador local sin secretos, búsqueda, navegación por anclas, progreso opcional, impresión y recursos descargables. Diseño crema/navy/turquesa, fuentes locales con licencia y SVG original de los tres equipos. El programa Windows y WEB.md, DESING.md y CONNECTION.md se conservaron. Se añadió al README raíz una referencia de arranque del sitio; los cambios previos del repositorio se respetaron.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| Instalación npm y auditoría durante instalación | 26 paquetes; 0 vulnerabilidades reportadas |
| `npm run build` con `SITE_BASE=/` | Correcto; distribución final en `dist/` |
| `npm run build` con `SITE_BASE=/guia-demo/` | Correcto; fonts, assets y descargas respondieron bajo esa base |
| `npm run typecheck` | Correcto |
| `npm test` | 7 pruebas aprobadas |
| `python scripts/check_python.py` | Dos bloques Python con sintaxis válida; cuatro rutas /print y TLS validado en descarga |
| `node --check` en scripts de contenido y navegador | Correcto |
| Navegador Edge real sin ventana, base raíz | Correcto; `evidence/browser-results.json` |
| Navegador Edge real sin ventana, subruta | Correcto; `evidence/browser-subpath.json` |
| Vistas 360, 430, 768, 1024 y 1440 px | Capturadas y revisadas; sin desbordamiento horizontal global |
| Reflujo equivalente al 200% | Viewport de 720 px para escritorio de 1440; sin desbordamiento |
| Colores de texto | Prueba de 21 combinaciones de paleta con relación mínima 4.5:1 |
| Distribución pública | Lista permitida: HTML, JS/CSS del sitio, fuentes/licencias y dos descargas |
| Solicitudes externas y errores del navegador | Ninguna solicitud externa, ningún error de página ni respuestas HTTP 4xx/5xx durante la prueba |

Las pruebas incluyen rechazo de comillas, `$()`, backticks, punto y coma, saltos de línea, controles, rutas de traversal y HTML en cada campo configurable; sustitución sin cascada; límites de IPv4/puertos/nombres; comparación del script descargado con el mostrado; copia exacta al portapapeles; selección manual cuando falla la copia; marcadores que bloquean Copiar; búsqueda y retorno por anclas; recarga de etapa; navegación Anterior/Siguiente; persistencia opcional y borrado de progreso; ausencia de configuración en almacenamiento local; teclado en el enlace de salto; movimiento reducido; impresión de secciones ocultas por búsqueda; y contenido completo con JavaScript deshabilitado. Las comprobaciones adicionales de copia manual y JavaScript deshabilitado se añadieron y ejecutaron sobre la base raíz.

## Evidencia

- `evidence/home-360.png`, `home-430.png`, `home-768.png`, `home-1024.png`, `home-1440.png`: capturas propias del sitio.
- `evidence/tls-360.png`: etapa y bloques de terminal en móvil, con navegación fija.
- `evidence/reflow-200.png`: reflujo equivalente al 200%.
- `evidence/guia-impresion.pdf`: salida de impresión del navegador.
- `evidence/browser-results.json` y `browser-subpath.json`: resultados de ejecución por base.

## Fuentes y alcance de la revisión

Se leyeron README y encargo vigente, el formulario y las implementaciones del conector/lector. Se seleccionó contenido público de WEB.md y se adaptó la redacción al visitante. Las carpetas sensibles no se leyeron ni copiaron. La distribución se construye exclusivamente desde `web/`, sin tomar estado privado, ejecutables o archivos de configuración del programa.

Se consultaron fuentes oficiales de [Vite](https://vite.dev/guide/), [Vercel](https://vercel.com/docs/frameworks/frontend/vite), [integración GitHub](https://vercel.com/docs/git/vercel-for-github), [Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [grants Tailscale](https://tailscale.com/docs/reference/syntax/grants), [usuarios RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User) y [librouteros](https://librouteros.readthedocs.io/en/latest/connect.html), además de las releases oficiales de las Actions incluidas en la plantilla. El ejemplo de la biblioteca que desactiva TLS no se incorporó; se conserva la validación del certificado y del SAN IP. Cada etapa mantiene sus enlaces técnicos para revisión por el administrador.

## Límites pendientes

- No se publicaron sitios, activaron workflows ni crearon repositorios. Vercel está documentado; el workflow Pages permanece como plantilla inactiva en `deploy/`.
- No hubo SSH, instalación o cambios en Raspberry, Tailscale o MikroTik reales. No se acredita compatibilidad física de RouterOS 6/7, ARMv6, reglas Morosos o corte de internet.
- Python se analizó con AST, sin ejecutar contra dispositivos ni acreditar runtime Python 3.11/librouteros en una Raspberry.
- Se revisó reflujo equivalente al 200%; el zoom nativo del navegador al 200%, lector de pantalla, impresión en papel, teléfono físico y otros navegadores requieren revisión manual adicional. El contraste comprobado corresponde a los tokens de texto, no a una auditoría completa de accesibilidad.
- La descarga Markdown conserva el escenario ficticio; se explica en el configurador. El script Python sí se adapta desde el bloque mostrado. Los datos del visitante no se guardan ni se transmiten.

Para publicar falta autorización, destino y acceso al repositorio/proveedor elegido. Después debe verificarse la URL pública, HTTPS, recursos y móvil. Un build local no acredita despliegue.


## Simplificación de acceso · 25 de octubre de 2026

Ruta rápida de tres pasos sin comandos obligatorios para localidades preparadas. Preparación y diagnóstico en desplegables; prueba TLS equivalente retirada; receta de usuario según modo elegido. Verificados en navegador local el selector de control y el enlace que abre escritura. Compilación, siete tests y análisis estático del script Python correctos. Captura: `evidence/acceso-rapido.png`. No se realizaron conexiones ni cambios en Raspberry o MikroTik.

## Revisión para publicación · 25 de octubre de 2026

Se repitieron build (incluye TypeScript), siete tests, análisis estático Python y auditoría npm: correctos; cero vulnerabilidades reportadas. El contenido actual tiene 17 secciones, 36 bloques y un bloque Python. Se actualizó la prueba de navegador para abrir los desplegables antes de interactuar y comprobar esos conteos. La suite completa de Edge pasó con base `/`; se regeneraron `evidence/browser-results.json`, capturas y PDF. Sin peticiones externas ni errores de página/HTTP en el recorrido comprobado. La captura de 360 px se revisó visualmente. No se repitió la prueba de subruta en esta revisión. El dictamen conjunto y los límites están en `../docs/revision-publicacion-2026-10-25.md`. No se publicó el sitio.

## Modo oscuro · 25 de octubre de 2026

Paleta tomada de `portal/static/portal/app.css`, con selector Oscuro/Claro y preferencia independiente del progreso. Build con TypeScript y siete tests correctos. `node scripts/theme-check.mjs` pasó en Edge local: fondo oscuro de la app, ausencia de desbordamiento a 320/360/430/768/1024/1440 px, selector visible, activación por teclado, persistencia tras recarga, sincronización entre pestañas, aislamiento al borrar progreso, búsqueda, impresión clara, almacenamiento bloqueado y contenido sin JavaScript. La prueba usa preview en 4173 por defecto o `QA_URL`; esta ejecución usó 4175. Capturas revisadas visualmente: `evidence/theme-dark-1440.png` y `evidence/theme-dark-360.png`; también se generó `evidence/theme-light-1440.png`. La suite general de navegador y la subruta no se repitieron en este cambio. Cambios preparados localmente; no se desplegó en Vercel.
