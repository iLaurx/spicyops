# Checklist de release 1.0.0

## Preparación local

- [x] Leer encargo vigente y auditoría; preservar modificaciones previas y distribuciones anteriores.
- [x] Implementar recuperación, respaldos, traslado cifrado y formato versionado.
- [x] Mantener lectura SSH/TLS acotada y restricciones de Morosos.
- [x] Versión única en aplicación y EXE; carpeta y ZIP versionados.
- [x] Guía de primer uso, actualización, datos, recuperación y problemas conocidos.
- [x] Recopilar licencias/avisos y fuentes de dependencias LGPL incluidas; no asignar licencia propia.

## Verificación de entrega

Los resultados finales y comandos reproducibles se registran en `verificacion-release-1.0.0.md`. Consultar ese documento antes de distribuir; este checklist no reemplaza evidencia.

- [x] Suite completa: 113 pruebas correctas y regresiones de recuperación.
- [x] Dependencias, sintaxis, diferencias y correspondencia de fuentes contra EXE final.
- [x] Smoke final: DPAPI, navegación, persistencia, SSH loopback, autolectura, instancia única, cierre/reapertura.
- [x] Recuperación y traslado mediante EXE, clave dañada y migración entre dos versiones locales.
- [x] Carga sintética acotada con tres localidades e historial completo; ver release-soak.json.
- [x] ZIP íntegro, archivos idénticos y hashes SHA-256 en integridad.json; sin datos privados, fixtures ni carpetas sensibles.

## Exclusiones y pendientes externos

- **Excluido por el usuario:** instalar en Windows limpio.
- **Excluido por el usuario:** actualizar en Windows limpio.
- Pendiente de autorización: piloto físico descrito en `aceptacion-piloto.md`.
- Pendiente del propietario: titular, licencia del proyecto y canal de soporte; no se inventaron.
- Pendiente de certificado autorizado: firma Authenticode; paquete local sin firmar.
- Publicación/subida/release remota no autorizadas y no realizadas.

## Firma futura (solo con certificado autorizado)

Usar SignTool del Windows SDK, certificado de firma de código válido del propietario y servidor de sellado de tiempo de su proveedor. Ejemplo orientativo: `signtool sign /sha1 HUELLA_AUTORIZADA /fd SHA256 /tr URL_TIMESTAMP_DEL_PROVEEDOR /td SHA256 RUTA_EXE`. Verificar con `signtool verify /pa /v RUTA_EXE` y con Get-AuthenticodeSignature. No usar certificados inventados ni presentar autofirma como confianza pública. Después de firmar: repetir smoke, empaquetar de nuevo y regenerar hashes/manifiesto. No se ha ejecutado este procedimiento.
