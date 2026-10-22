# Investigación y decisiones tecnológicas

Fecha de consulta: 16 de octubre de 2026. Recomendaciones de diseño, no resultados de pruebas físicas. Las versiones exactas de dependencias se fijarán al comenzar la implementación y verificar compatibilidad.

Actualización con fuentes locales: el [análisis de SpicyNet](red-actual.md) confirma RouterOS 6.49.23 en el export y un esquema de control por IP/colas/Morosos. El primer adaptador será el definido en [adaptación](adaptacion-spicynet.md). Esta evidencia refuerza el uso de API tradicional y permite posponer PPPoE/RADIUS. API-SSL, API y SSH estaban deshabilitados al exportar; la salida posterior de servicios compartida por el usuario confirma que ya están habilitados. Después, el usuario confirmó mediante salida de terminal la asignación de `spicyops-api` y TLS only-1.2. La prueba posterior desde Raspberry validó TLSv1.2, cadena e IP con Verification: OK. La cuenta dedicada ya está configurada con read,api y origen .90/32. La última salida del servicio confirma ADDRESS .90/32 y la nueva prueba TLS fue correcta. Las reglas IPv4 de API ya se confirmaron activas y ordenadas. La lectura autenticada desde Raspberry confirmó identidad, RouterOS 6.49.23 (stable) y 15 colas. El cierre de API sin TLS ya se confirmó; API-SSL mantiene certificado, TLS 1.2 y .90/32. Faltan rechazo desde otro origen y operaciones de clientes. La Raspberry ya sirve como destino del portal y acceso Tailscale; el consumo debe presupuestarse junto con ambos servicios.

## Recomendación

Usar un monolito Django con PostgreSQL en un servidor central y un agente Python pequeño por sitio. La Raspberry consulta tareas por HTTPS y controla MikroTik por su API tradicional con TLS. Instalar el agente como servicio systemd, sin escritorio ni contenedores en la Raspberry del piloto. Mantener Tailscale para diagnóstico y mantenimiento.

Se elige esta combinación por el volumen inicial y para reducir componentes operativos. No se afirma que sea la mejor para cualquier ISP: debe revisarse si cambian las capacidades del equipo, el equipo de desarrollo o la escala.

## Cómo comunicarse con MikroTik

| Alternativa | Ventajas para este caso | Limitaciones | Decisión |
|---|---|---|---|
| API tradicional con TLS | Interfaz estructurada; permite diseñar compatibilidad con RouterOS 6 y 7 | Requiere configurar y verificar certificados y probar operaciones concretas | Primera opción |
| SSH con Paramiko | Puede aprovechar experiencia y scripts del colega | Mayor cuidado con cadenas de comandos, respuestas y claves del servidor | Alternativa si la prueba de API revela un impedimento |
| REST sobre HTTPS | Integración HTTP/JSON accesible para desarrollo web | Requiere RouterOS 7; no está en el 6.49.23 del export | Adaptador futuro |
| RADIUS / FreeRADIUS | Centraliza autenticación, autorización y accounting en escenarios compatibles | Cambia la arquitectura de acceso y añade dependencia operativa para nuevas autenticaciones | Evaluar cuando exista esa necesidad |

La API tradicional utiliza por defecto 8728 y 8729 para la variante segura. La opción recomendada es API-SSL con certificado validado y acceso limitado al agente. La biblioteca candidata es `librouteros`; su documentación describe autenticación para versiones posteriores a 6.43. Esa coincidencia no sustituye la prueba con el router real. Fuentes: [API de MikroTik](https://manual.mikrotik.com/docs/developer-guides/api/), [conexión de librouteros](https://librouteros.readthedocs.io/en/latest/connect.html).

Algunos ejemplos de librouteros desactivan la validación del certificado: no deben copiarse así al proyecto. Si API-SSL no resulta viable en el equipo, se evaluará SSH con verificación de la clave del router antes de elegir otra vía. No se degradará silenciosamente a una conexión sin cifrar. [Cliente SSH de Paramiko](https://docs.paramiko.org/en/stable/api/client.html).

REST aparece a partir de RouterOS 7.1beta4. No hace falta migrar para disponer de automatización. La referencia inicial era 6.49.22 en la captura; el export recibido posteriormente confirma 6.49.23. [Referencia de REST](https://help.mikrotik.com/docs/spaces/ROS/pages/47579162/REST%2BAPI).

## Dónde ejecutar el control

| Enfoque | Evaluación |
|---|---|
| Agente local que consulta HTTPS | Elegido: conexión saliente, credenciales de router por sitio y acceso local incluso con direcciones repetidas en otros sitios |
| Servidor central accediendo por Tailscale a cada MikroTik | Válido para un piloto pequeño, pero concentra credenciales y depende de rutas/ACL por sitio; podría simplificar si se decide prescindir del agente |
| Peticiones entrantes a cada Raspberry | Posible por Tailscale, pero no aporta suficiente ventaja inicial frente a consultas salientes |
| Instalar toda la aplicación en la Raspberry | No recomendado con 512 MB y funciones de acceso remoto ya presentes; mezclaría panel, base de datos y agente |
| Instalar la aplicación dentro del MikroTik mostrado | Descartado: RB750UPr2 es MIPSBE y esa arquitectura no está entre las admitidas por el paquete Container |

El fabricante documenta 64 MB de RAM, 16 MB de flash y cinco puertos 10/100 para este router. Esas capacidades aconsejan limitar consultas y no asumir margen para cargas adicionales. [Ficha del equipo](https://mikrotik.com/product/RB750UPr2), [requisitos de Container](https://manual.mikrotik.com/docs/containers/).

Tailscale permite acceder a dispositivos sin cliente Tailscale mediante un subnet router. Mantenerlo para administración no obliga a que el agente lo use para recoger tareas. Si se centralizara el control mediante subredes, habría que resolver redes superpuestas; los agentes locales evitan ese problema para sus operaciones. [Subnet routers](https://tailscale.com/docs/features/subnet-routers), [redes entre sitios](https://tailscale.com/docs/features/site-to-site).

## Panel, almacenamiento y entrega de tareas

| Pieza | Elección inicial | Motivo y alternativa |
|---|---|---|
| Aplicación | Django, línea soportada; 5.2 LTS como candidata | Autenticación, ORM y administración disponibles; FastAPI sería razonable para una API independiente con un frontend separado |
| Interfaz | Plantillas Django y CSS adaptable a móvil | Evita una segunda aplicación en el MVP; React puede incorporarse si aparecen necesidades de interacción que lo justifiquen |
| API del agente | Django REST Framework | Contratos y validación HTTP; identidad de agentes separada de las sesiones humanas |
| Datos y cola | PostgreSQL | Una transacción puede guardar intención, tarea y auditoría; no hace falta mantener Redis o un broker inicialmente |
| Agente | Python y librouteros; HTTPS mediante biblioteca mantenida | Comparte lenguaje con el backend; comprobar instalación y consumo en la CPU real |
| Servicio local | systemd y registro local mínimo en SQLite | Reinicio supervisado y persistencia de resultados pendientes; no alojar el CRM localmente |
| Despliegue central | Servidor Linux con HTTPS y PostgreSQL, preferentemente administrado | El hosting concreto y su costo se deciden después del piloto; necesita persistencia, copias y restauración |

La autenticación de Django cubre usuarios y permisos; los roles específicos del negocio se configuran en el proyecto. Los bloqueos transaccionales de PostgreSQL/Django sirven para reclamar tareas evitando que dos procesos tomen la misma fila; no garantizan una única ejecución en el router. [Django: autenticación](https://docs.djangoproject.com/en/5.2/topics/auth/), [bloqueo de filas](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [PostgreSQL SELECT](https://www.postgresql.org/docs/current/sql-select.html), [DRF: autenticación](https://www.django-rest-framework.org/api-guide/authentication/).

## HTTPS frente a MQTT

Para el piloto se propone consultar cada 15 segundos con variación aleatoria. Es un parámetro de diseño ajustable, no una garantía de latencia. Una cola en PostgreSQL almacena las solicitudes; la Raspberry nunca se conecta directamente a la base de datos.

MQTT con Mosquitto es una alternativa válida para comunicación persistente y eventos frecuentes. Añadiría broker, permisos de temas y supervisión; tampoco elimina la necesidad de deduplicar tareas ni verificar cambios. Se reconsiderará si la cantidad de sitios o la latencia requerida hace inconvenientes las consultas HTTP. [Documentación de Mosquitto](https://www.mosquitto.org/documentation/).

## Raspberry de 512 MB

512 MB justifican probar un agente de alcance reducido; no permiten asegurar compatibilidad ni estabilidad sin conocer modelo, CPU, sistema operativo y carga de Tailscale y portal. Una inspección posterior confirmó lighttpd loaded/active/running y sockets escuchando en TCP/80; falta validar respuesta y flujo desde clientes. Raspberry Pi OS Lite ofrece una variante sin escritorio y opciones de arquitectura para equipos antiguos. No se propone reinstalar la Raspberry que ya funciona. [Raspberry Pi OS](https://www.raspberrypi.com/documentation/computers/os.html).

Comenzar con una sola operación simultánea por router, consultas acotadas y sin recopilar tráfico continuamente. Objetivo experimental del agente: RSS inferior a 80 MB, sin crecimiento sostenido; debe medirse junto con memoria disponible, CPU, temperatura, swap y estabilidad de Tailscale. Este presupuesto es una meta propia, no una especificación del fabricante. Si falla, revisar dependencias y frecuencia; después evaluar un agente Go o reemplazar hardware, según la causa.

## Construir frente a adoptar

Antes de invertir en facturación completa conviene evaluar una solución existente. Splynx documenta integración MikroTik DHCP/RADIUS, aunque debe verificarse su ajuste al esquema real y costo mediante una evaluación aparte. UISP tiene CRM y suspensión integrada, pero su guía vincula esas funciones a gateways UISP/EdgeRouter: no debe asumirse equivalente para el MikroTik actual. [Splynx: DHCP/RADIUS](https://wiki.splynx.com/network-management/authentication_of_customers/mikrotik_dhcp_radius), [UISP: suspensión y velocidad](https://help.uisp.com/hc/en-us/articles/22590998317719-UISP-Suspension-Traffic-Shaping-and-Aggregation).

Construir SpicyOps se justifica si se busca un flujo propio y control sobre agentes e integración. FreeRADIUS se reconsiderará cuando centralizar autenticación/accounting de PPPoE o HotSpot sea un requisito; no es un reemplazo por sí solo del CRM. [Documentación de FreeRADIUS](https://www.freeradius.org/documentation/), [RADIUS en MikroTik](https://manual.mikrotik.com/docs/authentication-authorization-accounting/radius/).
