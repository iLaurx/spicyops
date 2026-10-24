# Verificación local — SpicyOps 1.0.0

Realizada el 22 de octubre de 2026 en Windows 11 x64 (10.0.26300), Python 3.12.14, sin equipos de red reales. El trabajo partió con cambios previos en README, interfaz y smoke: se conservaron. Las carpetas sensibles no se leyeron ni modificaron. No se usó el estado de la instalación del usuario, no se cerraron instancias ajenas ni se sustituyeron distribuciones históricas.

## Implementación

Estado formato 1: valida estructura, tipos, límites, números finitos e integridad autenticada antes de aceptar datos. Migra el formato anterior sin versión al guardar. Rechaza formatos futuros sin sobrescribir. Cifrado Fernet y sustituciones atómicas con fsync; DPAPI para clave empaquetada. El arranque mantiene el servidor y la recuperación aunque el estado o la clave fallen; una clave temporal solo permite presentar esa interfaz y se persiste protegida únicamente tras importación explícita.

Antes de guardar, respaldo del estado anterior, máximo uno por hora, cinco copias y 512 MiB. Estado activo limitado a 256 MiB. Recuperación lista solo copias válidas para la clave actual. Restaurar conserva originales en carpeta separada sin rotación automática, requiere confirmación y excluye operaciones activas. Las localidades quedan desconectadas, manteniendo accesos, preferencias y datos. Traslado portable con contraseña: scrypt N=32768/r=8/p=1, sal aleatoria de 16 bytes y Fernet autenticado; no depende de DPAPI del origen. Contraseña errónea o archivo inválido no modifica el estado. Los fallos de guardado, incluso en segundo plano, muestran un aviso persistente hasta un guardado exitoso.

La restauración protege contra concurrencia con solicitudes y trabajos automáticos del proceso, además del bloqueo del archivo y de las reclamaciones persistidas. Las operaciones SSH/TLS y el contrato de Morosos mantienen sus restricciones. Conectar/sincronizar no escriben en routers.

## Resultados ejecutados

- **113 pruebas correctas** en `portal.tests` (98 vigentes + 15 de recuperación). Cubren corrupción/truncamiento, contraseña incorrecta, formato portable futuro, estructura semántica inválida, restauración correcta, traslado entre claves, migración, notas/preferencias/historial, rotación y cuota, frecuencia horaria, concurrencia, disco lleno simulado, rollback de clave ante fallo de guardado y autenticación/CSRF. La suite vigente conserva pruebas de aislamiento, cálculos, resets, DNS/SSH acotados, autolectura y errores de conexión/Morosos simulados.
- `pip check`: sin dependencias rotas. Lector/contrato analizados con sintaxis Python 3.11. `git diff --check` correcto. PyInstaller concluyó la construcción; se comprobaron las advertencias no bloqueantes mediante el smoke del EXE.
- **Correspondencia final:** `check_windows_sources.py` compara el código compilado del EXE/PYZ con las fuentes, entrada, plantillas, CSS/JS y lector/contrato. Excluye `portal.tests`, librouteros local, psycopg y nombres de estado privado. [Manifiesto de fuentes](release-sources.json).
- **EXE final, smoke vigente:** producto vacío (en el Windows actual), recursos, sesión/CSRF, instancia única, DPAPI, persistencia, colas excluidas, diagnóstico de puerto rechazado, lectura automática SSH exclusivamente en loopback sin ventanas y preferencias tras reiniciar. Todo con carpetas sintéticas temporales.
- **EXE final, aceptación nueva:** versión histórica `dist/auditoria-20261022/SpicyOps/SpicyOps.exe` y versión 1.0.0 sobre la misma carpeta temporal. La versión histórica abre el formato anterior, la nueva migra y conserva historial/notas/intervalo. Se inicializó una bandeja nativa real (`tray_ready` tras `icon.visible`), se cerró ordenadamente por la ruta local autenticada y se volvió a abrir. No se hizo clic manual en el menú de bandeja: la aceptación visual/manual del menú y el efecto real de suspensión del SO siguen pendientes.
- **Recuperación en EXE:** se corrompió el estado, se comprobó que arrancaba en Recuperación y que una contraseña incorrecta dejaba intactos los bytes. Se importó el portable correcto, se verificaron originales conservados y salida ordenada. Después se dañó la clave DPAPI; se comprobó que no se sustituía al abrir, se importó y se reinició con la clave recuperada y los datos iguales. No se enviaron comandos a routers.
- **Interfaz final:** Edge/Playwright, cinco vistas (Analytics, Clientes, Conexiones, Nueva localidad y Respaldos) a 1280 y 390 px, tanto con estado sano como corrupto, sin desbordamiento horizontal ni errores JavaScript. Se inspeccionaron visualmente capturas finales de recuperación móvil y escritorio.
- **Carga acotada:** `soak_release.py --seconds 300` mantiene tres localidades sintéticas, diez clientes por localidad y 1440 muestras por localidad. Intercala ticks y escrituras simultáneas de notas, compara cálculos e historial exactos y no conecta red. [Mediciones y resultado de la ejecución](release-soak.json). Ejecución final: 300,72 segundos, 57 rondas de comprobación, 5700 ticks, 171 guardados de notas y archivo cifrado de 20 170 276 bytes. Mediana de tres guardados y una lectura: 4,485 s. La operación conjunta de tres guardados y una lectura tarda varios segundos: el archivo único sigue siendo un límite material, no se promete respuesta instantánea con cargas grandes.
- **Metadatos:** FileVersion/ProductVersion 1.0.0; EXE x64 y firma `NotSigned`. [Registro](release-exe.json). Versión única en `portal/version.py`.
- **Distribución:** ZIP verificado mediante CRC de todos los miembros y SHA-256 individual contra la carpeta final; nombres idénticos. EXE/ZIP y manifiesto en la carpeta oficial. Se incluyen guía, notas, checklist, piloto, avisos, licencias originales y fuentes instaladas de Paramiko/pystray. No se incluyen accesos, claves, estado de usuario, fixtures ni carpetas sensibles.

Las primeras ejecuciones restringidas no pudieron usar DPAPI y abrieron correctamente recuperación en lugar de la vista vacía esperada por el smoke antiguo. Se repitió el smoke con ejecución local autorizada; los resultados correctos corresponden a esa ejecución del paquete final. Los avisos de desconexión SSH en la suite pertenecen al servidor efímero de loopback y a pruebas deliberadas de error.

## Reproducir

Usar `.venv` con `requirements-build.txt` instalado. Para las fuentes de prueba, establecer `SPICYOPS_STATE_DIR` en una carpeta temporal propia y `DJANGO_SECRET_KEY` sintética; nunca usar las credenciales de una instalación real.

```powershell
.\.venv\Scripts\python.exe manage.py test portal.tests --noinput
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/collect_notices.py
.\.venv\Scripts\python.exe scripts/build_windows.py
.\.venv\Scripts\python.exe scripts/check_windows_sources.py --report docs/release-sources.json
# Retirar DJANGO_SECRET_KEY del entorno antes del smoke para comprobar DPAPI:
Remove-Item Env:DJANGO_SECRET_KEY -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe scripts/smoke_windows.py
.\.venv\Scripts\python.exe scripts/smoke_release.py
.\.venv\Scripts\python.exe scripts/soak_release.py --seconds 300
.\.venv\Scripts\python.exe scripts/package_windows.py
```

El smoke nuevo requiere la distribución histórica indicada, Edge y Playwright disponibles localmente; el script configura la ruta de los paquetes del runtime de Codex. Solo son dependencias de verificación, no de la aplicación. Las salidas auxiliares están en `build/release-1.0.0/` (logs y capturas). Los hashes y el manifiesto final se entregan junto al ZIP; no se reutilizan hashes de distribuciones anteriores.

## Exclusiones y pendientes

**Instalación en Windows limpio: excluida expresamente por el usuario. Actualización en Windows limpio: excluida expresamente por el usuario.** No se sustituyen esas exclusiones por la prueba local con carpetas temporales.

Pendientes externos: piloto físico con autorización nueva, certificado de firma y decisiones del propietario sobre titular/licencia propia/canal de soporte. Se recopilaron avisos y textos de terceros desde dependencias instaladas; esto no asigna licencia al proyecto ni sustituye la decisión/revisión de redistribución del propietario. Referencias: [licencia de PyInstaller](https://pyinstaller.org/en/stable/license.html), [pystray](https://pypi.org/project/pystray/), [Python para Windows](https://docs.python.org/3.12/using/windows.html). No se publicaron ni subieron archivos ni se creó una release remota. No se declara probado un corte físico ni compatibilidad física de Raspberry/RouterOS 7.
