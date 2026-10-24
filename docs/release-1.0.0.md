# Notas de versión — SpicyOps 1.0.0

Primera distribución local preparada para revisión pública. Conserva Analytics, Clientes y Conexiones y el diseño oscuro existente. Versión única en `portal/version.py`, visible en el pie y en FileVersion/ProductVersion del EXE.

- Recuperación al fallar el archivo cifrado o su clave, conservando originales.
- Respaldos automáticos rotativos, validación y restauración explícita.
- Traslado cifrado con contraseña, independiente de DPAPI de origen.
- Estado de formato 1, migración desde formato anterior sin versión y rechazo de formatos futuros.
- Restaurar desconecta localidades sin retirar accesos; mantiene historial, notas y preferencias.
- Salida ordenada desde Respaldos y bandeja; se puede iniciar bandeja sin ventana con `--no-open --tray`.
- Formularios sin referencias al ensayo cerrado; guías y avisos de terceros incluidos.

Paquete oficial: `dist/SpicyOps-1.0.0-Windows/`. Versiones anteriores conservadas. No firmado y sin publicación remota. La prueba física y las decisiones del propietario sobre licencia, titular y soporte siguen pendientes. Instalación y actualización en Windows limpio: excluidas por indicación expresa del usuario.

Ver `verificacion-release-1.0.0.md` para pruebas ejecutadas y límites. El archivo `integridad.json` junto al ZIP contiene hashes y manifiesto completo. La firma futura cambia el hash del EXE y exige regenerar ZIP y manifiesto.
