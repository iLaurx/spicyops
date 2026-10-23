"""Coordinación local al proceso; nunca envía acciones de escritura al conector."""
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import threading
import time

from django.shortcuts import redirect
from .store import Store

INTERVALS = (1, 5, 10, 15, 30, 60)
_guard = threading.Lock()
_locks = {}


def locality_lock(profile_id):
    with _guard:
        return _locks.setdefault(profile_id, threading.RLock())


def locality_available(profile_id):
    lock = locality_lock(profile_id)
    if not lock.acquire(blocking=False):
        return False
    lock.release()
    return True


def exclusive_view(view):
    @wraps(view)
    def wrapped(request, profile_id=None, **kwargs):
        if not profile_id or request.method != 'POST':
            return view(request, **kwargs) if not profile_id else view(request, profile_id=profile_id, **kwargs)
        lock = locality_lock(profile_id)
        if not lock.acquire(blocking=False):
            request.session['notice'] = 'La localidad tiene una operación en curso. Espera a que termine.'
            return redirect('connections' if view.__name__ != 'morosity' else 'clients')
        try:
            return view(request, profile_id=profile_id, **kwargs)
        finally:
            lock.release()
    return wrapped


def auto_context(profile):
    config = profile.get('automatic', {})
    enabled = config.get('enabled', False)
    status = ('localidad desconectada' if not profile.get('connected') else
              'desactivada' if not enabled else
              'actualizando' if profile.get('operation_active') else
              'esperando reintento' if config.get('failures', 0) else 'programada')
    return dict(enabled=enabled, interval=config.get('interval', 5), status=status,
                next_at=config.get('next_at') if enabled and profile.get('connected') else None)


class Coordinator:
    """Un propietario en run_panel, sin cola de ciclos ni recuperación de atrasos.

    El reloj y la función de lectura son sustituibles para pruebas sin red.
    Tras 3 reintentos (1, 2 y 4 minutos), espera al menos 15 minutos.
    """
    def __init__(self, refresh, *, clock=time.time, store=None, workers=2):
        self.refresh = refresh
        self.clock = clock
        self.store = store or Store()
        self.workers = workers
        self.stop_event = threading.Event()
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='spicyops-read')
        self.pending = {}
        self.thread = None
        self.schedule_snapshot = None

    def prepare(self):
        now = self.clock()
        def reset(data):
            index = 0
            for profile in sorted(data['profiles'].values(), key=lambda p: p['id']):
                profile['operation_active'] = False
                profile['busy_until'] = 0
                config = profile.setdefault('automatic', {'enabled': False, 'interval': 5})
                config['failures'] = 0
                config['next_at'] = None
                if profile.get('connected') and config.get('enabled'):
                    # Espaciar arranque y no reproducir ejecuciones perdidas.
                    config['next_at'] = now + config.get('interval', 5)*60 + index*3
                    index += 1
        self.store.update(reset)

    def start(self):
        if self.thread is not None:
            return
        self.prepare()
        self.thread = threading.Thread(target=self.run, name='spicyops-coordinator', daemon=True)
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            self.tick()
            self.stop_event.wait(1)

    def tick(self):
        if self.stop_event.is_set():
            return
        self.pending = {key: future for key, future in self.pending.items() if not future.done()}
        self.schedule_snapshot = self.store.schedule(self.schedule_snapshot)
        profiles = self.schedule_snapshot[1]
        due = sorted(profiles, key=lambda p: p.get('automatic', {}).get('next_at') or float('inf'))
        for profile in due:
            if len(self.pending) >= self.workers:
                break
            config = profile.get('automatic', {})
            if (profile['id'] not in self.pending and profile.get('connected') and config.get('enabled')
                    and not profile.get('operation_active') and (profile.get('busy_until') or 0) <= self.clock()
                    and config.get('next_at') is not None and config['next_at'] <= self.clock()
                    and locality_available(profile['id'])):
                self.pending[profile['id']] = self.pool.submit(self.execute, profile['id'])

    def execute(self, profile_id):
        lock = locality_lock(profile_id)
        if not lock.acquire(blocking=False):
            return
        try:
            profile = self.store.read()['profiles'].get(profile_id, {})
            config = profile.get('automatic', {})
            if (self.stop_event.is_set() or not profile.get('connected') or not config.get('enabled')
                    or not config.get('next_at') or config['next_at'] > self.clock()):
                return
            if profile.get('busy_until', 0) > self.clock():
                return
            # La lectura compartida guarda resultado, fecha y siguiente ejecución.
            self.refresh(profile_id)
        finally:
            lock.release()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        # Las lecturas SSH tienen plazos acotados. Esperar su persistencia antes de salir.
        self.pool.shutdown(wait=True, cancel_futures=True)


def finish_schedule(profile, now, error):
    config = profile.setdefault('automatic', {'enabled': False, 'interval': 5})
    failures = config.get('failures', 0) + 1 if error else 0
    config['failures'] = min(failures, 4)
    delay = (60 * 2**(failures-1) if failures <= 3 else max(900, config['interval']*60)) if error else config['interval']*60
    config['next_at'] = now + delay if config.get('enabled') and profile.get('connected') else None
