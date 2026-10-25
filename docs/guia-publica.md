# SpicyOps 1.0.0 para Windows

Distribución oficial local: `dist/SpicyOps-1.0.0-Windows/SpicyOps/SpicyOps.exe`.
ZIP: `dist/SpicyOps-1.0.0-Windows/SpicyOps-1.0.0-Windows.zip`.
Extrae el ZIP completo y conserva `_internal` junto al EXE. No requiere instalar Python, PostgreSQL ni un servicio en Windows. Paquete sin firma digital; no publicado remotamente.

## Requisitos y primer uso

Objetivo: Windows 10/11 x64 con navegador actualizado. Construido con Python 3.12.14 x64; solo se ha comprobado en el Windows local de desarrollo. No se acredita Windows ARM nativo, versiones anteriores ni un Windows limpio. Edge abre una ventana de aplicación; sin Edge se usa el navegador predeterminado. No requiere privilegios de administrador. Reserva espacio para el programa, el estado cifrado, respaldos y originales de restauraciones. El estado admite hasta 256 MiB; los recursos necesarios crecen con localidades y clientes.

1. Abre SpicyOps.exe. Empieza sin localidades ni clientes.
2. Conexiones → Nueva localidad: introduce el acceso SSH de tu Raspberry por LAN o Tailscale. Para usar Tailscale, ambos extremos ya deben tener acceso autorizado; SpicyOps no instala ni configura VPN, rutas o firewall. Cada Raspberry consulta su propio MikroTik, incluso si las localidades repiten direcciones privadas.
3. Indica el ejecutable de Python **ya disponible en Raspberry** con librouteros (por ejemplo `/ruta/a/tu/entorno/bin/python`); `/usr/bin/python3` solo sirve si ese intérprete tiene la dependencia. El lector contempla Python 3.11/ARMv6; no se han comprobado esos equipos físicamente. El cliente SSH incluido en Windows no requiere librouteros local.
4. Indica usuario y contraseña API, dirección del MikroTik o puerta de enlace, y ruta de su CA existente en Raspberry. API-SSL usa el puerto 8729 y valida certificado/nombre. Se necesitan SSH, API-SSL y permiso de lectura de identidad, recursos, colas simples y Morosos. No se instala nada ni se cambian permisos.
5. Confirma la huella SSH comparándola con una fuente confiable del administrador. Un cambio de huella detiene la conexión. Diagnosticar identifica la etapa fallida; no modifica Clientes ni Analytics.
6. Clientes se genera desde colas individuales. Puedes editar alias, contacto, ubicación y notas. IP, velocidades y contadores pertenecen al router. Analytics muestra GB decimales y Mbps (o MB/s); estimados de 24 h/30 días son aproximaciones por uptime, no consumo mensual medido ni facturación. Resets y ambigüedades invalidan estimados.

## Respaldar y recuperar

Abre **Respaldos** en el pie de la aplicación. Guarda un respaldo portable con contraseña de al menos 12 caracteres; consérvala por separado. Incluye accesos y datos privados cifrados con scrypt (N=32768, r=8, p=1, sal aleatoria de 16 bytes) y Fernet autenticado. No compartas el respaldo ni su contraseña públicamente. La contraseña perdida no se recupera.

Antes de guardar cambios se conserva una copia local del estado anterior, como máximo una por hora, hasta cinco archivos y 512 MiB en total. Una modificación reciente puede no estar aún en un respaldo automático: exporta antes de actualizar o de trasladarte. Las copias locales requieren la clave de la cuenta Windows original. El estado activo usa Fernet y su clave se protege con DPAPI en el ejecutable.

Si el estado se daña o su clave no se abre, el programa presenta Recuperación en español y no crea un estado vacío sobre el original. Solo ofrece respaldos locales descifrables y válidos. Selecciona uno y confirma, o importa un portable con su contraseña. Una contraseña incorrecta, estructura inválida o formato futuro se rechaza antes de modificar el estado vigente. No borres archivos para resolver un error.

Cada restauración conserva `connections.enc` y los archivos de clave originales en una subcarpeta `original-...` de los datos privados. Estos originales no rotan automáticamente; revísalos y elimina únicamente los que ya no necesites, después de comprobar la recuperación. Las localidades restauradas quedan desconectadas: se conservan accesos, notas, historial y preferencias de actualización; reconecta explícitamente cuando estés listo. No se envían comandos al importar.

Sin clave válida ni respaldo portable con contraseña no se pueden descifrar los datos. Recupera la cuenta original o conserva los archivos para diagnóstico. Un error de espacio/permisos impide guardar: resuelve la causa y repite; no se declara un guardado exitoso.

## Traslado a otra cuenta o PC

En la cuenta original exporta un portable. En el destino abre la misma versión y **Respaldos → Importar respaldo portable**, selecciona el archivo, introduce la contraseña y confirma. Comprueba todas las localidades, notas e historial antes de retirar el origen. Las claves SSH de Windows y los certificados de Raspberry no se copian: ajusta sus rutas y asegúrate de que existan en sus equipos. No basta copiar `connections.enc` con `secret.dpapi` a otra cuenta.

## Actualización y operación

Exporta un portable, sal desde la bandeja o desde Respaldos → Salir de SpicyOps, y espera la salida del proceso. Extrae la versión nueva en otra carpeta; conserva la anterior. Abre el nuevo EXE con la misma cuenta Windows: reutiliza `%LOCALAPPDATA%/SpicyOps`. El formato anterior sin versión se valida y migra a formato 1 al guardar, conservando el contenido y un respaldo del formato anterior. No abras simultáneamente versiones distintas con la misma carpeta de datos. Para volver a una versión anterior conserva/exporta antes los datos y usa un estado separado compatible; no hay downgrade automático de formatos futuros.

Actualización automática se configura por localidad y empieza desactivada. Sigue funcionando con las ventanas cerradas mientras permanezca el icono de bandeja. Al salir espera las lecturas en curso. No ejecuta ciclos con el programa cerrado o la PC apagada/suspendida ni reconstruye intervalos perdidos. Hay hasta dos lecturas paralelas y una operación por localidad. Los errores conservan el último dato válido y no acreditan disponibilidad actual.

Suspender/reactivar exige confirmación individual y acceso API con escritura previamente autorizado por el administrador. Solo agrega/habilita/deshabilita una IPv4 individual en la lista fija Morosos. No modifica firewall, planes o permisos. Rangos, subredes, entradas dinámicas, duplicados y restricciones ambiguas bloquean la escritura. Un resultado incierto exige sincronizar antes de reintentar. La lista no demuestra corte físico, especialmente con IPv6, FastTrack o sesiones existentes.

## Datos y límites conocidos

Datos privados en `%LOCALAPPDATA%/SpicyOps`: conexiones cifradas, hasta 1440 muestras por localidad, notas, excepciones de inventario, diagnósticos y preferencias. `secret.dpapi` protege la clave; `runtime.json` contiene un enlace local de apertura temporal y es privado. Locks coordinan la instancia y las escrituras. No subas ni distribuyas esa carpeta. La aplicación escucha solo en loopback y protege sesión y CSRF; no es un portal multiusuario público.

Un solo archivo cifrado se lee/cifra bajo bloqueo. Historias grandes aumentan latencia, memoria y espacio. Un respaldo conserva el estado anterior y no garantiza recuperar el último cambio ni detectar una corrupción ocurrida antes de la primera copia. Se necesita espacio adicional para originales durante restauraciones. Una pérdida de alimentación durante una sustitución de clave en recuperación puede requerir recuperar los originales; ningún formato cifra de forma recuperable sin clave.

SpicyOps se distribuye bajo la licencia MIT incluida en LICENSE. Los componentes de terceros conservan sus propias licencias.

Pendientes: piloto real Raspberry/MikroTik y firewall, certificado de firma y canal de soporte. Instalación y actualización en Windows limpio están excluidas expresamente por el usuario. Revisión visual del menú nativo y comportamiento tras suspensión real requieren aceptación manual. No hay telemetría de soporte, cobros ni suspensión automática.
