# Plan de implementación y validación

Este documento conserva la secuencia propuesta. Posteriormente, el usuario preparó API-SSL y permisos de MikroTik e instaló un entorno de diagnóstico en Raspberry; las salidas y cierre están en preparación-mikrotik.md y prueba-cliente-011.md. Este plan pertenece al MVP sustituido; su código y sus pruebas se retiraron. Para el producto Windows implementado, consultar el [encargo vigente](encargo-panel-conectado.md) y el [README](../README.md).

## Etapa 0: inventario y decisiones del piloto

La revisión documental ya produjo [red actual](red-actual.md) y [adaptación del MVP](adaptacion-spicynet.md). Se confirma versión exportada 6.49.23, bridge LAN, colas por IP, Morosos y automatismos nocturnos. El usuario confirmó baja de Diego y rol AP de SN-LP-06. Los dos backups binarios se inventariaron, pero no se decodificaron ni restauraron.

Completar con acceso de lectura y sin publicar secretos:

- Modelo exacto, arquitectura, sistema operativo, versión de Python y carga de la Raspberry; memoria libre, almacenamiento y estado de la microSD.
- Preparación segura de servicios: la salida posterior compartida por el usuario confirma SSH/API/API-SSL habilitados; Una salida más reciente confirma certificado spicyops-api y TLS only-1.2, con ADDRESS vacío. La prueba TLS desde Raspberry ya validó cadena e IP. La cuenta dedicada ya está habilitada con read,api y origen .90/32. La restricción del servicio API-SSL a .90/32 y la prueba TLS posterior están confirmadas. El filtro IPv4 de API ya se confirmó activo y ordenado, conservando acceso TLS desde Raspberry. La autenticación y lectura API ya confirmaron identidad, versión 6.49.23 (stable) y 15 colas. API sin TLS ya se confirmó deshabilitada, manteniendo API-SSL. Faltan rechazo desde otro origen y validación de altas, suspensión/reactivación y velocidad. La revisión adicional del portal queda aplazada por prioridad del usuario y no bloquea el MVP. No asumir que el export previo describe la activación.
- Validez actual del esquema de IP fija de cada CPE. Se tiene un ejemplo (.52) con NAT de vivienda; confirmar que no se agrupen distintos abonados detrás de una sola IP controlada.
- Validar once abonados candidatos .52–.62, sus CPE y AP. .51 corresponde a baja histórica, no debe darse de alta por importación.
- Completar uplink y `.cfg` de SN-LP-06; confirmar enlace local .4/.5 y puertos físicos del nodo principal.
- Confirmar IPv6 y estado dinámico de red: el export no basta. Revisar que no se hayan añadido reglas después del respaldo.
- Lighttpd ya está identificado; su revisión adicional es opcional y queda para después. Comprobar Tailscale, rutas aprobadas y políticas de acceso sigue siendo relevante para mantenimiento.
- Scripts anteriores del colega, sin ejecutar sus acciones; revisar selección de clientes y manejo de errores.
- Cantidad esperada de sitios, routers, operadores y clientes en el primer año.

El método inicial elegido es IP fija + cola simple + Morosos. Antes de automatizar, confirmar la política nocturna y el trato de .56/FREE. No hace falta migrar a PPPoE. No se necesitan contraseñas adicionales para terminar esta definición; los archivos de sistema deben compartirse saneados.

## Etapa 1: prueba técnica de solo lectura

Seguir [preparación de MikroTik](preparacion-mikrotik.md) para configurar y verificar acceso seguro paso a paso. El usuario ejecuta los comandos en su terminal y comparte resultados; entregar instrucciones no equivale a haberlas aplicado. La guía separa requisitos reutilizables de valores concretos de SpicyNet.

Verificar en la Raspberry real que las dependencias elegidas se instalan y consultan el router de forma segura. Validar certificado API-SSL, autenticación, lectura de un objeto, tiempos de respuesta y consumo de memoria junto con Tailscale.

Salida: decisión confirmada o corregida sobre Python/librouteros/API-SSL. Si no funciona, documentar la causa antes de optar por Paramiko, otra biblioteca o hardware. No resolver certificados desactivando su comprobación.

## Etapa 2: primer recorrido completo

Construir el panel mínimo y el agente después de aprobar el diseño operativo del piloto: cliente, servicio, tarea persistente, consulta del agente, operación permitida y lectura de resultado. Empezar en simulación; luego usar un cliente reservado para pruebas.

Para el primer recorrido elegir una operación reversible sobre un servicio existente. Añadir después aprovisionamiento, suspensión/reactivación y cambio de plan. No introducir facturación ni automatización por mora en este paso.

## Etapa 3: fallos y seguridad

| Prueba | Resultado requerido |
|---|---|
| Entregar dos veces el alta | Un solo objeto técnico, asociado al servicio correcto |
| Solicitar suspensión y enseguida reactivación | Convergencia a la última revisión y trazabilidad de ambas |
| Apagar agente antes de aplicar | Tarea recuperable o vencida, sin falso éxito |
| Reiniciar tras cambio y antes del reporte | Lectura del estado y resultado recuperado, sin duplicados |
| Perder Starlink o el panel | Se conserva el acceso previamente configurado; no hay cortes por desconexión del gestor |
| MikroTik inaccesible | Reintentos acotados y error visible |
| Certificado o identidad inválidos | Conexión rechazada, sin degradación automática |
| Agente de otro sitio reclama la tarea | Acceso denegado |
| Operador sin permisos solicita un cambio | Solicitud rechazada por el servidor |
| Cambiar IP o detectar asociación ambigua | Detener modificación hasta revisar el vínculo |
| Modificación manual desde WinBox | Discrepancia visible; no sobrescribirla automáticamente sin política definida |
| Suspender con IPv6 o sesión establecida | Sin acceso residual por los caminos controlados del cliente de prueba |
| Revertir cambio individual | Recuperación del servicio sin alterar otros abonados |

## Etapa 4: piloto sobre la red de once abonados candidatos activos

El usuario seleccionó posteriormente el servicio .62, cliente 011, para una prueba temporal. Seguir el [registro acotado](prueba-cliente-011.md): lectura inicial, recuperación preparada y cambios exclusivamente sobre ese servicio. La autorización no se extiende a otros abonados ni a borrar/recrear su conexión para ensayar un alta.

Primero intervenir únicamente el servicio de prueba, en una ventana acordada. Conservar respaldo y exportación del router fuera del dispositivo, sin guardarlos en Git: pueden contener información sensible. Confirmar acceso local de recuperación y comprobar que el canal de administración no queda incluido en la suspensión.

Aplicar las pruebas específicas de adaptación: proteger .1–.6, .50 y .90, conservar el orden de las 15 colas y los schedulers, impedir altas automáticas del cliente histórico .51 y tratar el aviso del portal como opcional; si se incorpora después, comprobar su recorrido antes de depender de él. El historial del inventario de doce abonados no equivale a doce clientes activos.

Registrar antes y después: configuración relevante, acceso real del cliente, subida/bajada con pruebas controladas, CPU/RAM del router y recursos de la Raspberry. Una lectura correcta de API demuestra configuración, no demuestra por sí misma conectividad o límite efectivo. El resultado de velocidad también depende de Starlink y de la radio/red local.

Objetivo inicial de estabilidad: 72 horas sin crecimiento sostenido de memoria, reinicios inesperados ni degradación de Tailscale. El umbral propuesto del agente está en [investigación](investigacion-tecnologias.md). Revisar carga al aplicar colas/firewall, especialmente si cambia el tratamiento de FastTrack. No exigir una velocidad medida superior a la capacidad física del equipo.

Extender el piloto solo después de verificar el primer servicio. Los otros clientes actúan como control: no deben perder acceso ni recibir cambios de plan por las pruebas.

## Criterios para declarar completo el MVP

Un operador realiza alta administrativa y técnica, suspensión, reactivación y cambio de plan con el método de acceso elegido. Se comprueba el resultado desde un cliente; hay recuperación de tareas, separación de permisos y auditoría; una restauración de la base de datos y una reversión individual se han ensayado. Las limitaciones conocidas quedan registradas.

## Decisiones de crecimiento

| Señal observada | Decisión a reevaluar |
|---|---|
| Instalación o consumo problemáticos en la Raspberry | Ajustar agente; evaluar Go o hardware con más recursos |
| Consultas HTTP costosas o reacción insuficiente al crecer sitios | Medir y considerar long polling o MQTT |
| Necesidad de autenticación/accounting centralizados | Diseñar RADIUS y su continuidad de servicio antes de migrar |
| UI con interacción compleja demostrada | Evaluar frontend independiente manteniendo el contrato del agente |
| Colas y reglas saturan el MikroTik | Revisar diseño de tráfico y capacidad del router; no asumir que actualizar software basta |
| Facturación resulta más importante que personalización | Comparar adopción de plataforma ISP existente con desarrollo propio |

No se fija presupuesto ni calendario cerrado hasta completar inventario y primera prueba. Los costos a cotizar son servidor, base de datos, respaldos, dominio, acceso remoto aplicable y tiempo de operación; no se asignan tarifas sin una selección de proveedor.

## Cierre de la preparación interactiva

El usuario pidió terminar la secuencia de comandos. Se cerró la prueba de escritura del mismo límite de .62 con plan conservado y grupo devuelto a read,api,!write, confirmado por salida. Continuar con diseño/documentación; los ensayos de efecto real siguen sin validarse y podrán retomarse cuando se programe otra etapa, sin condicionar ahora el avance a más comandos del usuario.
