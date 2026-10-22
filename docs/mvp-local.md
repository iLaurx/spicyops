> ARCHIVO HISTÓRICO DEL PRIMER ENCARGO. El usuario sustituyó el producto manual/simulado por SpicyOps para Windows. Ver [encargo vigente](encargo-panel-conectado.md) y [README](../README.md). Las pruebas anteriores no acreditan la conexión física ni describen la interfaz actual.

# MVP local implementado

Fecha: 16/10/2026. Sustituye las afirmaciones históricas de que todavía no existe aplicación **local**. No cambia el cierre del ensayo real ni acredita una instalación en Raspberry.

## Componentes

`spicyops/` contiene configuración Django/WSGI y rutas. `ops/` contiene modelos, migraciones, formularios, panel en español y cola. `agent/` separa cliente HTTP, contrato, ejecución, simulador y transporte RouterOS. `tests/` tiene pruebas unitarias, PostgreSQL y HTTP con agentes como procesos independientes. `scripts/local.ps1` prepara/arranca/detiene el laboratorio; `deploy/` contiene ejemplos para una instalación futura.

El panel distingue cliente de servicio y sitio de nodo/AP. La demo usa nombres e IP de documentación, no importa ninguna fuente real. Los usuarios tienen membresías por sitio: consulta, operador y administrador; estos dos últimos pueden solicitar operaciones. No hay privilegio implícito por `is_staff` o por datos enviados por el navegador. La edición administrativa de inventario/roles queda por ORM/comandos, sin editor web en este incremento.

## Transacciones y reclamación

La solicitud bloquea router y servicio, comprueba membresía/revisión/IP/inventario, actualiza la intención y crea una tarea en la misma transacción. La revisión crece incluso al solicitar de nuevo el mismo estado. Un formulario viejo no duplica una intención; muestra error inline. Otro alta explícita con revisión vigente reconcilia la misma cola.

`claim()` usa `SELECT FOR UPDATE SKIP LOCKED` sobre routers en PostgreSQL. La concesión dura **30 segundos** y serializa servicios del mismo router. Las tareas tienen vencimiento de **15 minutos**, máximo **5 intentos** y espera creciente (2, 4, 8, 16 segundos; tope 60). El plazo de concesión es suficiente para el simulador; no existe renovación de concesiones para operaciones físicas prolongadas.

Una revisión posterior cancela pendientes anteriores. Una tarea reclamada anterior retiene el router hasta vencer; deja de ser ejecutable y su reporte ya no modifica el estado observado. Los intentos se guardan con UUID y fechas. Al reclamar de nuevo, se registra la concesión perdida, se revalida la revisión y se crea otro intento. Concesión vencida, revisión obsoleta, destino ajeno o reporte distinto no acreditan éxito.

No se promete ejecución exactamente una vez. Una única instancia del agente por inventario está protegida mediante bloqueo de archivo del estado local. La concesión central no es un bloqueo físico distribuido de RouterOS: no se debe arrancar un sustituto con otra copia de inventario/estado mientras la instancia anterior pueda seguir escribiendo. Las escrituras físicas están deshabilitadas.

## API del agente

Tres POST JSON: `/api/agent/claim/` con `{}`, `/api/agent/validate/` con `task`/`attempt`, `/api/agent/report/` con `task`/`attempt`/`report`. Identidad mediante `X-Agent-ID` y `Authorization: Bearer …`; el servidor almacena solo el digest del token, permite revocación mediante `Agent.active` y comprueba asignación al sitio/router. Ninguna credencial del agente se entrega al navegador.

El sobre de versión 1 contiene tarea, intento, sitio, router, acción, vencimientos y estado completo tipado: servicio, IP individual, revisión, habilitado y subida/bajada en kbps. Solo admite `provision`, `suspend`, `resume` y `plan`. El agente revalida con el servidor inmediatamente antes de aplicar y comprueba su propio inventario local de destinos; el servidor no puede ampliarlo mediante una tarea.

Un reporte tiene `ok`, `state`, `error`. Solo un éxito que coincida completamente con el snapshot de la tarea vigente actualiza el observado. Reportes idénticos se deduplican por intento; los cambiados se rechazan. Los errores tienen códigos cerrados; no se guardan excepciones arbitrarias que puedan revelar secretos. El panel registra actor, motivo, eventos, intentos, resultado y fecha de observación.

El cliente HTTP comprueba certificados mediante el almacén de confianza, exige HTTPS y no sigue redirecciones ni usa proxies implícitos. HTTP requiere bandera explícita y destino literal loopback. El servidor local se enlaza solo a 127.0.0.1. El login tiene límite de 12 intentos por IP cada cinco minutos y las solicitudes de operación un límite básico de 30 por usuario/minuto. No sustituye una política de autenticación/exposición de producción.

## Simulador y recuperación

SQLite mantiene el **router simulado** y una bandeja durable de reportes; PostgreSQL mantiene todas las intenciones, tareas y resultados centrales. Al aplicar, el simulador carga su configuración, comprueba identidad/unicidad y política Morosos-v1 y realiza una transacción local. El alta comienza restringida, coloca la cola tras Descanso_Madrugada y antes de Default Queue y verifica el estado final. Suspensión/reactivación solo cambia la restricción individual; el cambio de plan conserva posición, parent, burst, colas generales y schedulers.

No se adopta automáticamente una cola o restricción ajena. IP de infraestructura y subredes se rechazan tanto en servidor como en agente. No hay interpretación de comandos arbitrarios. FREE bloquea suspensión sin una decisión comercial posterior.

Después de escribir, el agente lee de nuevo el simulador y guarda el reporte antes de enviarlo. Si se pierde la conexión, la bandeja permanece. Tras reiniciar se hace una lectura nueva antes de reenviar; el diario solo no es evidencia del estado actual. Si el proceso muere entre la escritura y el diario, al vencer la concesión otra ejecución lee/reconcilia la misma revisión sin duplicar. Una discrepancia inesperada en la misma revisión queda visible y no se sobreescribe como si fuera éxito.

La observación se toma al procesar tareas; no hay sondeo continuo de divergencias cuando no hay trabajo. El panel muestra **última** observación con fecha, no disponibilidad ni acceso a internet en tiempo real. Los vencimientos y agotamiento de intentos se materializan cuando el agente consulta. Después de vencer/fallar, el operador puede enviar una intención nueva desde la ficha.

## Transporte físico preparado, sin ejecutar

`agent/routeros.py` contiene transporte API-SSL/8729 con CA, validación de host/IP, TLS mínimo 1.2 y lectura con lista cerrada de rutas, para familias 6/7. Incluye comprobaciones de objetos únicos etiquetados/adoptados y normalización de velocidad. No depende de REST.

`RouterOSAdapter.apply()` permanece bloqueado de forma explícita, y el ejecutable del agente solo admite `mode=simulator`. La lectura física tampoco se ejecuta en este encargo. No se presenta este esqueleto como un adaptador de escritura terminado: faltan adopción, manifiesto de política, escrituras estrechas con conservación de orden/burst, validación de restricciones superpuestas, reconciliación física y la matriz de pruebas por versión. Esto no impide el recorrido simulado solicitado.

No se accedió ni se modificó `config-mikro/` o `config-antenasyclientes/`. No se enviaron solicitudes a MikroTik, Raspberry o CPE. La prueba real de Lulu sigue cerrada, con cuenta en lectura según evidencia previa.

