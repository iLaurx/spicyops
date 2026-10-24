# Encargo vigente: SpicyOps para Windows

Reemplaza el primer MVP local por indicación expresa del usuario. La aplicación anterior y sus pruebas quedan como evidencia histórica; no son la experiencia que se debe seguir ofreciendo.

El usuario administra varias localidades, cada una con Raspberry y MikroTik. Accede mediante SSH —por red local o Tailscale— y quiere conectar una localidad, verificar su router y recibir automáticamente la información. Aceptó un programa Windows como alternativa a un sitio público; esta opción aprovecha su acceso de red existente y evita publicar SSH o instalar PostgreSQL manualmente.

## Experiencia

1. Abrir `SpicyOps.exe`. Analytics, Clientes y Conexiones son la navegación principal. La instalación comienza vacía, sin datos de demostración.
2. Conectar una localidad indicando dirección/usuario SSH, contraseña o clave Windows y acceso API de lectura. Confirmar la huella SSH del equipo la primera vez. Mantener certificado de MikroTik validado.
3. Comprobar Raspberry y MikroTik, leer identidad/versión/uptime, colas y contadores. Crear automáticamente la lista de servicios; separar infraestructura y colas compartidas. No interpretar una cola como una persona jurídicamente identificada ni como prueba de acceso efectivo a internet.
4. Consultar consumo observado en Analytics y actualizar la lectura. La aclaración del usuario del 19 de octubre de 2026 conserva las tarjetas y lista de estimados a 24 horas/30 días usando exclusivamente la aproximación por uptime, identificada como tal. Se retiran selector, periodo analizado y proyecciones entre lecturas. Se conserva la gráfica de diferencias observadas con fechas y colores por día.
5. Consultar Clientes, velocidades en Mbps o MB/s y consumo en GB. Editar nombre visible, contacto, ubicación y notas de SpicyOps. Conservarlos al actualizar la lectura. Las velocidades, IP y contadores proceden del router y no se modifican en este incremento.
6. Agregar/configurar/desconectar localidades independientes. Al desconectar se retiran contraseñas, se conserva la última lectura y los datos complementarios. Reconectar el mismo perfil no duplica localidad ni pierde notas.

## Ampliación: control de morosidad

Por solicitud posterior del usuario, Clientes incorpora un botón por servicio para suspender por adeudo o quitar de Morosos. Esta ampliación autoriza implementar y probar localmente la acción; no reabre el ensayo de Lulu ni autoriza ejecutar cambios en la red durante el desarrollo. La acción real solo se envía cuando el operador confirma cliente, IP y localidad en el programa.

El conector mantiene las cuatro rutas de lectura y añade únicamente `/ip/firewall/address-list/add` y `/ip/firewall/address-list/set`, con lista fija `Morosos` e IP individual validada contra el inventario recién leído. No acepta comandos ni destinos libres del navegador. Crear/habilitar suspende; deshabilitar la entrada individual retira la restricción. No cambia permisos ni instala reglas. Requiere cuenta con escritura y firewall existente adecuado. Se rechazan colas ambiguas/deshabilitadas y restricciones activas compartidas o dinámicas, además de entradas individuales duplicadas. El estado mostrado procede de lectura posterior, sin equipararlo a una comprobación física de internet. No contempla suspensión automática por fecha ni cobros.

## Cálculo

La auditoría del 22/10/2026 añade revisión local de colas excluidas: conserva el filtro predeterminado y permite incluir/revertir únicamente una cola IPv4 individual válida de la última lectura. La excepción se vincula a localidad, ID, nombre e IP, y se revalida contra el inventario fresco para Morosos. No admite destinos compartidos/múltiples, IPv6, ambigüedad ni valores inválidos. El navegador solicita una identidad observada; no puede desactivar protecciones mediante una bandera.

Morosos interpreta IPv4, CIDR y rangos inclusivos con el mismo contrato en normalización, validación previa y confirmación posterior. Una restricción activa compartida/dinámica aplicable o activa no interpretable impide un cambio individual seguro. Los fallos de escritura/confirmación exigen sincronizar antes de reintentar.

En la gráfica: `bytes del intervalo = contador final − contador inicial`. Se incluyen subida y bajada. Las estimaciones usan contador acumulado / uptime × horizonte (86400 segundos o 30 veces ese valor); la edad real del contador no está confirmada. Se excluyen resets/cambios conocidos y colas ambiguas. GB y Mbps son unidades decimales. `MB/s = Mbps / 8`.

No mezclar épocas de arranque, descensos de contadores individuales o cambios de identidad de cola. Uptime del router no prueba cuándo se creó o reseteó una cola. No ofrecer las proyecciones como facturación ni medición histórica mensual. No fabricar gráficos o cifras cuando falta conexión/intervalo.

Los descensos se detectan entre lecturas consecutivas, por cada dirección. Se conserva su invalidación durante esa época incluso si el contador recupera el valor anterior o se elimina la lectura antigua por el límite de 1440 muestras. La migración inicial consulta el historial retenido; no reconstruye resets anteriores a ese historial ni no observados.

## Implementación y límites

Las operaciones tienen presupuesto global de 60 segundos, incluidos DNS y cierre. DNS usa como máximo dos hilos daemon sin credenciales; las comunicaciones tienen cuatro cupos fijos para contener bloqueos de biblioteca/sistema sin impedir salir. El coordinador conserva dos lecturas automáticas concurrentes y una operación por localidad. Su instantánea de programación no contiene credenciales/historial: se invalida con la firma del archivo bajo el bloqueo y el trabajo vuelve a leer el perfil vigente. Se conserva el archivo cifrado único y su coste en lecturas completas/escrituras necesarias. El encargo posterior de release 1.0.0 autoriza respaldos, recuperación y traslado cifrado; consultar docs/guia-publica.md.

Interfaz Django con servidor embebido y ventana de aplicación de Edge; empaquetado Windows con Python y dependencias incluidos. La configuración actual no usa ORM, PostgreSQL ni migraciones. Un archivo de estado cifrado por instalación conserva perfiles, metadatos y hasta 1440 lecturas por localidad; la clave de la versión empaquetada se protege con DPAPI del usuario Windows. La distribución no contiene ese estado.

El conector SSH corre en Windows; el lector remoto usa Python estándar y librouteros existente en Raspberry (3.11/ARMv6 contemplados). Solo cuatro rutas RouterOS `/print` permitidas, más la acción cerrada de Morosos descrita arriba. No se ejecutan instaladores, reinicios ni cambios de permisos. Conectar y sincronizar no escriben en RouterOS. Fuentes sensibles permanecen intactas.

El usuario introduce secretos en el formulario del programa, nunca en el chat. El servidor escucha únicamente en loopback, tiene sesión firmada de apertura y CSRF. No es un panel web públicamente desplegado. Una versión hospedada requeriría decidir autenticación, persistencia central y comunicación saliente/VPN hacia las localidades; no se declara publicada por haber empaquetado Windows.
