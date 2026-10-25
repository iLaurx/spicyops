# SpicyOps para Windows

SpicyOps permite consultar y administrar los servicios de varias localidades con redes MikroTik desde una PC con Windows. Se conecta por SSH a la Raspberry de cada localidad y, desde ella, consulta el router mediante API-SSL.

Los clientes se detectan automáticamente a partir de las colas simples individuales del MikroTik. Las conexiones, lecturas y notas se guardan en el equipo para continuar trabajando al volver a abrir el programa.

**Versión 1.0.0 · Interfaz en español · Analytics, Clientes y Conexiones**

## Funciones principales

- Administrar varias localidades con accesos y datos independientes.
- Consultar clientes, direcciones IP, planes y contadores de consumo.
- Guardar nombre visible, contacto, ubicación y notas por cliente.
- Ver consumo observado entre lecturas y estimaciones a 24 horas y 30 días.
- Actualizar lecturas manualmente o de forma automática.
- Diagnosticar problemas de conexión por etapas.
- Suspender o reactivar una IPv4 individual mediante la lista `Morosos`, con confirmación.
- Crear respaldos cifrados, recuperar datos y trasladarlos a otra PC.

Cada instalación comienza sin localidades ni clientes precargados.

## Requisitos

### En la PC

- Windows 10 u 11 de 64 bits.
- Microsoft Edge o un navegador predeterminado actualizado.
- Acceso a las Raspberry por red local o Tailscale.
- Espacio para el programa, los datos y los respaldos.

El paquete incluye las dependencias de la aplicación. No necesitas instalar Python, PostgreSQL ni Docker, crear una base de datos o abrir el programa como administrador.

### En cada localidad

- Una Raspberry accesible mediante SSH con contraseña o clave.
- Python con `librouteros` ya disponible en la Raspberry.
- Acceso desde la Raspberry al MikroTik por API-SSL, en el puerto 8729.
- Un certificado CA en la Raspberry para validar el certificado y el nombre del router.
- Una cuenta API con lectura de identidad, recursos, colas simples y lista `Morosos`.

Para suspender o reactivar clientes también necesitas permisos de escritura y reglas de bloqueo de `Morosos` previamente configuradas por el administrador.

SpicyOps utiliza la configuración de red existente. La preparación de SSH, Tailscale, Python, certificados y permisos corresponde al administrador de la red.

## Abrir SpicyOps

1. Extrae el paquete completo en una carpeta de tu PC.
2. Conserva la carpeta `_internal` junto a `SpicyOps.exe`.
3. Abre `SpicyOps.exe`.

El programa abre una ventana de aplicación con Edge. Si Edge no está disponible, utiliza el navegador predeterminado. No lo ejecutes directamente desde el ZIP ni copies únicamente el archivo `.exe`.

Las distribuciones y compilaciones de prueba anteriores se retiraron durante la limpieza previa a producción. El siguiente paquete debe generarse desde las fuentes actuales; esta limpieza no genera ni publica un ejecutable nuevo.

La limpieza del código antiguo y de las distribuciones está realizada. Windows impidió retirar seis directorios temporales: `.local/ui-cleanup-build`, `.local/ui-cleanup-preview`, `.local/ui-cleanup-tests`, `build/audit-tests`, `build/release-review` y `build/release-tests`. Se requiere acceso del propietario de esas carpetas para completar su eliminación. No se incluyen en el empaquetado.

## Ejecutar y preparar el paquete desde las fuentes

Con Python y las dependencias de `requirements.txt` instalados, ejecuta `python run_panel.py` para abrir la aplicación. Para construir la distribución Windows, instala también `requirements-build.txt` y ejecuta, en este orden:

```powershell
python scripts/collect_notices.py
python scripts/build_windows.py
python scripts/package_windows.py
```

El ejecutable se genera en `dist/SpicyOps-1.0.0-Windows/SpicyOps/SpicyOps.exe` y el ZIP junto a esa carpeta. Se conservan las licencias y fuentes de terceros necesarias para distribuirlo. Las suites, simuladores, herramientas de pruebas, capturas y reportes históricos se eliminaron por solicitud del propietario; no hay un comando de tests incluido en este árbol.

## Conectar la primera localidad

Abre **Conexiones → Nueva localidad** y completa los accesos.

### 1. Acceso a la Raspberry

| Campo | Qué indicar |
| --- | --- |
| Nombre de la localidad | Un nombre que te permita reconocerla. |
| Dirección de la Raspberry | IP o nombre accesible por LAN o Tailscale, sin URL ni comandos. |
| Puerto SSH | El puerto configurado; normalmente, 22. |
| Usuario de Raspberry | La cuenta autorizada para SSH. |
| Autenticación SSH | Contraseña o clave SSH de Windows. |
| Contraseña o frase de clave | La contraseña de acceso o la frase de la clave, según el método elegido. |

Si utilizas clave SSH, puedes indicar su archivo privado en Windows dentro de la configuración adicional. Si dejas la ruta vacía, se utiliza el agente SSH o las claves habituales disponibles.

### 2. Acceso al MikroTik

| Campo | Qué indicar |
| --- | --- |
| IP del MikroTik | Su IPv4 accesible desde la Raspberry. Vacío: se utiliza la puerta de enlace de la Raspberry. |
| Usuario API del MikroTik | La cuenta autorizada para consultar el router. |
| Contraseña API del MikroTik | La contraseña de esa cuenta. |
| Python con librouteros en Raspberry | Ruta del intérprete que ya tiene esa dependencia. |
| Certificado CA en Raspberry | Ruta del certificado CA existente. Es obligatoria. |

Las rutas de Python y del certificado pertenecen a la Raspberry. La ruta de la clave SSH pertenece a Windows. `/usr/bin/python3` solo sirve si ese intérprete tiene `librouteros` disponible.

### 3. Confirmar y leer

1. Pulsa **Comprobar y conectar**.
2. Compara la huella SSH mostrada con la que te proporcione el administrador por un medio confiable.
3. Si coincide, pulsa **Confirmar huella y conectar**.
4. Espera la comprobación y la importación de las colas individuales.

Un cambio de huella previamente aceptada detiene el acceso. Verifica la identidad del equipo antes de continuar.

Conectar y sincronizar son operaciones de lectura. No instalan servicios en Raspberry ni cambian planes, reglas o permisos del router.

## Trabajar con varias localidades

Agrega cada localidad desde **Conexiones → Nueva localidad**. Sus accesos, lecturas y notas permanecen separados, incluso cuando distintas redes repiten direcciones privadas.

El selector superior permite cambiar de localidad. **Todos** abre Clientes con los servicios de las localidades conectadas, indicando localidad y fecha de lectura por fila. Las desconectadas siguen disponibles al seleccionarlas individualmente.

En Conexiones puedes abrir, configurar, diagnosticar o desconectar cada localidad. Desconectar retira las contraseñas guardadas y conserva la última lectura y los datos complementarios. Para reconectar, configura el mismo perfil e introduce los accesos que falten.

Los estados **Activa**, **Error de conexión** y **Desconectada** reflejan la última operación. Revisa también la fecha de lectura: un estado activo o una lectura guardada no garantizan disponibilidad actual.

## Clientes

La lista muestra el nombre del servicio, IP, plan de subida y bajada, consumo acumulado del contador y estado de la cola y de su suspensión. En **Todos** también muestra la localidad y la fecha de los datos.

Puedes buscar por nombre, IP o localidad y elegir velocidades en **Mbps** o **MB/s**. Pulsa **Sincronizar clientes** para obtener una nueva lectura de la localidad seleccionada.

### Editar datos complementarios

Pulsa la flecha **↗ — Ver datos** para guardar nombre visible, contacto, ubicación y notas.

Estos datos se conservan al sincronizar. La IP, las velocidades y los contadores proceden del MikroTik; editar un alias o una nota no cambia la configuración del router.

### Revisar colas excluidas

Si falta un servicio, abre **Revisar colas excluidas** para consultar su identificación, IP y motivo de exclusión.

**Incluir en Clientes** permite incorporar una cola IPv4 individual válida filtrada como infraestructura. La inclusión es local y queda vinculada a localidad, identidad de la cola e IP. **Revertir inclusión** restaura el filtro. Un cambio de identidad o IP no hereda esa excepción.

Las colas compartidas, ambiguas o con destinos inválidos requieren revisión en el router. Esta función no crea clientes manuales ni modifica MikroTik. Si la lectura guardada no tiene el detalle necesario, sincroniza primero.

## Analytics y consumo

Selecciona una localidad y pulsa **Actualizar lectura** para consultar los contadores actuales. **Actualizar y estimar** también obtiene una nueva lectura para las estimaciones por cliente.

| Dato | Cómo interpretarlo |
| --- | --- |
| Consumo del contador | Subida y bajada acumuladas en las colas. No representa por sí solo el consumo del mes. |
| Consumo observado | Diferencia válida entre contadores de dos lecturas consecutivas. Cada barra identifica su intervalo y fecha. |
| Estimado en 24 horas | Aproximación del contador dividida entre el tiempo encendido del router y proyectada a un día. |
| Estimado a 30 días | La misma aproximación, proyectada a 30 días a ritmo constante. |

El tiempo encendido del router no confirma la edad real de cada contador. Las estimaciones no equivalen a consumo mensual medido ni deben utilizarse como facturación.

La gráfica necesita al menos dos lecturas comparables y un intervalo suficiente. Tras la primera lectura, espera al menos un minuto antes de actualizar. Reinicios, resets, cambios de identidad y colas ambiguas pueden invalidar comparaciones o estimaciones. Cuando falta una base válida, el cálculo queda sin resultado.

Se conservan hasta **1,440 lecturas por localidad**. El tiempo cubierto depende de la frecuencia de actualización; los periodos sin lecturas no se reconstruyen.

Las unidades son decimales: **1 GB = 1,000,000,000 bytes** y **1 MB/s = 8 Mbps**. El plan muestra la velocidad configurada en la cola, no una prueba de velocidad de internet.

## Actualización automática

En la tarjeta de cada localidad, dentro de **Conexiones**:

1. Marca **Actualización automática**.
2. Elige **1, 5, 10, 15, 30 o 60 minutos**.
3. Pulsa **Guardar**.

Empieza desactivada, con 5 minutos seleccionados. Para pausarla, desmarca la opción y guarda. La preferencia se conserva al reiniciar. Desconectar la localidad detiene su programación efectiva; reconectarla permite retomarla.

Cada tarjeta muestra la última lectura, la próxima actualización y el estado de programación. Los fallos conservan los últimos datos válidos y espacian los reintentos. Una lectura manual también ajusta el siguiente ciclo.

Las actualizaciones continúan con SpicyOps abierto o en la bandeja. Se detienen al salir del programa, apagar o suspender la PC. Al reanudar no se recuperan todos los ciclos perdidos. SpicyOps no arranca automáticamente al encender Windows.

Las vistas incorporan lecturas nuevas sin recargar toda la página. Si tienes un formulario sin guardar o una confirmación abierta, la actualización visual espera para conservar lo que estás haciendo.

La actualización automática solo consulta datos; nunca suspende ni reactiva clientes.

## Suspender o reactivar clientes

El interruptor **Suspender** muestra **Sí** cuando la restricción está activa y **No** cuando está desactivada.

1. Pulsa el interruptor del servicio.
2. Revisa localidad, cliente e IP en la confirmación.
3. Confirma la suspensión o reactivación.
4. Espera la lectura que confirma el resultado.

Suspender agrega la IPv4 individual a la lista exacta `Morosos` o habilita su entrada existente. Reactivar deshabilita su entrada individual sin borrarla. Antes de escribir se comprueba de nuevo el inventario del router.

La operación requiere escritura y reglas de bloqueo previamente configuradas. Restricciones compartidas, dinámicas, duplicadas o ambiguas impiden el cambio individual. SpicyOps no modifica rangos, subredes, planes, reglas de firewall ni permisos.

El estado de `Morosos` no acredita por sí solo un corte de internet. El efecto depende de las reglas del router; IPv6, FastTrack o sesiones existentes pueden permitir tráfico. Ante un resultado incierto, sincroniza antes de reintentar. Las escrituras no se reintentan automáticamente.

## Diagnosticar una conexión

Abre **Conexiones → Diagnosticar** en la localidad correspondiente. Se comprueban por etapas el puerto SSH, identidad y autenticación, Python y `librouteros`, certificado, lecturas API-SSL e inventario.

Si falla una etapa, las dependientes aparecen como **No comprobada**. Sigue la orientación mostrada. En una localidad desconectada puede ser necesario introducir de nuevo los accesos desde **Configurar**.

El resultado conserva fecha y hora. Aparece como histórico al volver a la vista y como desactualizado si cambias la configuración. Diagnosticar no actualiza Analytics ni Clientes y no prueba escrituras o acceso a internet de los abonados.

## Guardado y privacidad

Localidades, accesos, lecturas, notas, diagnósticos y preferencias se guardan automáticamente en:

```text
%LOCALAPPDATA%\SpicyOps
```

El estado está cifrado y, en el ejecutable, su clave queda protegida mediante la cuenta Windows. No compartas esa carpeta, sus claves ni los enlaces temporales de apertura. Introduce las credenciales únicamente en el programa.

SpicyOps utiliza un servidor local accesible solo desde la propia PC. Cada instalación mantiene su información de manera independiente; no es un portal público ni un sistema de datos compartidos entre administradores.

## Respaldos y recuperación

Abre **Respaldos** en el pie de la aplicación.

### Crear un respaldo portable

1. Introduce una contraseña de **al menos 12 caracteres**.
2. Pulsa **Descargar respaldo portable**.
3. Guarda el archivo `.spicybackup` en un lugar seguro y la contraseña por separado.

Incluye accesos, localidades, notas e historial cifrados. Sin su contraseña no se puede recuperar. Exporta uno antes de actualizar, cambiar de PC o restaurar datos.

### Copias locales automáticas

Antes de guardar cambios se conserva una copia del estado anterior, como máximo una por hora, hasta cinco copias y 512 MiB en total.

Estas copias requieren la clave original de la cuenta Windows y pueden no incluir los cambios más recientes. Utiliza un respaldo portable para trasladar datos a otra cuenta o PC.

### Restaurar datos

Selecciona un respaldo local válido y pulsa **Restaurar respaldo seleccionado**, o utiliza **Importar respaldo portable** con su archivo y contraseña. Revisa y confirma el reemplazo de los datos actuales.

La restauración conserva los archivos originales en una subcarpeta `original-...` de los datos privados. Las localidades quedan desconectadas, conservando accesos, historial, notas y preferencias. Reconéctalas cuando estés listo.

Si el estado o la clave no se pueden abrir, se presenta la pantalla de recuperación sin sustituir el original por datos vacíos. No borres archivos para intentar resolverlo. Sin una clave válida o un respaldo portable con contraseña no es posible descifrar los datos.

Los originales conservados no se eliminan automáticamente. Retíralos únicamente después de comprobar la recuperación y disponer de un respaldo válido.

## Cambiar de PC o cuenta Windows

1. Exporta un respaldo portable desde la cuenta original.
2. Abre la misma versión de SpicyOps en el destino.
3. En **Respaldos → Importar respaldo portable**, selecciona el archivo e introduce la contraseña.
4. Confirma y comprueba localidades, notas e historial.
5. Ajusta las rutas de claves SSH y reconecta las localidades.

Las claves SSH de Windows y los certificados de Raspberry no se incluyen en el respaldo. Deben estar disponibles en sus equipos correspondientes. Copiar solamente la carpeta privada a otra cuenta Windows no sustituye este procedimiento.

## Actualizar SpicyOps

1. Exporta un respaldo portable y conserva la contraseña.
2. Selecciona **Salir de SpicyOps** y espera a que termine el proceso.
3. Extrae el paquete nuevo en otra carpeta y conserva la versión anterior.
4. Abre el nuevo ejecutable con la misma cuenta Windows.
5. Comprueba tus localidades y datos antes de continuar.

La nueva versión utiliza la misma carpeta de datos del usuario. Evita abrir versiones distintas simultáneamente sobre esos datos. Volver a una versión anterior requiere un respaldo de formato compatible; no hay conversión automática de formatos futuros.

## Cerrar el programa

Cerrar la ventana permite que SpicyOps continúe en la bandeja del sistema y mantenga las actualizaciones automáticas.

Para detenerlo por completo, utiliza **Salir de SpicyOps** desde la bandeja o desde **Respaldos → Cerrar SpicyOps**. Espera a que terminen las lecturas en curso y se guarden sus resultados.

## Solución de problemas

| Problema | Qué revisar |
| --- | --- |
| No abre el programa | Extrae el paquete completo y conserva `_internal` junto al ejecutable. |
| No conecta con Raspberry | Revisa dirección, puerto, acceso LAN/Tailscale y credenciales. Ejecuta Diagnosticar. |
| Cambió la huella SSH | Verifica con el administrador la identidad del equipo antes de aceptar otra huella. |
| Falla Python o librouteros | Confirma la ruta del intérprete de Raspberry que tiene la dependencia. |
| Falla el certificado | Revisa ruta de la CA, validez y coincidencia del certificado con el destino. |
| El botón de conexión parece no responder | Despliega la configuración adicional y completa Python y CA obligatoria. Revisa los errores del formulario. |
| No aparecen clientes | Revisa colas excluidas y confirma que existan colas simples individuales compatibles. Un inventario vacío puede ser válido. |
| No hay gráfica o estimaciones | Obtén lecturas comparables y revisa intervalos insuficientes, reinicios, resets o colas ambiguas. |
| Los datos parecen antiguos | Consulta su fecha, sincroniza y revisa la programación automática. |
| No permite suspender o reactivar | Revisa permisos de escritura y restricciones compartidas, dinámicas, duplicadas o ambiguas. |
| Una suspensión no queda confirmada | Sincroniza antes de reintentar y comprueba el estado de Morosos. |
| No se guarda un cambio | Revisa espacio libre y permisos de la carpeta de datos; después vuelve a intentarlo. |
| No abre los datos tras cambiar de cuenta | Importa un respaldo portable con su contraseña o utiliza la cuenta original. |

## Compatibilidad y disponibilidad

SpicyOps importa servicios de **colas simples de RouterOS 6 y 7**. PPPoE, RADIUS y otros modelos de inventario no están incluidos. Tampoco incorpora facturación, registro de pagos, cobros, suspensión automática por fecha ni portal cautivo.

La aplicación y el ejecutable se han comprobado localmente con datos de prueba y conexiones SSH controladas. La validación física completa con Raspberry, MikroTik y reglas de bloqueo sigue pendiente, al igual que la comprobación en un Windows limpio. La compatibilidad física con RouterOS 7 aún no está acreditada.

La licencia de uso propia y el canal de soporte están pendientes de definición. Consulta los [avisos y licencias de componentes de terceros](docs/THIRD-PARTY-NOTICES.txt) incluidos con el proyecto.
