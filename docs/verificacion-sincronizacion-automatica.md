# Sincronización automática por localidad

Verificación local del 22 de octubre de 2026. Producto: `portal/`; no se utilizaron equipos reales ni carpetas sensibles.

## Implementación

- Preferencias cifradas por localidad: desactivada inicialmente; intervalo inicial de 5 minutos y opciones 1, 5, 10, 15, 30 y 60. Pausar no elimina información.
- Un coordinador se inicia después del bloqueo de instancia de Windows. No depende de pestañas ni ventanas. Hasta dos lecturas automáticas simultáneas, sin cola de ciclos vencidos.
- Bloqueo por localidad durante toda la operación: lectura automática/manual, configuración, desconexión y Morosos. Integrado también con el diagnóstico concurrente presente en el checkout. Las localidades ocupadas se omiten para no bloquear a las demás.
- Se reutiliza la lectura manual, normalización y persistencia. La programación nunca pasa una acción Morosos al conector. Las preferencias sobreviven a la reconfiguración y al reinicio.
- Errores con fecha, última lectura válida preservada y espera progresiva de 1/2/4 minutos; después, al menos 15 minutos o el intervalo configurado. Una lectura manual también actualiza el siguiente vencimiento.
- La vista consulta cambios locales cada 5 segundos. Conserva consulta, unidades y desplazamiento; difiere reemplazos mientras hay edición, búsqueda pendiente o confirmaciones abiertas. Las consultas de fondo no modifican la sesión ni consumen avisos del operador.
- Reinicio sin recuperar ejecuciones perdidas, arranque espaciado y cierre del coordinador esperando persistencia de las lecturas en curso.

## Pruebas ejecutadas

`python manage.py test portal.tests --noinput`: 74 pruebas correctas en la comprobación completa previa al empaquetado. Incluyen pruebas con reloj y conector controlados, y SSH real efímero exclusivamente en loopback. Las advertencias de cierre de sockets de esas pruebas no corresponden a equipos externos.

La suite `portal.tests.test_scheduling` cubre intervalos, pausa, cifrado/persistencia y reinicio; inicio idempotente del coordinador; ciclos vencidos sin acumulación; coordinación con lectura manual, configuración, desconexión y Morosos; independencia entre localidades; errores con límite de espera y recuperación; persistencia al cerrar, ejecución sin ventanas y notas guardadas durante una reconfiguración.

Interfaz comprobada en navegador local: activación y guardado, lectura que aparece sin recarga completa, borrador conservado mientras llega otra lectura y controles en anchos de 390 y 320 píxeles. Se mantuvieron Analytics, Clientes, Conexiones y el tema oscuro. También se comprobó sintaxis JavaScript y `pip check`.

El smoke del ejecutable usa estado temporal/DPAPI y un servidor SSH de prueba en loopback. Comprueba apertura protegida, ausencia de datos iniciales, recursos y vistas, reapertura sin segunda instancia, autolectura sin ventanas, ausencia de acción Morosos en el payload y preferencias/lecturas/notas conservadas tras reiniciar. El reinicio del smoke incluye terminación abrupta; el cierre ordenado se verifica por separado con un conector controlado en la suite.

Salida aislada: `dist/auto-sync/SpicyOps/SpicyOps.exe` y `dist/auto-sync/SpicyOps-Windows.zip`. Se cotejaron recursos y código compilado (coordinador, vistas, conector, diagnóstico y arranque/cierre) con las fuentes y se excluyen estado privado, credenciales, configuraciones sensibles y fixtures de pruebas.

## Límites

No hay lecturas con Windows apagado o suspendido ni después de salir de SpicyOps. Cerrar solo la ventana conserva la programación mientras el proceso siga en la bandeja. Volver de suspensión omite ciclos perdidos; reiniciar agenda desde el intervalo elegido. No se instala un servicio ni se configura arranque con Windows.

Pendiente: validación física Raspberry/MikroTik y prueba prolongada en las redes del operador. Las pruebas locales no acreditan disponibilidad real, compatibilidad física RouterOS v7 ni un cambio de acceso a internet.
