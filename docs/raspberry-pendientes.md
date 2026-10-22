> ARCHIVO HISTÓRICO DEL PRIMER ENCARGO. El usuario sustituyó el producto manual/simulado por SpicyOps para Windows. Ver [encargo vigente](encargo-panel-conectado.md) y [README](../README.md). Las pruebas anteriores no acreditan la conexión física ni describen la interfaz actual.

# Instalación posterior en Raspberry: pendientes

El agente permanente **no está instalado**. Este documento registra preparación y límites, no una secuencia de cambios autorizados en la red.

El diseño mantiene Django y PostgreSQL en el servidor central; la Raspberry solo ejecutaría el agente Python. El simulador usa biblioteca estándar de Python 3.11+, sin wheels de PostgreSQL/Django ni Docker. `librouteros==4.2.2` es una dependencia separada para el transporte futuro; no se incorpora al modo simulado. Se comprobó sintaxis Python 3.11, pero el runtime disponible para los tests fue Python 3.12.14 en Windows.

Antes de instalar, falta:

1. Ejecutar tests del agente con **Python 3.11 en ARMv6 real**, medir RAM/CPU y escrituras en microSD en el equipo de 512 MB con sus servicios actuales. No asumir que un binario ARMv7/ARM64 es válido.
2. Definir la ubicación del panel central, HTTPS con certificados confiables, cuenta PostgreSQL de mínimos privilegios, backups y una restauración ensayada. El usuario local con CREATEDB está limitado al laboratorio; el servidor de desarrollo Django no es un despliegue público.
3. Crear usuario del sistema y directorio privado del agente, asignar inventario revisado y token revocable fuera de Git; conservar la bandeja y estado al actualizar. El token y el inventario no se envían al navegador.
4. Revisar/adaptar `deploy/spicyops-agent.service` y `deploy/agent.example.json`. Son ejemplos sin secretos, no unidades instaladas. El proceso no sirve HTTP ni ocupa puerto 80. `MemoryMax=96M` es un límite propuesto, no una medición en Raspberry. Configurar retención de journal antes de operar en microSD.
5. Verificar funcionamiento del agente primero contra **simulador** por HTTPS desde la Raspberry y recuperación tras reinicio, sin modificar Tailscale, lighttpd, firewall o configuración de los clientes.
6. Completar por separado el adaptador de escritura física. Requiere autorización nueva y específica, adopción de objetos, referencia estable, protección de infraestructura, política Morosos/IPv6, conservación de orden y burst, tiempos de operación/concesiones y recuperación. El actual ejecutable rechaza modo real y el adaptador bloquea escrituras.
7. Validar en laboratorio autorizado RouterOS **6.49.23** y una versión **7** elegida; solo después medir acceso/suspensión y velocidad desde un abonado de prueba. La compatibilidad física con v7 todavía no está acreditada.

La cuenta real sigue en `read,api,!write` de acuerdo con el cierre documental previo. La prueba de Lulu conserva 2M/4M; este desarrollo no la reabrió ni comprobó de nuevo físicamente. No hay que elevar permisos para usar el MVP local. El portal cautivo continúa secundario.

