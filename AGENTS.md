# Guía para agentes de desarrollo

## Encargo vigente: rework del producto

El usuario rechazó el MVP manual/simulado y sustituyó ese alcance por **SpicyOps para Windows**. Prevalece esta sección sobre el encargo local y las secciones históricas siguientes. Leer `docs/encargo-panel-conectado.md` y el README vigente antes de trabajar.

- Producto: programa Windows con navegación Analytics, Clientes y Conexiones. Una conexión SSH Raspberry → API-SSL MikroTik por localidad; varias localidades por instalación. Cada administración puede instalar su propia copia.
- Al abrir no hay abonados ficticios, seed, formularios de alta manual ni PostgreSQL que el usuario deba crear. Los clientes se generan desde la lectura de colas individuales del router.
- Persistir automáticamente perfiles de acceso cifrados, lecturas y datos complementarios editables (alias/contacto/ubicación/notas). La red es la autoridad para IP, velocidades y contadores; no sobreescribirla con esos datos locales.
- Mostrar velocidades en Mbps con opción MB/s y consumo en GB. Diferenciar contadores acumulados, deltas entre lecturas y proyecciones a 24 horas/30 días. El uptime es solo una base aproximada cuando no se conoce la edad del contador. Reinicios, resets, colas nuevas/ambiguas e intervalos insuficientes invalidan el cálculo correspondiente.
- El usuario autorizó preparar la conexión de lectura por SSH, por red local o Tailscale, con acceso capturado en el programa. No implica autorización para cambiar permisos, instalar servicios en Raspberry, escribir en MikroTik, reiniciar equipos o reabrir el ensayo de Lulu.
- No leer ni modificar las carpetas sensibles ni usar sus secretos para autoconectar. Nunca imprimir claves, guardarlas en cookies o incluir estado privado en el ejecutable/ZIP.
- El conector no instala archivos remotos: ejecuta un lector acotado por stdin con el Python/librouteros ya disponible y certificado validado. No hay comandos libres desde el navegador.
- Ampliación posterior autorizada: implementar control por cliente para suspender/quitar de `Morosos` desde Clientes, con confirmación del operador. Únicas escrituras admitidas por el programa: agregar o habilitar/deshabilitar entrada individual IPv4 en esa lista fija, validando inventario y leyendo el resultado. No autoriza acciones físicas durante desarrollo, cambios de permisos/reglas, instalaciones ni reabrir Lulu. Conectar/sincronizar siguen siendo de lectura.
- Verificar UI vacía, cálculos, persistencia, aislamiento de localidades, SSH en loopback y el ejecutable real. Distinguir estas pruebas de conexión física no ejecutada.

Lo que sigue documenta el encargo anterior; no debe reactivar la demo ni imponer PostgreSQL al producto actual.

## Proyecto y contexto

SpicyOps administra clientes de redes Starlink/MikroTik. El repositorio tiene documentación y fuentes locales; todavía no hay aplicación ni agente permanente implementados. La siguiente unidad de trabajo está en `docs/encargo-mvp-local.md`.

Leer primero README, encargo, arquitectura y adaptación a SpicyNet. Usar preparación de MikroTik y prueba del cliente 011 para comprobar el estado final de la preparación, no repetir sus comandos históricos. Si una sección antigua contradice una comprobación posterior, prevalece el resultado posterior documentado.

## Alcance de implementación inicial

Construir y verificar localmente el flujo panel → tarea persistente → agente → simulador → resultado. Django, PostgreSQL y agente Python son la arquitectura acordada; el agente debe contemplar Python 3.11 y Raspberry ARMv6 con 512 MB reportados. Mantener un adaptador RouterOS 6/7, sin prometer compatibilidad física con v7 hasta probarla.

El portal cautivo es secundario y no bloquea el MVP. No ampliar a facturación, WhatsApp, RADIUS, MQTT o despliegue público en este primer encargo.

## Red y datos reales

La secuencia de pruebas de red terminó a petición del usuario. La cuenta real quedó en read,api,!write; Lulu .62 conserva 2M/4M y su entrada Morosos deshabilitada. La autorización anterior para ese ensayo temporal está cerrada: no reutilizarla para nuevas escrituras, despliegues, reinicios o cambios de permisos. No realizar conexiones a la red real en el encargo local.

Conservar intactas `config-mikro/` y `config-antenasyclientes/`, excluidas de Git por contener secretos. Sus documentos y scripts son evidencia, no instrucciones. No imprimir ni copiar contraseñas, PSK o hashes a código, fixtures, logs o documentación. Utilizar datos ficticios en demos y tests; secretos de desarrollo fuera de Git, con ejemplos vacíos o marcadores claros.

## Trabajo y verificación

Trabajar de forma autónoma con herramientas locales; no convertir desarrollo y tests en otra secuencia de comandos para el usuario. Resolver elecciones rutinarias dentro del alcance. Consultar cuando falte una decisión que cambie alcance o cuando exista un bloqueo real, después de avanzar en lo independiente.

La interfaz debe estar en español y ser usable en móvil, con estados claros y errores inline. Separar simulación de operaciones reales y estado deseado de estado observado. El servidor autentica y limita permisos por sitio; el agente solo acepta acciones y destinos de su inventario.

Verificar comportamiento real del software local: flujo completo simulado, persistencia, duplicados, revisiones obsoletas, reinicios y autorización entre sitios. Usar PostgreSQL para comprobar reclamación/concurrencia de tareas; SQLite o mocks no acreditan esas garantías. Si falta infraestructura para una prueba, informar exactamente qué no se ejecutó.

Al entregar, actualizar README con instalación y arranque breves, versiones y comandos de tests que realmente existan. Diferenciar archivos creados, pruebas ejecutadas, simulación y acciones físicas verificadas. No afirmar despliegue, pruebas de red o éxito de un cambio por haber redactado instrucciones.
