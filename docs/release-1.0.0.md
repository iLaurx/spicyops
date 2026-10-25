# Notas de versión — SpicyOps 1.0.0

Primera distribución local preparada para revisión pública. Conserva Analytics, Clientes y Conexiones y el diseño oscuro existente. Versión única en `portal/version.py`, visible en el pie y en FileVersion/ProductVersion del EXE.

- Recuperación al fallar el archivo cifrado o su clave, conservando originales.
- Respaldos automáticos rotativos, validación y restauración explícita.
- Traslado cifrado con contraseña, independiente de DPAPI de origen.
- Estado de formato 1, migración desde formato anterior sin versión y rechazo de formatos futuros.
- Restaurar desconecta localidades sin retirar accesos; mantiene historial, notas y preferencias.
- Salida ordenada desde Respaldos y bandeja; se puede iniciar bandeja sin ventana con `--no-open --tray`.
- Formularios sin referencias al ensayo cerrado; guías y avisos de terceros incluidos.

Destino del próximo paquete: `dist/SpicyOps-1.0.0-Windows/`. Las distribuciones históricas se retiraron durante la limpieza previa a producción. No se ha generado, firmado ni publicado un paquete nuevo con esta limpieza. SpicyOps se distribuye bajo la licencia MIT incluida en `LICENSE`; los componentes de terceros conservan sus propias licencias. La prueba física y la definición del canal de soporte siguen pendientes. Instalación y actualización en Windows limpio: excluidas por indicación expresa del usuario.

Las suites y los reportes históricos de pruebas se retiraron por solicitud del propietario. Al generar un paquete, `integridad.json` junto al ZIP contiene sus hashes y manifiesto completo. La firma futura cambia el hash del EXE y exige regenerar ZIP y manifiesto.
