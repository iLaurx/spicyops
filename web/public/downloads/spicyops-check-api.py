from functools import partial
from getpass import getpass
from pathlib import Path
import ssl
import sys
from librouteros import connect

if not sys.stdin.isatty():
    raise SystemExit("Ejecuta este archivo desde una terminal interactiva.")

ip = "192.168.88.1"
ctx = ssl.create_default_context(
    cafile=str(Path.home() / "spicyops-certs" / "spicyops-ca.crt")
)
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
api = connect(
    host=ip,
    port=8729,
    username="spicyops-agent",
    password=getpass("Contraseña API (no se muestra): "),
    ssl_wrapper=partial(ctx.wrap_socket, server_hostname=ip),
    timeout=8,
)
try:
    for path, properties in [
        ("/system/identity/print", "name"),
        ("/system/resource/print", "uptime,version,board-name"),
        ("/queue/simple/print", ".id,name,target,bytes"),
        ("/ip/firewall/address-list/print", ".id,list,address,disabled"),
    ]:
        count = sum(1 for _ in api(path, **{".proplist": properties}))
        print(path, "OK; registros:", count)
finally:
    api.close()
