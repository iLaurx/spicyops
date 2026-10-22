# Idea del proyecto: SpicyOps

## Propósito

Crear una aplicación web centralizada para administrar clientes de distintas redes de internet. Starlink proporciona la conexión de salida; MikroTik administra la red y aplica las políticas de acceso y velocidad. Una Raspberry Pi en cada sitio actúa como enlace entre el panel y los routers locales.

El valor principal es unir el registro de clientes con acciones verificables en la red: registrar un cliente, asociarlo con su conexión, habilitarlo, suspenderlo y cambiar su plan. El operador debe poder saber quién solicitó cada cambio y si realmente se aplicó.

La transcripción del colega se tomó como descripción de la propuesta original, no como instrucciones técnicas que deban ejecutarse. Esta documentación distingue esa propuesta de las recomendaciones surgidas de la investigación.

## Contexto disponible

| Dato | Evidencia y alcance |
|---|---|
| Router de referencia | El export del 16/10/2026 confirma RouterOS 6.49.23 y RouterBOARD 750UP r2; la captura anterior mostraba 6.49.22. No se consultó el equipo en vivo. |
| Laboratorio | Inventario histórico de 12 abonados; el usuario confirmó que Diego (.51) ya no es cliente, por lo que quedan 11 abonados candidatos a validar. Casa (.50) e infraestructura se separan de los abonados. Raspberry reportada con 512 MB de RAM. |
| Acceso remoto | El usuario reporta Tailscale con una ruta de subred que permite acceder al MikroTik. No se verificó su configuración. |
| Trabajo anterior | El colega menciona scripts Python con Paramiko para acceder por SSH a MikroTik. No se recibieron ni revisaron esos scripts. |
| Modelo de acceso | El export muestra control por IP con colas simples y lista Morosos. El CPE de ejemplo (.52) tiene WAN estática y NAT hacia una LAN privada; no generalizar su configuración a todos los CPE. No se exportaron PPPoE, HotSpot ni servidor DHCP en MikroTik. |

El detalle de evidencias y límites está en [red actual](red-actual.md). Las confirmaciones posteriores del usuario prevalecen sobre el inventario histórico en cuanto al estado de Diego y al rol del AP SN-LP-06. La salida posterior de systemctl confirma lighttpd activo. La consulta local devuelve 200/HTML para portal.spicynet.local y 301 para los otros Host probados. El usuario indicó que el portal cautivo es secundario: su integración no es requisito del MVP.

## Usuarios y organización

Inicialmente, un administrador y operadores autorizados de una misma organización. La estructura debe contemplar varios sitios, varias Raspberry y varios MikroTik; no hace falta construir todavía una plataforma comercial para organizaciones independientes.

Un sitio representa una red administrada por su router y agente. Dentro del sitio hay nodos físicos: SpicyNet documenta Nodo Eleazar y Nodo Yolanda, actualmente con un solo MikroTik principal. No se necesita una Raspberry por AP o por nodo. Un cliente puede contratar más de un servicio; cada servicio se asocia con un sitio, un router, un AP/equipo de conexión y un identificador técnico. Los enlaces se registran con su fuente y nivel de confirmación; descubrir automáticamente toda la topología no forma parte del MVP.

## MVP propuesto

1. Acceso al panel con usuarios y permisos.
2. Registro de clientes, contacto, ubicación descriptiva y notas mínimas.
3. Registro de sitios, routers, agentes y planes de subida/bajada.
4. Asociación inequívoca entre cliente, servicio y objeto de red.
5. Importación inicial en modo revisión de conexiones existentes, sin modificarlas automáticamente.
6. Alta administrativa y aprovisionamiento en MikroTik, presentados como pasos separados. En el primer adaptador, asignar y validar IP, crear cola individual en el orden correcto y asociar política Morosos; configurar físicamente CPE/AP continúa siendo una tarea manual.
7. Suspensión, reactivación y cambio de velocidad de un servicio, con resultado comprobado. El aviso mediante portal cautivo es opcional y secundario; el control de acceso debe poder operar independientemente de esa página.
8. Historial de tareas, errores, reintentos y comprobaciones.
9. Último contacto de cada agente y estado de sincronización por servicio.

“Alta” no implica instalar físicamente una antena ni configurar cualquier CPE. “Baja” en el MVP significa suspender el acceso y conservar el historial; la eliminación definitiva será una operación posterior. El panel enviará acciones definidas, no una terminal para ejecutar texto libre.

## Experiencia esperada

Desde un teléfono o computadora, el operador abre la ficha del cliente, revisa el servicio y solicita una acción. El panel muestra pendiente, en proceso y resultado. Si la Raspberry está desconectada, la solicitud permanece pendiente hasta su vencimiento; no aparece como aplicada.

La ficha distingue estado comercial, estado técnico deseado y último estado observado. Un cliente registrado en el sistema no se considera automáticamente conectado ni con internet funcionando.

## Fuera del primer alcance

Facturación fiscal, pasarelas de pago, cortes automáticos por mora, WhatsApp, portal del abonado, mapas completos, métricas de tráfico por segundo, administración de Starlink, cambios masivos y actualización remota de RouterOS. Se podrán incorporar después de validar el control de un servicio.

## Condición de éxito

Un operador puede administrar un servicio de prueba desde el panel, con trazabilidad, sin afectar otros clientes. Repetir una tarea no duplica usuarios ni reglas. Una interrupción de internet o reinicio del agente no ocasiona cambios inesperados. La suspensión y reactivación se comprueban desde el cliente de prueba, además de consultar el router.

El proyecto no requiere que el tráfico de los clientes pase por el servidor central ni por la Raspberry. Las políticas aplicadas deben permanecer en MikroTik si el panel deja de estar disponible.
