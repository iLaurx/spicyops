# Prueba temporal: cliente 011

## Alcance autorizado

El 16/10/2026 el usuario seleccionó expresamente `011_Lulu Mendoza`, objetivo `192.168.8.62`, para realizar pruebas durante un rato, con cambios mínimos y reversibles. Esa autorización se refiere solo a este servicio; no habilita cambios en otros abonados, reglas generales, antenas o infraestructura.

La captura compartida muestra cola habilitada, nombre `011_Lulu Mendoza`, target .62 y max-limit 2M/4M (subida/bajada). No muestra burst configurado. Estos datos son referencia visual: antes de escribir se debe consultar la configuración actual completa y comprobar que haya exactamente una cola y una entrada Morosos correspondientes.

Estado actual de la preparación: cuenta API con solo read,api; se entregó después una escritura del mismo límite existente, aún sin confirmar ejecución. No se aplicó una reducción ni suspensión en el último estado conocido. El portal es secundario y no se modificará para esta prueba.

## Primera etapa: lectura de estado

Ejecutar en MikroTik:

```routeros
/queue simple print detail without-paging where name="011_Lulu Mendoza"
/ip firewall address-list print detail without-paging where address=192.168.8.62
```

Registrar nombre, target completo, estado habilitado/deshabilitado, max-limit, burst, parent, horario y cualquier coincidencia adicional de listas. Si el target no es exclusivamente .62, existen duplicados o el estado difiere de la captura, detener las modificaciones y resolver la discrepancia. No usar índices numéricos de WinBox para escribir.

La salida del usuario confirmó la cola e IP esperadas y una entrada Morosos deshabilitada. El usuario está en Guadalajara y no tiene acceso a un dispositivo bajo ese CPE para comprobar acceso y velocidad. Un ping al CPE o una lectura correcta de la cola no demuestra internet desde el abonado.

## Secuencia prevista

1. Confirmar estado inicial y preparar reversión exacta antes de la primera escritura, con un límite temporal definido y mecanismo de recuperación elegido para este piloto.
2. Primero comprobar una escritura del mismo límite, conservando el plan. La reducción temporal real queda pendiente de una ventana y recuperación concretas; no se envía en este primer ensayo.
3. En una etapa posterior, probar suspensión/reactivación solo para .62, con recuperación preparada y restauración del estado previo de su entrada Morosos. No tocar las reglas generales ni limpiar globalmente conexiones.
4. Confirmar al finalizar que cola y restricción coinciden con el estado inicial y que el cliente recuperó su servicio; registrar evidencia y límites de la prueba.

No se ejecutará un alta creando una segunda cola para este cliente existente ni se borrará su configuración para simular un alta. El alta nueva necesita un destino de laboratorio separado o una validación aislada; no está incluida como operación destructiva sobre este abonado.

Antes de elevar permisos API, documentar que write amplía el alcance de la cuenta en el router y restringir el diagnóstico al destino validado. Después del ensayo, devolver el grupo a lectura. Se entregaron comandos de elevación temporal, diagnóstico de escritura del mismo límite y retorno a lectura; sus resultados siguen pendientes.

## Primera escritura: conservar el mismo límite

La lectura compartida confirmó una cola habilitada, target 192.168.8.62/32, parent=none, max-limit=2M/4M, limit-at=0/0, priority=8/8, queue=default-small/default-small, burst-limit=0/0, burst-threshold=0/0, burst-time=0s/0s y bucket-size=0.1/0.1. Hay una entrada Morosos .62 deshabilitada. El usuario confirmó que está en Guadalajara y no tiene acceso a un dispositivo bajo ese cliente.

Por tanto, la primera escritura enviará el mismo max-limit existente. No se aplica todavía reducción de plan ni suspensión. Esto comprueba permisos de escritura y operación API sobre el destino validado; no demuestra velocidad o acceso efectivos desde la vivienda. El servicio puede experimentar efectos internos de reconfiguración del router aunque el valor enviado sea idéntico; no se garantiza impacto cero a partir de una lectura de configuración.

Estado: diagnóstico ejecutado y confirmado por salida del usuario: Escritura API del mismo limite: OK, destino .62, plan conservado 2M/4M y sin modificación de Morosos. El primer intento de devolución a lectura aún mostraba write positivo. La corrección posterior policy=read,api,!write quedó confirmada por salida del usuario: read,api positivos y !write. Ensayo cerrado; no solicitar más comandos para esta prueba. Elevar temporalmente permisos en MikroTik:

```routeros
/user group set [find name="spicyops-read"] policy=read,write,api
```

Write es un permiso amplio del router, no restringido por RouterOS a .62. En este piloto se concede únicamente durante este diagnóstico, con origen de cuenta/servicio ya limitado a Raspberry. No ejecutar otros scripts o acciones con esa cuenta durante el ensayo.

En Raspberry, ejecutar el bloque completo; escribir la contraseña solo en el prompt oculto:

```sh
"$HOME/spicyops-prueba/.venv/bin/python" - <<'PY'
from functools import partial
from getpass import getpass
from pathlib import Path
import ssl
from librouteros import connect

host = "192.168.8.1"
ctx = ssl.create_default_context(cafile=str(Path.home() / "spicyops-ca.crt"))
api = connect(host=host, port=8729, username="spicyops-agent",
              password=getpass("Clave de spicyops-agent: "),
              ssl_wrapper=partial(ctx.wrap_socket, server_hostname=host), timeout=10)
try:
    path = api.path("queue", "simple")
    matches = [q for q in path if q.get("name") == "011_Lulu Mendoza"]
    if len(matches) != 1:
        raise RuntimeError("Cola ausente o duplicada; no se escribe.")
    before = matches[0]
    if (before.get("target") != "192.168.8.62/32"
            or before.get("max-limit") not in ("2000000/4000000", "2M/4M")
            or before.get("disabled") not in (False, "false", "no")):
        raise RuntimeError("El estado difiere del esperado; no se escribe.")
    path.update(**{".id": before[".id"], "max-limit": before["max-limit"]})
    matches = [q for q in path if q.get(".id") == before[".id"]]
    if len(matches) != 1:
        raise RuntimeError("No se pudo comprobar la cola despues de escribir.")
    fields = ("name", "target", "disabled", "parent", "max-limit",
              "burst-limit", "burst-threshold", "burst-time",
              "limit-at", "priority", "queue", "bucket-size", "packet-marks")
    if any(before.get(k) != matches[0].get(k) for k in fields):
        raise RuntimeError("Hay una diferencia de configuracion; revisar en MikroTik.")
    print("Escritura API del mismo limite: OK")
    print("Cliente: 011_Lulu Mendoza | IP: 192.168.8.62")
    print("Plan conservado: 2 Mbps subida / 4 Mbps bajada")
    print("No se modifico Morosos ni se probo un corte.")
finally:
    api.close()
PY
```

El diagnóstico valida nombre único, IP exclusiva, límite esperado y cola habilitada. Escribe únicamente el mismo max-limit por ID recién consultado y después compara las propiedades de configuración del servicio; no crea objetos, no cambia orden ni escribe en Morosos. Un fallo de comprobación se reporta como tal, sin intentar restauraciones globales. No incorporar credenciales en el archivo ni en la salida compartida.

Al terminar la prueba, incluso si falla, volver a MikroTik y restaurar permisos de lectura:

```routeros
/user group set [find name="spicyops-read"] policy=read,api
/user group print detail without-paging where name="spicyops-read"
```

Compartir resultado del diagnóstico y grupo final sin contraseña. No declarar completado el ensayo sin revisar ambos. La devolución de permisos depende de que el operador ejecute el comando: no es automática. Al escribir el mismo valor no se prepara un temporizador de reversión de plan; para una prueba futura que sí cambie acceso o velocidad habrá que definir y comprobar recuperación antes.

Fuente del método update: [librouteros Path](https://librouteros.readthedocs.io/en/latest/path.html).

## Retirada de escritura confirmada

El usuario compartió el diagnóstico exitoso y ejecutó el retorno policy=read,api, pero la impresión posterior conserva write positivo. No se atribuye a una causa concreta. La negación explícita siguiente se ejecutó posteriormente y su salida confirmó !write; la reducción de permisos está completada. Comandos conservados como referencia, no deben repetirse para cerrar este ensayo:

```routeros
/user group set [find name="spicyops-read"] policy=read,api,!write
/user group print detail without-paging where name="spicyops-read"
```

Resultado requerido: read y api positivos, write negado con !write. Si persiste write positivo o aparece error, detener y deshabilitar la cuenta de diagnóstico antes de investigar por qué no cambia; no continuar con cambios de cliente. El comando de contingencia es `/user disable [find name="spicyops-agent"]`, solo si no se logra retirar el permiso. No es necesario alterar la cola ni Morosos para corregir permisos.

## Registro

| Hito | Estado |
|---|---|
| Selección de cliente | Confirmada por instrucción del usuario y captura |
| Referencia visual | Habilitada, .62, límite 2M/4M |
| Lectura actual y unicidad | Salidas confirman cola .62/32 habilitada, 2M/4M, sin burst y entrada Morosos deshabilitada; el diagnóstico revalida unicidad antes de escribir |
| Comprobación desde un dispositivo del abonado | No disponible; usuario remoto en Guadalajara. No se afirmará efecto real |
| Recuperación y ventana concreta | Sin cambio de plan en el primer ensayo; retorno manual a read,api. Recuperación automática pendiente antes de cambios reales |
| Cambios temporales | Escritura API del mismo max-limit confirmada; sin reducción ni suspensión. Permiso write retirado y comprobado |
| Restauración final | Plan 2M/4M conservado; grupo con read,api y !write confirmado. Prueba cerrada, sin más comandos pendientes para este ensayo |

## Cierre

El usuario pidió terminar la secuencia de comandos. Tras la última salida del grupo se confirma read,api y !write; no se proponen más pruebas de clientes ahora. Quedan como límites de evidencia, no como tareas que deba ejecutar el usuario en este momento: no se midió velocidad desde la vivienda, no se probó suspensión/reactivación real ni alta técnica nueva. El portal permanece secundario. La siguiente fase puede continuar con diseño/documentación del proyecto.
