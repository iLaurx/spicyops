> ARCHIVO HISTÓRICO DEL PRIMER ENCARGO. El usuario sustituyó el producto manual/simulado por SpicyOps para Windows. Ver [encargo vigente](encargo-panel-conectado.md) y [README](../README.md). Las pruebas anteriores no acreditan la conexión física ni describen la interfaz actual.

# Encargo para el siguiente agente: primer MVP local

Fecha: 16/10/2026. Este encargo prepara la siguiente fase de desarrollo; no afirma que el software exista ya. El agente de desarrollo es quien implementará el sistema. El agente de Raspberry es un componente del producto, no una IA ni un requisito de contratar una API de modelos.

## Objetivo y punto de llegada

Entregar una versión local ejecutable de SpicyOps que permita registrar un cliente y un servicio, solicitar alta técnica, suspensión/reactivación o cambio de plan, procesar esa solicitud mediante un agente simulado y ver el resultado persistido en el panel.

El recorrido debe funcionar de extremo a extremo con PostgreSQL y el simulador, sin conectarse al MikroTik real ni requerir nuevas pruebas manuales del usuario en su pueblo. Implementar y verificar, no quedarse en otro documento de planificación.

## Lectura inicial

1. [README](../README.md) y [AGENTS](../AGENTS.md).
2. [Idea](idea.md), [arquitectura](arquitectura.md) y [adaptación a SpicyNet](adaptacion-spicynet.md).
3. [Red actual](red-actual.md) como contexto técnico; [preparación MikroTik](preparacion-mikrotik.md) y [prueba 011](prueba-cliente-011.md) para resultados y límites.

No releer ni ejecutar todos los comandos de los procedimientos. Varias secciones registran estados históricos: el cierre es lectura, API sin TLS deshabilitada y pruebas reales terminadas. Si se actualizan resúmenes, conservar la trazabilidad y corregir afirmaciones antiguas que parezcan actuales.

## Hechos ya comprobados

- MikroTik real `192.168.8.1`, RouterOS 6.49.23; control mediante IP, colas simples y lista Morosos. Se leyeron 15 colas.
- API-SSL/8729 habilitada con certificado `spicyops-api`, SAN IP:192.168.8.1, TLS 1.2 y origen .90/32. Certificado servidor vence el 16/10/2027. API/8728 deshabilitada.
- Raspberry .90: Raspbian 12 bookworm, ARMv6, Python 3.11.2, OpenSSL disponible y 512 MB de RAM reportados. Tailscale y lighttpd ya tienen funciones existentes que deben conservarse.
- En Raspberry se creó un entorno de diagnóstico con librouteros 4.2.2 según comandos/confirmación del usuario. TLS con cadena e IP y lectura autenticada funcionaron.
- Se comprobó escritura del mismo max-limit sobre el cliente 011/.62, manteniendo 2M/4M. No se ensayó un corte ni se midió desde esa vivienda. El grupo quedó finalmente con read,api,!write confirmado.
- No hay aplicación web ni agente permanente instalados. No se han probado tareas durables, reconexión de un agente permanente, altas nuevas o compatibilidad física en RouterOS 7.

## Entregables del primer incremento

### Panel y datos

Django, PostgreSQL y plantillas adaptables a móvil. Login y roles básicos; inventario de sitio, nodo físico, router/agente, cliente, servicio y plan. El cliente y su conexión técnica son entidades distintas. Un AP no crea por sí mismo un sitio o agente adicional.

Pantallas suficientes para listar clientes, abrir servicio, ver plan/ubicación/estado deseado y observado, solicitar acciones y consultar historial. Datos ficticios para demo; indicar claramente que se está en simulación. No mostrar el estado como aplicado hasta recibir y validar el resultado del agente.

### Tareas y API del agente

Guardar intención y tarea en una transacción. Entrega HTTPS prevista, identidad por agente y alcance por sitio, reclamación temporal, intentos, vencimiento y resultado. Una respuesta perdida puede causar repetición: deduplicar y reconciliar contra estado, sin prometer ejecución exactamente una vez.

Revisión creciente por servicio y serialización por router. Rechazar tareas de otro sitio, parámetros fuera de contrato y revisiones obsoletas. No aceptar comandos RouterOS arbitrarios desde el navegador.

### Agente y simulador

Proceso Python ligero que consulte tareas, aplique acciones permitidas en un simulador persistente de router y reporte verificación. Separar cliente de API central, ejecución de acciones y transporte RouterOS. El simulador debe implementar el mismo contrato de estado que el adaptador, no limitarse a devolver siempre OK.

Preparar adaptador librouteros con validación TLS para versiones 6/7 y configuración explícita, pero sin conexiones reales durante este encargo. La ejecución real queda deshabilitada por defecto. El contrato debe proteger infraestructura, validar unicidad y conservar colas generales, orden y burst.

### Operación y documentación

Configuración por entorno y archivos de ejemplo sin secretos; migraciones; datos de demo ficticios; arranque local breve con los runtimes disponibles. Preparar unidad systemd de ejemplo para el agente, sin instalarla en Raspberry. No asumir Docker ni binarios ARMv7/ARM64 disponibles; verificar herramientas antes de elegir cómo ejecutar PostgreSQL localmente. No cambiar globalmente el equipo del usuario para facilitar tests.

## Secuencia recomendada de implementación

1. Estructura mínima, dependencias compatibles, modelos, migraciones, login y demo.
2. Un recorrido vertical simulado: solicitar cambio de plan → reclamar tarea → aplicar en simulador → comprobar → reportar → mostrar resultado.
3. Agregar alta, suspensión y reactivación usando el mismo contrato, sin duplicar mecanismos.
4. Completar permisos, reintentos, revisiones y recuperación; ejecutar pruebas y revisar el comportamiento visible.
5. Entregar versión local revisable, instrucciones cortas y resultados concretos. No desplegar públicamente ni instalar en la red.

## Criterios de aceptación

- Desde el panel se crea un servicio ficticio y se recorren las cuatro acciones; el resultado coincide con el estado persistido del simulador.
- Repetir el alta no duplica usuario/cola simulados; repetir suspensión/reactivación conserva coherencia.
- Una tarea vencida u obsoleta no aplica el estado antiguo; dos consumidores no reclaman válidamente la misma tarea a la vez.
- Tras reiniciar los procesos y conservar PostgreSQL/estado simulado, la tarea y su resultado se recuperan o reconcilian sin falso éxito.
- Fallo antes de escribir, después de escribir y antes de reportar, y reporte repetido tienen resultados verificables y visibles.
- Un agente de otro sitio u operador sin permiso no ejecuta la acción. La identidad/destino no se acepta solo porque venga del navegador.
- Ninguna prueba necesita secretos de producción, tráfico al MikroTik real o intervención del usuario en clientes.
- Se distinguen pruebas unitarias, integración PostgreSQL y recorrido completo ejecutados. Una comprobación con mocks no sustituye PostgreSQL para bloqueos/transacciones.

Si no se dispone de PostgreSQL o de otra dependencia necesaria para verificar una garantía, avanzar en lo independiente y declarar la comprobación pendiente; no sustituir silenciosamente la cola por una en memoria ni afirmar éxito integral.

## Límites y autonomía

El usuario quiere que el agente trabaje, no volver a recibir decenas de comandos. Ejecutar localmente lo necesario dentro del alcance y entregar algo concreto. Pedir información solo ante un bloqueo real que no pueda resolverse con el repositorio.

El portal cautivo, facturación, pagos, WhatsApp, MQTT/RADIUS, actualización de RouterOS y despliegue público quedan fuera de este incremento. No hay autorización vigente para volver a modificar al cliente .62: su prueba temporal terminó. No abrir sesiones reales a Raspberry/MikroTik ni elevar permisos para completar la implementación local.

Conservar las fuentes sensibles intactas e ignoradas por Git. No incluirlas en demos, contenedores o artefactos de distribución. Documentar integración real futura como una fase distinta, sin presentar su falta como bloqueo del MVP simulado.

La estructura del encargo usa objetivo, contexto, límites y criterios de terminado, siguiendo la [guía oficial para trabajar con Codex](https://learn.chatgpt.com/guides/best-practices).

