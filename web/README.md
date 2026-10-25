# Guía de conexión SpicyOps

Sitio estático en español implementado según `../WEB.md`. Se mantiene separado de la aplicación Windows. Abre con una ruta rápida de tres pasos para localidades preparadas, sin comandos obligatorios. La preparación desde cero (diez etapas), diagnóstico manual, control de Morosos y anexos permanecen en apartados desplegables. Los enlaces y la búsqueda abren el apartado correspondiente; la impresión incluye todo. Se muestra solo el bloque de creación de cuenta del modo elegido. La prueba TLS equivalente en Python se retiró: no se exigen dos pruebas del mismo enlace. El diagnóstico API manual es opcional; SpicyOps es la comprobación principal.

## Arranque y compilación

Desde esta carpeta, con Node 24 LTS y npm:

```powershell
npm ci
npm run dev
```

Abre la dirección local que muestra Vite. Para revisar la distribución:

```powershell
npm run build
npm run preview
```

Comprobaciones existentes:

```powershell
npm run typecheck
npm test
python scripts/check_python.py
node scripts/browser-check.mjs
node scripts/theme-check.mjs
```

La última comprobación requiere Edge instalado y el servidor preview accesible en `http://127.0.0.1:4173/`; puedes cambiarlo con `QA_URL`. Genera las capturas y el PDF de impresión en `evidence/`. Python solo analiza sintaxis y contrato de las recetas, sin importarlas ni ejecutarlas contra equipos.

Runtime utilizado: Node 24.21.0, npm 11.19.0, Python 3.14.7. Dependencias fijadas en package-lock.json: Vite 8.3.5, TypeScript 7.0.2, marked 18.1.1, Playwright 1.64.1 y Fontsource 5.3.0. `npm ci` permite reproducirlas. El análisis de sintaxis no equivale a una ejecución física del lector con Python 3.11.

## Contenido y comportamiento

- Selector **Oscuro / Claro** en la cabecera, con la paleta del programa Windows. Abre en oscuro y recuerda la elección en este navegador; solo guarda el tema en `spicyops-guide-theme-v1`, separado del progreso. Funciona también sin almacenamiento disponible y mantiene la impresión en claro. `src/theme.js` restaura la apariencia antes de pintar la página; el generador lo incluye en la cabecera.
- `src/content/guide.json`: contenido público seleccionado y adaptado; no se publican los Markdown internos completos.
- `scripts/content.mjs`: genera HTML completo, metadatos de comandos y descargas desde esa fuente. Se ejecuta automáticamente al iniciar o compilar.
- `src/content/commands.json`: modelo generado de terminal, acción, privilegios, prerrequisitos, resultado, fuentes y marcadores.
- `src/main.ts` y `src/config.mjs`: búsqueda, anclas, copia, progreso opcional y personalización sin secretos.
- `src/styles.css`, `src/illustrations/network.svg`: cuaderno técnico, diagrama original, adaptación móvil e impresión.
- `public/fonts/`: fuentes locales y licencias OFL; sin solicitudes a Google Fonts.

Los ejemplos se personalizan únicamente en memoria de la pestaña. Se admiten IPv4 de router y Raspberry LAN, host Raspberry, puerto SSH y usuarios con gramática restringida. Las rutas se derivan del usuario Linux; no hay entrada libre de rutas ni contraseñas. Las descargas iniciales conservan el escenario ficticio y se indica junto al configurador; al aplicar datos el script Python se descarga desde el mismo código mostrado. La guía Markdown conserva el escenario ficticio para compartir sin divulgar la configuración de la pestaña.

El progreso se guarda solo al elegirlo: versión del esquema e IDs de etapas en localStorage. Borrar progreso elimina ese registro. Las casillas expresan comprobaciones declaradas por el visitante; la web no detecta equipos.

## Vercel

Preparado para importar un repositorio GitHub autorizado: Root Directory `web`, preset Vite, Node 24, instalación `npm ci`, build `npm run build`, Output Directory `dist`, `SITE_BASE=/` (valor por defecto). No necesita funciones, secretos ni reescrituras SPA. Publicar únicamente el resultado de `web/dist`.

Si el sitio se extrae a un repositorio independiente, esa carpeta pasa a ser la raíz del proyecto. Revisar acceso del propietario, plan e integración antes de conectar GitHub: Hobby no admite repositorios privados de organizaciones. No cambiar la visibilidad del repositorio del programa para resolverlo. Elegir rama de producción y previews al autorizar la publicación. [Documentación Vercel/Vite](https://vercel.com/docs/frameworks/frontend/vite), [integración GitHub](https://vercel.com/docs/git/vercel-for-github).

## GitHub Pages

La plantilla `deploy/github-pages.yml` permanece fuera de `.github/workflows`, por lo que no activa despliegues. Cuando se autorice publicar, cópiala a `.github/workflows/spicyops-guide.yml` del repositorio elegido y configura Pages → GitHub Actions. Se inicia únicamente con `workflow_dispatch`; no tiene evento push. Requiere proporcionar la base real: `/repositorio/` para un sitio de proyecto, `/` para dominio propio/raíz. La expresión de entrada se pasa por variable de entorno, sin interpolación en comandos de shell.

Usa Actions oficiales comprobadas: checkout 7.0.1, setup-node 7.1.0, configure-pages 5, upload-pages-artifact 5.0.0 y deploy-pages 5.0.1. Publica solo `web/dist` y solicita contents:read, pages:write e id-token:write. En un repositorio separado ajustar los directorios y el lockfile a su raíz.

Para probar una subruta ficticia localmente:

```powershell
$env:SITE_BASE='/guia-demo/'
npm run build
npm run preview
```

Abre la URL con `/guia-demo/`. Después elimina esa variable y recompila para volver a `/`:

```powershell
Remove-Item Env:SITE_BASE
npm run build
```

Pages desde repositorios privados depende del plan; en Free requiere repositorio público. Se recomienda un repositorio separado que contenga solo el sitio revisado. [Workflows oficiales y disponibilidad de Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages). Las versiones de Actions se revisaron en sus páginas oficiales de releases; no se ejecutó el workflow remoto.

## Verificación y límites

Consulta `VERIFICACION.md` y `evidence/` para resultados reales. La distribución final está compilada con base `/`. No se ha publicado en Vercel o Pages ni creado repositorios. Las recetas no se ejecutaron en Raspberry, Tailscale o MikroTik reales. La guía no captura contraseñas, hace SSH, instala software remoto ni suspende abonados. No incluye el ejecutable Windows ni sus datos privados.
