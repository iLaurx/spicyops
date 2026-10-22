# RouterOS 6 frente a 7 para SpicyOps

Consulta: 16 de octubre de 2026. La captura inicial mostraba RouterOS 6.49.22; el export recibido después confirma **6.49.23** a las 15:25:48 de esa fecha. No se comprobó el estado en vivo. El [análisis de la red](red-actual.md) y la [adaptación](adaptacion-spicynet.md) usan este export como referencia vigente documental.

## Diferencias que afectan al proyecto

| Aspecto | RouterOS 6 | RouterOS 7 | Implicación |
|---|---|---|---|
| API tradicional y SSH | Disponibles | Disponibles | Es posible diseñar un adaptador común, validando comandos y respuestas por versión |
| REST | No disponible | Disponible desde 7.1beta4 | Es una opción adicional, no un requisito para automatizar |
| Evolución del sistema | Rama anterior | Incorpora cambios de funciones y del sistema de enrutamiento | Revisar la configuración al migrar; no asumir comportamiento idéntico |
| Recursos | El equipo ya funciona con la configuración mostrada, según la captura | La compatibilidad no garantiza igual rendimiento con la carga real | Medir CPU, RAM, espacio y tráfico en el piloto |
| Contenedores en RB750UPr2 | No es una opción | El paquete Container no admite MIPSBE | La Raspberry sigue siendo el lugar propuesto para el agente |
| Capacidad física | Puertos de 100 Mbps y recursos del modelo | Mismo hardware | La actualización no convierte los puertos en Gigabit ni aumenta RAM |

Para SpicyNet, los objetos principales son colas simples, address-list Morosos y sus reglas asociadas. El primer adaptador debe conservar horarios, orden de colas y referencias de servicio en ambas versiones. API/SSH estaban deshabilitados en el export; una salida posterior compartida por el usuario confirma SSH, API y API-SSL habilitados. Tras el paso de certificados, una salida posterior confirma `spicyops-api` y TLS only-1.2; ADDRESS sigue vacío. Una prueba posterior desde Raspberry confirmó TLSv1.2 y verificación de cadena/IP correcta. Sigue pendiente autenticación y lectura API; esta prueba de transporte no verifica el adaptador de clientes ni la compatibilidad con v7.

La API tradicional y REST están documentadas por MikroTik: [API](https://manual.mikrotik.com/docs/developer-guides/api/), [introducción de REST](https://help.mikrotik.com/docs/spaces/ROS/pages/47579162/REST%2BAPI). Los cambios de migración se describen en [Upgrading to v7](https://manual.mikrotik.com/docs/getting-started/upgrading-to-v7/).

## Qué significa para el hEX PoE lite

La ficha del RB750UPr2 indica arquitectura MIPSBE, CPU de 650 MHz, 64 MB de RAM y 16 MB de flash. El fabricante ofrece descargas v7 para el producto; eso no demuestra el rendimiento de la configuración del usuario. [Ficha oficial](https://mikrotik.com/product/RB750UPr2).

La guía de migración aconseja no ejecutar v7 con menos de 64 MB: este equipo está justo en ese umbral. La cantidad de clientes por sí sola no define su carga; importan tráfico, colas, reglas y funciones. El agente no debe alojarse en el router: las arquitecturas admitidas por Container son ARM, ARM64 y x86. [Migración](https://manual.mikrotik.com/docs/getting-started/upgrading-to-v7/), [Container](https://manual.mikrotik.com/docs/containers/).

## Recomendación

Diseñar SpicyOps con la API tradicional y compatibilidad comprobada por versión. Empezar la validación con el sistema existente, sin hacer de v7 una dependencia. No interpretar esta decisión como recomendación de conservar indefinidamente una versión concreta: revisar mantenimiento y seguridad por separado antes de producción.

Evaluar v7 cuando aporte una función necesaria, una actualización de mantenimiento pertinente o una política operativa que lo justifique. Cambiar a REST únicamente si simplifica una integración ya probada; mantener un adaptador evita acoplar las reglas comerciales a un transporte.

## Si se decide actualizar más adelante

Preparar inventario, respaldo binario y exportación saneada conservados fuera del router; registrar paquetes y RouterBOOT. La guía indica partir de una versión v6 estable o long-term actualizada antes de migrar. Elegir la ruta y versión de destino con la documentación vigente, espacio disponible y requisitos concretos del modelo; no fijar aquí una versión futura.

Realizarlo con ventana de mantenimiento, acceso local y procedimiento de recuperación, porque requiere reiniciar el equipo y puede interrumpir a los clientes. Probar DHCP/PPPoE, firewall, NAT, IPv6, colas, API, DNS y acceso desde Tailscale después de la migración. Si se necesita volver atrás, seguir el procedimiento compatible con las versiones y respaldos; no asumir que una copia de v7 restaura directamente en v6.

Esta documentación no autoriza ni ejecuta la actualización del router.
