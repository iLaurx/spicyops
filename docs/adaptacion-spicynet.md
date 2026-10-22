# Adaptación del MVP a la red SpicyNet

Basada en [red actual](red-actual.md), el export RouterOS 6.49.23 y las aclaraciones del usuario del 16/10/2026. Son decisiones de diseño; no se ejecutaron en equipos.

## Decisión principal

Conservar Django, PostgreSQL y agente Python. Implementar primero un adaptador de **IP estática + cola simple + política Morosos** para MikroTik, compatible con RouterOS 6 y 7. No migrar a PPPoE ni incorporar RADIUS para satisfacer el primer MVP. Las antenas se inventarían y relacionan con servicios, pero no se reconfiguran automáticamente.

El sitio piloto contiene un MikroTik y una Raspberry con varios nodos/AP. El esquema debe distinguir sitio administrado, nodo físico, equipo, enlace y servicio. Un AP no obliga a desplegar un nuevo agente. Guardar el recorrido conocido hacia el cliente y marcar los enlaces inferidos o pendientes.

## Contrato del primer adaptador

| Operación | Cambios previstos y comprobaciones |
|---|---|
| Adoptar servicio existente | Relacionar IP/CPE/AP, cola única y posible entrada Morosos; conservar orden, límites, burst y estado observados; revisión antes de marcarlo administrado |
| Alta técnica | IP aprobada sin conflicto, CPE instalado/configurado manualmente, cola individual antes de Default Queue y después de la política nocturna; estado inicial restringido hasta comprobación final |
| Suspender | Activar la entrada individual Morosos adoptada; si falta, crear solo una entrada para ese servicio con política definida. Mantener su cola de velocidad |
| Reactivar | Desactivar la entrada Morosos administrada, conservar su referencia y comprobar que no haya otra entrada activa aplicable; no cambiar reglas generales |
| Cambiar plan | Actualizar únicamente límites del servicio y burst explícitamente acordado. No reordenar colas ni modificar perfiles/políticas compartidas |
| Baja administrativa | Conservar historial y suspensión verificada; retirar IP/cola solo en un flujo posterior, evitando que Default Queue vuelva a dar acceso al CPE |

Una cola no autoriza acceso: el estado de restricción se controla por firewall. Agregar primero una cola para un CPE ya conectado puede darle el nuevo límite antes de completar el alta; el aprovisionamiento debe analizar y contener ese intervalo. Tampoco una entrada Morosos por sí sola es efectiva si faltan sus reglas: la lectura inicial debe validar la política del router y bloquear escrituras si no coincide con el contrato aprobado.

Se propone adoptar la lista existente `Morosos`, sin renombrarla ni reemplazar sus reglas automáticamente. El panel puede ofrecer “Suspender servicio”, pero no debe presentar la política vigente como aislamiento absoluto mientras permite DNS. Por indicación del usuario, el portal cautivo es secundario: su reparación y pruebas adicionales quedan aplazadas y no condicionan altas, suspensión/reactivación ni límites de velocidad. El aviso y el control efectivo de acceso se tratan como capacidades separadas.

## Importación inicial

Importar una sola variante de cada CSV y normalizar espacios en encabezados/nombres. Separar una IP de las URL `https://...`; no tratar esas URL como direcciones distintas ni como evidencia de HTTPS operativo. Relacionar fichas de Notion y `.cfg` por equipo y dirección, no por nombre únicamente.

La vista previa debe mostrar 2 nodos, 6 equipos de inventario, 12 registros históricos de abonados, Casa y Default Queue. Clasificar Diego .51 como baja histórica y once abonados .52–.62 como candidatos por confirmar. Agregar Raspberry .90 como infraestructura a partir de las fuentes del router y notas, sin duplicarla por el prefijo `001`.

No importar columnas Password/Contraseña/Pass al CRM ni guardar hashes de acceso en auditoría. Las credenciales de gestión requieren un almacén separado con acceso restringido; para el primer agente, archivo local protegido y usuario dedicado. Guardar referencias a secretos, no su valor, en registros del proyecto.

El AP SN-LP-06 conserva sus relaciones de Notion con .61/.62, rol AP confirmado y uplink pendiente. No inventar modelo, banda o configuración. El `.cfg` .52 confirma solo el esquema de ese abonado. `.56/FREE` necesita una decisión comercial explícita antes de permitir su suspensión.

## Protección de infraestructura y reglas existentes

Excluir del selector de cortes comerciales el gateway .1, antenas .2–.6, Casa .50, Raspberry .90 y objetivos `/24`. El servidor y el agente deben rechazar intentos de aplicar acciones de abonado a infraestructura, incluso si alguien altera una petición del navegador.

Preservar `Descanso_Madrugada`, `Default Queue`, sus posiciones y los dos schedulers. Los límites base de cada servicio se almacenan aparte de la política nocturna, para que una reducción global no parezca un cambio individual de plan. No interpretar el nombre `Apagar_Red` como una orden de apagar WAN.

La Raspberry tiene al menos dos roles documentados o previstos además del agente: subnet router Tailscale y destino del portal HTTP. El agente no debe ocupar puerto 80, cambiar el servicio web, reemplazar su firewall ni reiniciar servicios para instalarse. Su comunicación al panel será saliente. Verificar recursos combinados antes de desplegar.

## Compatibilidad RouterOS 6 y 7

Usar API tradicional cifrada y operaciones sobre `/queue/simple`, `/ip/firewall/address-list` y lectura de reglas/servicios/schedulers. No depender de REST, contenedores ni de propiedades exclusivas de v7. Evitar números de fila de WinBox: consultar IDs del router en cada sesión y validar coincidencia por IP, referencia de servicio y objeto adoptado antes de escribir.

Registrar versión y capacidades observadas. Los adaptadores deben normalizar valores y errores sin asumir que todos los campos son iguales entre versiones. La integración con v6.49.23 y con una versión v7 elegida para pruebas se verifica por separado; la compatibilidad es un objetivo hasta superar esa matriz. REST podría añadirse como otro transporte, conservando las mismas reglas de negocio.

API/SSH figuraban deshabilitados en el respaldo. Una salida posterior de `/ip service print` compartida por el usuario confirma SSH 22, API 8728 y API-SSL 8729 habilitados. Una salida más reciente confirma certificado `spicyops-api`, SAN IP:192.168.8.1 y TLS only-1.2; vence el 16/10/2027. ADDRESS sigue vacío. La prueba posterior desde Raspberry confirmó TLSv1.2 y Verification: OK con comprobación de IP. La cuenta spicyops-agent ya está habilitada con read,api y origen .90/32 según salida compartida. El servicio API-SSL ya muestra origen .90/32 y la prueba TLS posterior fue correcta. El filtro IPv4 de API ya está confirmado activo y ordenado, con nueva prueba TLS correcta desde Raspberry. La lectura autenticada desde Raspberry ya confirmó identidad, RouterOS 6.49.23 (stable) y 15 colas simples. El servicio API sin TLS ya está deshabilitado según salida compartida; API-SSL conserva .90/32, certificado y TLS 1.2. Faltan prueba de rechazo desde otro origen y operaciones de clientes. No usar API sin TLS como transporte de producción por conveniencia; Tailscale en la Raspberry no cifra automáticamente su tramo LAN al MikroTik.

## Pruebas específicas antes del primer cambio real

1. Confirmar IP fija y titularidad del CPE de prueba; asegurar que ningún otro abonado comparte su dirección aguas arriba. Un ping sin respuesta no demuestra que una IP esté libre.
2. Verificar API-SSL, permisos y lectura sin modificar; conservar Tailscale y no alterar el servicio web existente.
3. Adoptar un solo servicio y comparar cola, burst, posición y entrada Morosos antes y después de una operación simulada.
4. Probar suspensión/reactivación con tráfico nuevo y existente, DNS, HTTP, HTTPS e IPv6 cuando esté disponible. No limpiar globalmente connection tracking. Comprobar que no se afecta administración ni otros abonados.
5. Opcional y aplazado: ensayar el flujo de portal aparte solo cuando se retome esa función. No es criterio de aceptación del control de clientes.
6. Verificar que crear/retirar una cola no deja un abonado con acceso inesperado por Default Queue. Ensayar la prioridad nocturna con un horario temporal de laboratorio o entorno aislado, sin alterar los schedulers del servicio actual.
7. Repetir casos de tareas duplicadas, obsoletas y recuperación tras reinicio. Un cambio manual en WinBox se muestra como discrepancia; no se revierte de forma automática.

Fuentes técnicas: [colas y orden](https://help.mikrotik.com/docs/spaces/ROS/pages/328088/Queues), [address-lists](https://help.mikrotik.com/docs/spaces/ROS/pages/130220135/Address-lists), [NAT y connection tracking](https://help.mikrotik.com/docs/spaces/ROS/pages/3211299/NAT), [API](https://manual.mikrotik.com/docs/developer-guides/api/). Las conclusiones sobre la configuración concreta proceden de las fuentes locales identificadas en red actual.
