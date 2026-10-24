"""Entrada de SpicyOps para Windows. No arranca PostgreSQL ni un agente simulado."""
import argparse
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

def open_window(target):
    for prefix in (os.environ.get('PROGRAMFILES(X86)',''),os.environ.get('PROGRAMFILES','')):
        edge=Path(prefix)/'Microsoft/Edge/Application/msedge.exe'
        if edge.is_file():
            subprocess.Popen([str(edge),'--app='+target],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return
    import webbrowser
    webbrowser.open(target)

def instance_lock(folder):
    file=(folder/'instance.lock').open('a+b')
    file.seek(0);file.write(b'1');file.flush();file.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return file
    except OSError:
        file.close()
        return None

def main():
    parser = argparse.ArgumentParser(description='SpicyOps para Windows')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--state-dir')
    parser.add_argument('--tray', action='store_true', help='Mantener bandeja incluso con --no-open')
    args = parser.parse_args()
    if args.state_dir:
        os.environ['SPICYOPS_STATE_DIR'] = str(Path(args.state_dir).resolve())
    elif getattr(sys, 'frozen', False):
        os.environ.setdefault('SPICYOPS_STATE_DIR', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'SpicyOps'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','spicyops.portal_settings')
    folder=Path(os.environ.get('SPICYOPS_STATE_DIR',Path(__file__).resolve().parent/'.local'/'portal'))
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=instance_lock(folder)
    import django
    django.setup()
    from django.conf import settings
    from django.core import signing
    from django.core.wsgi import get_wsgi_application
    from waitress import create_server
    if lock is None:
        for _ in range(30):
            if (folder/'runtime.json').exists():break
            time.sleep(.1)
        runtime=json.loads((folder/'runtime.json').read_text())
        if not args.no_open:
            token=signing.dumps('open',salt='spicyops-desktop-open')
            open_window(f'http://127.0.0.1:{runtime["port"]}/open/{token}/')
        return
    logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
    server = create_server(get_wsgi_application(), host='127.0.0.1', port=args.port, threads=6, channel_timeout=70,
                           clear_untrusted_proxy_headers=True)
    token = signing.dumps('open',salt='spicyops-desktop-open')
    url = f'http://127.0.0.1:{server.effective_port}/open/{token}/'
    runtime = Path(settings.STATE_DIR) / 'runtime.json'
    runtime.write_text(json.dumps({'pid':os.getpid(), 'port':int(server.effective_port), 'launch_url':url}))
    runtime.chmod(0o600)
    from portal.scheduling import Coordinator
    from portal.views import refresh_profile
    coordinator = Coordinator(refresh_profile)
    coordinator.start()
    def reopen():
            # Cada reapertura obtiene un enlace corto; no se reutiliza el enlace caducado.
            fresh = signing.dumps('open',salt='spicyops-desktop-open')
            target = f'http://127.0.0.1:{server.effective_port}/open/{fresh}/'
            open_window(target)
    if not args.no_open:
        threading.Timer(.6, reopen).start()
    try:
        from portal.runtime import exit_requested
        if os.name == 'nt' and (not args.no_open or args.tray):
            import pystray
            from PIL import Image
            import portal
            thread=threading.Thread(target=server.run,daemon=True)
            thread.start()
            def exit_app(icon,item):
                exit_requested.set()
                icon.stop()
            icon=pystray.Icon('SpicyOps',Image.open(Path(portal.__file__).parent/'static/portal/app.ico'),'SpicyOps',
                pystray.Menu(pystray.MenuItem('Abrir SpicyOps',lambda icon,item:reopen(),default=True),
                    pystray.MenuItem('Salir de SpicyOps',exit_app)))
            def stop_when_requested():
                exit_requested.wait()
                icon.stop()
            threading.Thread(target=stop_when_requested, daemon=True).start()
            def tray_ready(icon):
                icon.visible = True
                info = json.loads(runtime.read_text())
                info['tray_ready'] = True
                runtime.write_text(json.dumps(info))
            icon.run(setup=tray_ready)
        else:
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            exit_requested.wait()
    finally:
        coordinator.stop_event.set()
        server.close()
        coordinator.stop()
        server.task_dispatcher.shutdown(timeout=120)
        lock.close()

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        # No imprimir variables de entorno, rutas SSH, credenciales ni configuración.
        if getattr(sys,'frozen',False) and '--no-open' in sys.argv:
            folder=Path(os.environ.get('SPICYOPS_STATE_DIR','.'))
            folder.mkdir(parents=True,exist_ok=True)
            (folder/'startup-error.json').write_text(json.dumps({'error_type':type(exc).__name__}))
            raise SystemExit(1)
        elif getattr(sys,'frozen',False):
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, 'No se pudo abrir SpicyOps. Comprueba espacio libre y permisos en tu carpeta de datos de Windows. Si hay otra instancia iniciándose, espera y vuelve a abrir. Conserva los archivos privados; no los borres.', 'SpicyOps', 0x10)
        else: raise
