# SpicyOps — guía de diseño y dirección de arte

Referencia: https://learn-arduino-red.vercel.app/es/  
Examinada el 24 de octubre de 2026. Nombre del archivo solicitado: `DESING.md`.

## 1. Encargo para el agente

Rediseñar la interfaz de SpicyOps para Windows con el lenguaje visual de la referencia: **papel crema, tinta azul marino, instrumentación técnica, ilustración isométrica y acentos turquesa**. Debe sentirse como una herramienta de trabajo cuidadosamente dibujada sobre una mesa de electrónica.

Este archivo especifica una adaptación visual. Conservar las funciones y reglas del producto descritas en `README.md`, `AGENTS.md` y `docs/encargo-panel-conectado.md`. La navegación principal sigue siendo Analytics, Clientes y Conexiones. Mantener también diagnóstico, inventario excluido, respaldos y recuperación.

No limitarse a cambiar el fondo: adaptar tipografía, superficies, iconos, diagramas, gráficos, tablas, formularios, estados, modales y composición. El resultado debe conservar la identidad SpicyOps y la claridad de una aplicación administrativa.

## 2. Qué se examinó y grado de certeza

Se abrió la página real en navegador, se revisaron su composición compacta, el visor de la placa, la navegación inferior, las tarjetas de lecciones, los paneles Resumen y Especificaciones y el panel de código. Se leyeron estilos calculados y reglas CSS accesibles de la página para comprobar colores, familias tipográficas, dimensiones y variantes adaptables.

La ventana disponible tenía un viewport CSS de 530 × 716. La composición amplia se reconstruye de las reglas CSS de la referencia; **no se verificó visualmente en un viewport de escritorio**. Las medidas de escritorio citadas abajo pertenecen a ese CSS, no a una captura amplia. Tampoco se auditó toda la aplicación educativa ni su accesibilidad completa.

Evidencia local de consulta, no recursos para incorporar al producto:

- [Composición compacta](docs/design-reference/arduino-es-home.png).
- [Panel de especificaciones](docs/design-reference/arduino-es-specs.png).

En este documento, **observado** describe la referencia. **Propuesta SpicyOps** establece decisiones para implementarla. Los tamaños y breakpoints propuestos son recomendaciones, no mediciones de la referencia.

## 3. Lectura del estilo y del arte

### Observado: cuaderno de ingeniería interactivo

La base es cálida y clara, con una leve luminosidad radial. Predominan crema, arena y beige; no blanco puro. El texto importante y los contornos del hardware usan azul marino casi negro. El turquesa dirige la atención hacia puntos interactivos, selección y señales de actividad.

La interfaz combina precisión técnica y calidez editorial:

- Títulos condensados en mayúsculas, con separación entre letras.
- Párrafos de una sans serif más abierta y cómoda.
- Fechas, hora y código con tipografía monoespaciada.
- Paneles delimitados por trazos beige finos, con radios moderados.
- Botones con iconos simples y poca elevación.
- Una zona visual protagonista y paneles auxiliares de información.
- Cuadrícula isométrica, pistas de circuito y pequeños nodos como contexto gráfico.

### Observado: ilustración técnica estilizada

La placa se presenta en perspectiva isométrica/oblicua, con volumen legible, bordes oscuros marcados, caras de color mate, detalles simplificados y sombras de contacto. Los cuerpos azul violáceo contrastan con piezas metálicas crema/gris y pequeños componentes rojos. No tiene acabado fotográfico brillante.

Los marcadores turquesa conectan visualmente el objeto con etiquetas crema de contorno fino. Las miniaturas del carrusel mantienen ese mismo vocabulario de objetos técnicos. La ilustración concentra el detalle; los controles alrededor son sobrios.

### Propuesta SpicyOps: interpretación

Trasladar esa sensación a una **consola de redes sobre papel técnico**. Usar diagramas vectoriales de PC → Raspberry → MikroTik y pequeños dibujos de equipos cuando ayuden a entender una conexión o un estado vacío. Mantener gráficas y tablas como protagonistas cuando ya existen datos.

No es necesario añadir un motor 3D, WebGL, una placa Arduino ni un simulador. Un SVG propio con volumen isométrico simple puede transmitir el estilo con menor coste. No copiar logo, modelos, miniaturas ni textos de la web; las capturas solo documentan la referencia.

## 4. Paleta comprobada y uso

Estos valores se extrajeron de las variables CSS de la referencia:

| Token de referencia | Valor | Papel visual |
| --- | --- | --- |
| `--bg` | `#F6EDDD` | Fondo crema |
| `--bg-deep` | `#EFE3D1` | Crema más profundo |
| `--sidebar` | `#E9DCCA` | Navegación arena |
| `--card` | `#F9F2E5` | Superficie de tarjetas |
| `--card-soft` | `#FAF4E9F7` | Superficie casi opaca; alfa F7 |
| `--code-bg` | `#F8F0E3` | Recuadros técnicos |
| `--line` | `#CEC0AD` | Contornos principales |
| `--line-soft` | `#E2D7C7` | Divisores secundarios |
| `--navy` | `#18213D` | Títulos y énfasis |
| `--navy-2` | `#24304A` | Iconos y controles |
| `--ink` | `#4F535B` | Texto de lectura |
| `--muted` | `#696D74` | Texto secundario |
| `--faint` | `#ADA293` | Detalle tenue |
| `--teal` | `#1AA3A1` | Interacción y nodos |
| `--teal-deep` | `#3F7F8E` | Selección y contornos activos |
| `--trace` | `#D3BEA3` | Trazas decorativas |
| `--track` | `#E3D8CA` | Pistas de progreso |

Los colores de sintaxis comprobados son azul `#2A56A3` y naranja `#C0652D`; no hace falta trasladar un editor de código a SpicyOps.

### Propuesta: distribución del color

Aproximadamente 80% de la superficie debe permanecer en crema/arena; la tinta organiza texto y controles, y el acento ocupa áreas pequeñas. Esta proporción es una orientación visual, no una métrica rígida.

El botón principal puede tener fondo navy y texto crema, como el control de ejecución de la referencia. Reservar turquesa para selección, foco y elementos de información. Conservar verde para Activa, ámbar para Error de conexión y gris para Desconectada. El rojo queda reservado a fallos y acciones de riesgo.

Colores semánticos **propuestos para SpicyOps**, no extraídos del sitio:

| Estado | Texto / borde | Fondo claro |
| --- | --- | --- |
| Correcto | `#246447` | `#E4EFE5` |
| Advertencia | `#805116` | `#F4E6C9` |
| Error / riesgo | `#993E37` | `#F5E1DA` |
| Neutro | `#62656B` | `#EAE3D8` |
| Información | `#315F71` | `#E1ECE8` |

Comprobar contraste sobre el fondo real antes de aprobar. `--faint` se limita a decoración; las fechas de lectura, errores y condiciones operativas deben usar texto secundario legible. Evitar texto blanco pequeño sobre el turquesa claro.

## 5. Tipografía

### Observado

La referencia usa **Barlow** para lectura, **Barlow Semi Condensed** para títulos/etiquetas y **JetBrains Mono** para información técnica. El título amplio declara 36.5 px, peso 600 y tracking de 0.13 em; el compacto observado usa 20 px. Los títulos de panel compactos rondan 18–21 px. Las pestañas observadas usan 14.5 px; las etiquetas sobre la placa, 11.5 px y peso 700.

### Propuesta SpicyOps

| Función | Fuente | Tamaño / peso | Tratamiento |
| --- | --- | --- | --- |
| Marca o título principal | Barlow Semi Condensed | 28–34 px / 600–700 | Mayúsculas; tracking 0.08–0.11 em |
| Sección | Barlow Semi Condensed | 20–22 px / 700 | Tracking 0.04–0.06 em |
| Etiquetas y navegación | Barlow Semi Condensed | 13–15 px / 600–700 | Mayúsculas solo en etiquetas cortas |
| Cuerpo y formularios | Barlow | 15–16 px / 400–500 | Interlineado 1.45–1.6 |
| Ayuda | Barlow | 13–14 px / 400 | Contraste suficiente |
| IP, fechas y cantidades | JetBrains Mono | 12–14 px / 400–500 | Números tabulares |
| Métrica principal | Barlow Semi Condensed | 30–36 px / 600–700 | Unidad más pequeña |

No poner párrafos, nombres de clientes ni notas enteras en mayúsculas. Conservar la lectura natural de alias largos. Alinear cantidades por su valor y mantener la unidad junto al número.

Distribuir fuentes localmente en la aplicación, conservando sus licencias; no depender de Google Fonts, CDN ni conexión a internet. Fallbacks: `Segoe UI`, `system-ui`, `sans-serif`; para datos, `Consolas`, `ui-monospace`, `monospace`.

## 6. Composición, espacio y superficies

### Observado en la referencia

El CSS amplio define un artboard de 1672 × 941, una barra lateral de 72 px que puede expandirse a 214 px, una gran zona de visualización a la izquierda, paneles de información/código a la derecha y lecciones en una banda inferior. El modo compacto cambia a una cuadrícula fluida y lleva la navegación a una barra inferior.

Los radios comprobados están entre 7 y 14 px. El CSS declara bordes de 1.5 px en muchos paneles, aunque el estilo calculado del viewport observado puede mostrar fracciones distintas. La selección de lección usa un borde de 2 px en turquesa oscuro. Las sombras son cálidas, cortas y discretas.

### Propuesta de estructura SpicyOps

Usar Grid/Flex y flujo normal; **no reproducir las posiciones absolutas ni escalar toda la aplicación como un lienzo fijo**. Las tablas, los nombres y los formularios necesitan crecer.

```text
┌───────────────┬─────────────────────────────────────────────────┐
│ SPICYOPS      │ Administración / vista       Localidad [▼]     │
│               ├─────────────────────────────────────────────────┤
│ Analytics     │ TÍTULO DE VISTA          Acción principal      │
│ Clientes      │ Estado del perfil · automática · fecha de datos│
│ Conexiones    │                                                 │
│               │ Tarjetas o herramientas de consulta            │
│               │                                                 │
│               │ Gráfica, tabla o perfiles de conexión           │
│ Localidad     │                                                 │
│ Estado        ├─────────────────────────────────────────────────┤
│               │ Versión · Respaldos         Última lectura      │
└───────────────┴─────────────────────────────────────────────────┘
```

- Barra lateral arena de aproximadamente 200–220 px con iconos y nombres visibles. Priorizar reconocimiento sobre imitar la barra estrecha del ejemplo.
- Área de trabajo crema, ancho máximo aproximado 1440–1600 px y margen interno 24–32 px; en móvil 16 px.
- Ritmo de espaciado: 4, 8, 12, 16, 24, 32 y 48 px.
- Separación entre paneles: 16–24 px. Padding de panel: 20–24 px.
- Radios: 8 px en controles, 12 px en paneles, 14 px en una zona ilustrada.
- Evitar apilar tarjetas dentro de tarjetas sin necesidad; un divisor puede resolver la agrupación.
- Reservar líneas de circuito y cuadrícula isométrica a estados vacíos, encabezados o diagramas. No ponerlas detrás de tablas, inputs o etiquetas de gráficas.

No usar grandes degradados de marca, luces neón, vidrio desenfocado, sombras negras pesadas ni un fondo oscuro como superficie principal. El volumen lo aportan las ilustraciones y los bordes, no una elevación exagerada de cada panel.

## 7. Componentes e interacción

### Navegación

Iconos navy con el mismo grosor y familia visual. Elemento activo: fondo de tinta al 6–9%, pequeña marca turquesa y texto de mayor peso. Mantener `aria-current` y foco visible. El selector de localidad permanece accesible; la opción Todos conserva su comportamiento actual.

En móvil se propone navegación inferior con las tres secciones, **icono y nombre**, altura aproximada de 64–72 px y espacio inferior para que no tape el contenido. Respaldos sigue accesible desde el pie. No añadir accesos a funciones inexistentes por reproducir los seis iconos de la referencia.

### Tarjetas y datos

Superficie `--card`, borde `--line`, título navy y etiqueta condensada. Métricas grandes con unidad secundaria y nota de procedencia/fecha. Usar `—` o el mensaje correspondiente cuando no hay datos; cero solo cuando se conoce que el valor es cero.

Las fichas técnicas del panel Especificaciones inspiran un patrón de etiqueta corta arriba y valor debajo, útil para identidad del router, IP, versión y última lectura. No copiar su texto tenue si perjudica el contraste.

### Botones

- Principal: navy, texto crema, radio 8 px, icono lineal y etiqueta clara.
- Secundario: crema, borde beige, texto navy.
- Acción de riesgo: rojo semántico; usarlo solo cuando corresponda al contexto.
- Icono aislado: nombre accesible y tooltip; área de interacción propuesta de al menos 44 × 44 px.
- Hover: cambio sutil de fondo/borde. En tarjetas seleccionables se admite desplazamiento de hasta 2 px, como la referencia; evitarlo en filas de tabla.
- Disabled: aspecto distinguible y explicación cuando la causa no sea evidente. No expresar estado únicamente con opacidad.

### Formularios

Campos crema pálido, borde beige, texto tinta, label siempre visible y ayuda debajo. Altura propuesta 44 px; `textarea` con crecimiento vertical. Foco con contorno contrastado de 2 px y separación de 2–3 px. Validar visualmente su contraste.

Errores inline junto al campo y resumen cuando corresponda. Mantener nombres, tipos, atributos `data-*`, validación y comportamiento de envío. Los secretos conservan el tratamiento actual; no incluirlos en maquetas, capturas ni ejemplos.

### Pestañas y controles segmentados

La referencia usa pestañas de texto sin píldoras grandes; la activa tiene una línea navy corta de unos 4–4.5 px y mayor peso. Adoptar ese patrón donde ya exista navegación secundaria. El selector Mbps/MB/s puede ser un control segmentado compacto, sin cambiar el cálculo.

No crear pestañas nuevas solo para que se parezca a la referencia.

### Avisos y ventanas

Avisos con fondo semántico claro, texto legible, icono y cierre. Conservar el comportamiento temporal actual, incluida la pausa por foco/hover. Distinguir esos avisos de errores persistentes y problemas que requieren intervención.

Modales crema, contorno beige, título navy, sombra cálida y backdrop tenue. Conservar foco inicial, navegación por teclado, devolución del foco al cerrar y reglas actuales de cierre. Las confirmaciones operativas deben mostrar claramente localidad, cliente e IP.

### Movimiento

La referencia declara transiciones de unos 150–250 ms en controles, 250 ms en tarjetas y hasta 450 ms en expansión de paneles. Para SpicyOps se proponen transiciones de 120–200 ms en color, borde y opacidad. El movimiento es auxiliar.

Respetar `prefers-reduced-motion`: eliminar desplazamientos, pulsaciones y animaciones decorativas. No añadir partículas, tráfico animado continuo ni un reloj que sugiera que los datos se actualizan cada segundo.

## 8. Aplicación por pantalla

### Analytics

Conservar métricas, gráfica de consumo observado y estimaciones existentes. La gráfica ocupa el panel dominante. Las métricas forman una fila o cuadrícula según el ancho. Título condensado, valores navy, ayudas grises legibles y fecha de lectura visible.

Proponer barras en turquesa oscuro y azul pizarra, conservando los colores por día y el detalle temporal actual. Ejes y cuadrícula beige muy suaves; leyenda y valores con contraste suficiente. Mantener inicio/fin del intervalo y desplazamiento horizontal en pantallas estrechas. Ofrecer la información también con foco o alternativa textual si hoy depende solo del cursor.

No representar contadores acumulados como consumo mensual real. Las aproximaciones por uptime siguen identificadas como aproximaciones; no añadir nuevos selectores de proyección ni inventar continuidad donde faltan lecturas. Sin intervalo válido, mostrar el estado vacío real.

### Clientes

Usar una tabla clara, con cabecera crema un poco más profunda, divisores suaves, filas de altura cómoda y hover discreto. Icono de usuario vectorial consistente; nombre en Barlow y datos técnicos en monoespaciada. Mantener búsqueda, localidad por fila cuando corresponde, IP, plan, consumo, estado y acciones.

No reducir fuente ni ocultar información crítica para forzar todas las columnas. Conservar la adaptación a tarjetas en anchos reducidos y etiquetas por dato. Los nombres extensos deben envolver sin desplazar acciones fuera de pantalla.

Suspender conserva el interruptor Sí/No y la confirmación. El color no debe confundir suspensión con conectividad: ámbar indica restricción configurada cuando corresponde; un verde no significa acceso físico a internet comprobado. No actualizar el interruptor de forma optimista antes de leer el resultado. Los casos inciertos conservan su instrucción de sincronizar.

Ver datos abre una ficha con los datos leídos diferenciados de alias/contacto/ubicación/notas editables. La estética de ficha técnica ayuda a separar grupos sin cambiar qué fuente manda.

### Conexiones y configuración

Tarjetas crema por localidad, icono o pequeño equipo isométrico, nombre, etiqueta de estado y fechas. Conservar Configurar, Diagnosticar, Conectar/Sincronizar, Desconectar y programación automática según la disponibilidad actual.

El diagrama PC → Raspberry → MikroTik puede usar líneas beige y nodos turquesa como recurso explicativo. Debe identificarse como esquema; no inventar estado de enlaces ni animar paquetes como si fueran telemetría real.

Agrupar el formulario por acceso SSH, API-SSL/certificado y opciones existentes. Las opciones avanzadas mantienen su visibilidad actual o una divulgación accesible. Huellas, validación TLS, advertencias y errores no pueden perder prioridad visual por el rediseño.

Mostrar por separado estado del perfil, fecha de los datos y resultado de la última operación. No deducir disponibilidad actual de una lectura guardada ni introducir caducidades nuevas.

### Diagnóstico, inventario, respaldos y recuperación

Extender el mismo sistema de superficies y tipografía. Diagnóstico: etapas legibles con texto e icono, no solo puntos de color. Inventario: motivos de exclusión y acciones claras. Recuperación: instrucciones y errores persistentes visibles; las acciones que afectan archivos deben seguir distinguiéndose con claridad.

### Instalación vacía

Un panel cálido con un SVG propio pequeño, título breve, explicación útil y la acción Nueva localidad. No llenar Analytics con cifras o gráficas sintéticas. La ilustración puede mostrar equipos genéricos sin nombres, IP ni credenciales reales.

## 9. Especificación de ilustración e iconografía

Para crear un recurso original de SpicyOps, usar esta dirección:

> Ilustración técnica isométrica de una Raspberry y un router genéricos sobre una base crema, volúmenes mate azul pizarra y gris cálido, contornos navy de grosor uniforme, perspectiva consistente, sombras de contacto suaves, puertos simplificados y un único indicador turquesa. Composición limpia y funcional, sin texto incrustado, sin logos de terceros y sin fondo fotográfico.

Preferir SVG para iconos y diagramas del producto. Si se usan bitmaps, suministrar resolución suficiente y variantes sin pérdida de legibilidad. Mantener el arte decorativo fuera del árbol accesible; si explica un flujo, acompañarlo de texto equivalente.

Reutilizar y ajustar los símbolos SVG actuales de SpicyOps antes de incorporar otra biblioteca. Contornos aproximados de 1.7–2 px, extremos redondeados, rejilla coherente de 24 px y tamaño visible de 20–24 px. Evitar emojis y mezclar iconos sólidos, fotográficos y lineales en un mismo grupo.

## 10. Base de tokens propuesta

Esta base facilita la adaptación; no es un parche completo ni debe pegarse al final de una cascada oscura sin revisar los componentes:

```css
:root {
  color-scheme: light;
  --bg: #f6eddd;
  --paper: #f9f2e5;
  --surface-soft: #faf4e9;
  --surface-deep: #efe3d1;
  --sidebar: #e9dcca;
  --ink: #4f535b;
  --heading: #18213d;
  --muted: #696d74;
  --border: #cec0ad;
  --border-soft: #e2d7c7;
  --brand: #3f7f8e;
  --accent: #1aa3a1;
  --action: #18213d;
  --on-action: #f9f2e5;
  --focus: #315f71;
  --shadow: 0 6px 16px -12px rgb(60 45 20 / 40%);
  --radius-control: 8px;
  --radius-panel: 12px;
  --font-body: 'Barlow', 'Segoe UI', system-ui, sans-serif;
  --font-heading: 'Barlow Semi Condensed', 'Barlow', 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, ui-monospace, monospace;
}

body { background: var(--bg); color: var(--ink); }
h1, h2, h3 { color: var(--heading); font-family: var(--font-heading); }
.button { background: var(--action); color: var(--on-action); }
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
```

Hay colores oscuros y colores literales repetidos en el CSS actual. Revisar también pseudoelementos, estados hover/disabled, campos, modales, leyendas, SVG, barras y reglas responsive. Migrar esas variantes a tokens semánticos para evitar texto claro sobre superficies claras o bloques oscuros residuales.

## 11. Adaptación a distintos tamaños

Breakpoints **propuestos**, a ajustar según el contenido real:

| Ancho CSS | Composición |
| --- | --- |
| ≥ 1200 px | Navegación lateral; métricas en fila; panel dominante amplio |
| 768–1199 px | Paneles que se apilan cuando falta espacio; métricas en dos columnas |
| < 768 px | Navegación inferior; una columna; acciones reordenadas sin ocultarlas |
| 360–430 px | Campos y tarjetas al ancho disponible; nombres largos envuelven |

No sustituir automáticamente el breakpoint vigente de Clientes: comprobar primero sus ocho columnas posibles y preservar el paso a tarjetas tan pronto como lo necesite. Evitar scroll horizontal global; admitirlo únicamente en regiones justificadas como la gráfica histórica. Comprobar zoom del 200% y ventanas de poca altura.

## 12. Ruta de implementación en este repositorio

1. Leer el estado actual y conservar los cambios previos del usuario. El árbol tenía modificaciones pendientes al redactar esta guía.
2. Empezar por `portal/static/portal/app.css`: tokens, tipografía, superficies y estados. Consolidar los overrides del tema oscuro en vez de acumular otra capa de excepciones.
3. Ajustar estructura y navegación en `portal/templates/portal/base.html` manteniendo enlaces, bloques, formularios y atributos usados por la actualización en vivo.
4. Adaptar `analytics.html`, `clients.html`, `connections.html` y `connect.html`; después `diagnostic.html`, `inventory.html`, `locked.html` y `recovery.html`.
5. Tocar `portal/static/portal/app.js` únicamente cuando la presentación o accesibilidad lo requiera. No alterar programación, persistencia o destino de acciones como parte del cambio visual.
6. Añadir fuentes e ilustraciones propias a recursos estáticos locales y comprobar su inclusión en el paquete Windows y avisos de terceros.
7. Revisar la interfaz con datos sintéticos aislados y estado vacío. Ejecutar las comprobaciones vigentes pertinentes; reconstruir/verificar el ejecutable si se entrega una nueva distribución.

El rediseño no autoriza conectarse a equipos reales, modificar MikroTik, instalar servicios, cambiar permisos ni leer carpetas sensibles. Para pruebas usar los mecanismos locales ya existentes, sin cargar el estado privado del operador.

## 13. Criterios de aceptación

### Fidelidad visual

- [ ] La primera impresión es papel crema con tinta navy y detalles turquesa.
- [ ] Se reconocen la tipografía condensada, los contornos beige y la sobriedad de los controles.
- [ ] Los recursos de red comparten una dirección técnica e isométrica coherente cuando se emplean.
- [ ] El arte acompaña; las tablas, cifras y acciones mantienen prioridad.
- [ ] No quedan superficies oscuras accidentales, colores literales incompatibles ni controles de estilos mezclados.

### Uso y accesibilidad

- [ ] Texto normal con contraste mínimo 4.5:1; texto grande y elementos no textuales esenciales según su criterio aplicable de 3:1.
- [ ] Foco visible, recorrido de teclado coherente y nombres accesibles para iconos.
- [ ] Estado expresado con texto además de color; etiquetas y errores legibles.
- [ ] Sin contenido cortado a 360, 430, 768, 1024 y 1440 px, ni al 200% de zoom.
- [ ] Modales, desplegables, navegación inferior y ayudas no se tapan entre sí.
- [ ] Movimiento reducido y recursos disponibles sin internet.

### Comportamiento conservado

- [ ] Arranque vacío, sin clientes, conexiones o gráficas ficticios en el producto.
- [ ] Localidades y Todos mantienen aislamiento, búsqueda y destino individual de acciones.
- [ ] Sincronización no pierde borradores ni confirma acciones pendientes.
- [ ] Morosos mantiene confirmación, validación y lectura posterior; no hay cambio optimista.
- [ ] Unidades, contadores, estimaciones y fechas conservan su significado.
- [ ] Diagnóstico, exclusiones, programación, respaldos y recuperación siguen accesibles.
- [ ] Se documentan vistas/casos realmente comprobados y cualquier prueba pendiente. Una captura no acredita conexión física.

## 14. Entrega esperada del agente implementador

Entregar el rediseño aplicado, capturas de Analytics/Clientes/Conexiones en escritorio y móvil con datos sintéticos, captura de arranque vacío y de una confirmación, relación breve de cambios y verificaciones realmente ejecutadas. Si se genera una distribución, comprobar que incluye recursos locales y corresponde a las fuentes.

Esta guía por sí sola no acredita implementación, pruebas de UI ni reconstrucción del ejecutable. Su propósito es ofrecer una referencia verificable y decisiones suficientes para ejecutar el rediseño.
