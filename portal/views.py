from datetime import datetime
import hashlib
import json
import time
import uuid
from django.utils import timezone
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.http import Http404
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from .auth import protected
from .connector import collect, ConnectionFailure
from .forms import ConnectionForm
from .store import Store
from .telemetry import normalize, same_boot, estimate_uptime, apply_inclusions, carry_counter_validity
from . import diagnostics
from .scheduling import auto_context, exclusive_view, locality_lock, finish_schedule, INTERVALS

def profiles_context(request, profile_id=None):
    data = Store().read()
    profiles = list(data['profiles'].values())
    profiles.sort(key=lambda p: p['name'].lower())
    selected = profile_id or request.GET.get('site') or request.session.get('site')
    all_sites = selected == 'all' and request.resolver_match.url_name == 'clients'
    active = None if all_sites else next((p for p in profiles if p['id'] == selected), profiles[0] if profiles else None)
    if not request.headers.get('X-SpicyOps-Live'):
        if active and selected != 'all': request.session['site'] = active['id']
        elif all_sites: request.session['site'] = 'all'
    # Nunca pasar credenciales, pin ni rutas de acceso a las plantillas generales.
    safe = [{k: p.get(k) for k in ('id','name','host','ssh_user','connected','last_error','last_read','last_error_at','last_attempt','inventory_revision')} for p in profiles]
    for locality, profile in zip(safe, profiles):
        locality['automatic'] = auto_context(profile)
        locality['connection_state'] = ('offline' if not locality['connected'] else
            'error' if locality['last_error'] else 'online')
        locality['connection_label'] = {'offline': 'Desconectada', 'error': 'Error de conexión',
            'online': 'Activa'}[locality['connection_state']]
    latest = active['history'][-1] if active and active.get('history') else None
    return data, active, {'localities': safe, 'all_sites': all_sites, 'active': next((p for p in safe if active and p['id'] == active['id']), None),
        'healthy_localities': sum(p['connection_state'] == 'online' for p in safe),
        'error_localities': sum(p['connection_state'] == 'error' for p in safe),
        'live_revision': hashlib.sha256(json.dumps(safe, sort_keys=True).encode()).hexdigest(),
        'snapshot': latest, 'fresh': bool(active and active.get('connected') and latest and not active.get('last_error') and time.time()-latest['timestamp'] < 120)}

def notice(request):
    return '' if request.headers.get('X-SpicyOps-Live') else request.session.pop('notice', '')

def apply_metadata(rows, profile):
    meta = profile.get('metadata', {}) if profile else {}
    for row in rows:
        details = meta.get(row['id']+'|'+row['ip'], {})
        row['display_name'] = details.get('alias') or row['name']
        row['metadata'] = details
    return rows

@protected
def analytics(request):
    _, profile, context = profiles_context(request)
    if not request.headers.get('X-SpicyOps-Live'): request.session.pop('mode', None)
    history = profile.get('history', []) if profile else []
    rows, summary = estimate_uptime(history)
    apply_metadata(rows, profile)
    bars = []
    recent = history[-13:]
    for before, after in zip(recent, recent[1:]):
        if same_boot(before, after):
            previous={c['fingerprint']:c for c in before['clients']}
            changes=[]
            for client in after['clients']:
                old=previous.get(client['fingerprint'])
                if (old and not old['ambiguous'] and not client['ambiguous'] and old['bytes'] is not None
                        and client['bytes'] is not None and all(client[k] >= old[k] for k in ('upload_bytes','download_bytes'))):
                    changes.append(client['bytes']-old['bytes'])
            if changes: bars.append({'bytes':sum(changes), 'start':before['timestamp'], 'at':after['timestamp']})
    peak = max((bar['bytes'] for bar in bars), default=0)
    previous_day = None
    day_index = -1
    for bar in bars:
        local_end = datetime.fromtimestamp(bar['at'], timezone.get_current_timezone())
        if local_end.date() != previous_day:
            day_index += 1
            previous_day = local_end.date()
        bar['day_tone'] = day_index % 2
        bar['date_label'] = local_end.strftime('%d/%m')
        bar['height'] = (bar['bytes']/peak*100) if peak else 0
    context.update(page='analytics', rows=sorted(rows,key=lambda r:r['monthly_bytes'] or 0,reverse=True), summary=summary, bars=bars, peak=peak, message=notice(request))
    return render(request, 'portal/analytics.html', context)

@protected
def clients(request):
    data, profile, context = profiles_context(request)
    profiles = ([data['profiles'][p['id']] for p in context['localities'] if p['connected']]
        if context['all_sites'] else [profile] if profile else [])
    rows = []
    for locality in profiles:
        latest = locality['history'][-1] if locality.get('history') else None
        clients_rows = apply_metadata([dict(row) for row in latest['clients']], locality) if latest else []
        for row in clients_rows:
            row.update(locality_id=locality['id'], locality_name=locality['name'],
                locality_connected=locality.get('connected', False), locality_error=locality.get('last_error', ''),
                locality_timestamp=latest['timestamp'])
        rows.extend(clients_rows)
    total_clients = len(rows)
    query = request.GET.get('q', '').strip()[:150]
    if query: rows = [r for r in rows if query.lower() in (r['display_name']+' '+r['ip']+' '+r['name']+' '+r['locality_name']).lower()]
    context.update(page='clients', rows=rows, total_clients=total_clients, query=query,
        active_localities=len(profiles), message=notice(request))
    return render(request, 'portal/clients.html', context)

@protected
def connections(request):
    data, _, context = profiles_context(request)
    saved = {key: p.get('diagnostic') for key, p in data['profiles'].items()}
    if any(value and value['running'] and data['profiles'][key].get('busy_until', 0) <= time.time()
           for key, value in saved.items()):
        saved = Store().update(lambda current: {key: diagnostics.recover(p) for key, p in current['profiles'].items()})
    for locality in context['localities']:
        locality['diagnostic'] = saved.get(locality['id'])
    context.update(page='connections', intervals=INTERVALS, message=notice(request))
    return render(request, 'portal/connections.html', context)

@require_POST
@protected
def diagnose(request, profile_id):
    try: return JsonResponse(diagnostics.start(profile_id), status=202)
    except ValueError as exc: return JsonResponse({'message': str(exc)}, status=409)

@protected
def diagnostic_status(request, profile_id):
    store = Store()
    profile = store.read()['profiles'].get(profile_id)
    if not profile: raise Http404()
    result = profile.get('diagnostic')
    if result and result['running'] and profile.get('busy_until', 0) <= time.time():
        result = store.update(lambda data: diagnostics.recover(data['profiles'][profile_id]))
    return JsonResponse(result or {})

@sensitive_post_parameters('ssh_password','router_password')
@protected
@exclusive_view
def connect(request, profile_id=None):
    store = Store()
    existing = store.read()['profiles'].get(profile_id) if profile_id else None
    if profile_id and not existing: raise Http404()
    if existing and request.method == 'POST' and existing.get('busy_until', 0) > time.time():
        request.session['notice'] = 'Espera a que termine la operación de la localidad antes de configurarla.'
        return redirect('connections')
    payload = request.POST.copy() if request.method == 'POST' else None
    if existing and payload is not None:
        for field in ('ssh_password','router_password'):
            if not payload.get(field): payload[field] = existing.get(field,'')
        # La misma Raspberry puede cambiar de IP LAN a Tailscale: conservar su
        # identidad SSH. Un equipo con otra clave no sustituye al anterior.
        if existing.get('fingerprint') or not request.session.get('pending_connection'):
            payload['fingerprint'] = existing.get('fingerprint','')
    pending_key = request.session.get('pending_connection')
    pending = store.read().get('pending', {}).get(pending_key) if pending_key else None
    if pending and pending['expires'] > time.time() and payload is not None:
        for field in ('ssh_password','router_password'):
            if not payload.get(field): payload[field] = pending['data'][field]
        # La huella solo se acepta si coincide con la obtenida en la conexión anterior.
        if payload.get('fingerprint') != pending['fingerprint']:
            payload['fingerprint'] = ''
    initial = {k:v for k,v in (existing or {}).items() if k in ConnectionForm.base_fields and k not in ('ssh_password','router_password')}
    form = ConnectionForm(payload, initial=initial)
    if existing and request.method == 'GET':
        form.fields['router_password'].required = False
    fingerprint = ''
    error_stage = ''
    if request.method == 'POST' and form.is_valid():
        profile = dict(form.cleaned_data)
        profile['id'] = profile_id or uuid.uuid4().hex
        configuration_id = uuid.uuid4().hex
        try:
            if existing:
                def claim_configuration(data):
                    current = data['profiles'].get(profile_id)
                    if not current or current.get('busy_until', 0) > time.time():
                        raise ConnectionFailure('La localidad tiene una operación en curso. Espera y vuelve a configurarla.')
                    current.update(generation=configuration_id, busy_until=time.time()+75)
                store.update(claim_configuration)
                existing['generation'] = configuration_id
            profile['inclusions'] = list((existing or {}).get('inclusions', ()))
            deadline = time.monotonic()+60
            sample = normalize(collect(profile), time.time(), deadline=deadline, inclusions=profile['inclusions'])
            carry_counter_validity((existing or {}).get('history', []), sample)
            profile.update(connected=True, last_read=sample['timestamp'], last_error='',
                history=((existing or {}).get('history',[]) + [sample])[-1440:], metadata=(existing or {}).get('metadata',{}))
            profile['automatic'] = dict((existing or {}).get('automatic', {'enabled': False, 'interval': 5}))
            profile['last_attempt'] = sample['timestamp']
            finish_schedule(profile, time.time(), '')
            def save(data):
                # Limitar perfiles y eliminar conexiones pendientes caducadas.
                current = data['profiles'].get(profile['id'])
                if existing and (not current or current.get('generation') != existing.get('generation')
                        ):
                    raise ConnectionFailure('La localidad cambió o tiene una operación en curso. Espera y vuelve a configurarla.')
                if not existing and len(data['profiles']) >= 100: raise ValueError('Se alcanzó el límite de localidades de esta instalación.')
                if current:
                    # Una edición local puede guardarse mientras se comprueba el acceso.
                    profile['metadata'] = current.get('metadata', {})
                if current and current.get('diagnostic'):
                    profile['diagnostic'] = dict(current['diagnostic'], stale=True)
                data['profiles'][profile['id']] = profile
                data['pending'] = {k:v for k,v in data.get('pending',{}).items() if v['expires'] > time.time() and k != pending_key}
            store.update(save)
            request.session['site'] = profile['id']
            request.session.pop('pending_connection',None)
            request.session['notice'] = 'Raspberry y MikroTik conectados. Los clientes se importaron desde las colas del router.'
            return redirect('analytics')
        except ConnectionFailure as exc:
            form.add_error(None, str(exc))
            fingerprint, error_stage = exc.fingerprint, exc.stage
            if fingerprint:
                pending_key = uuid.uuid4().hex
                def stage(data):
                    data['pending'] = {k:v for k,v in data.get('pending',{}).items() if v['expires'] > time.time()}
                    data['pending'][pending_key] = {'data': profile, 'fingerprint': fingerprint, 'expires': time.time()+600}
                store.update(stage)
                request.session['pending_connection'] = pending_key
                # El navegador conserva los campos públicos; las claves solo permanecen cifradas en el servidor.
                form.fields['ssh_password'].required = False
                form.fields['router_password'].required = False
                form.data = form.data.copy()
                form.data['fingerprint'] = fingerprint
        except (ValueError, KeyError, TimeoutError):
            form.add_error(None, 'La lectura del MikroTik está incompleta o tiene un formato no compatible; no se importaron datos parciales.')
        finally:
            if existing:
                def release_configuration(data):
                    current = data['profiles'].get(profile_id)
                    if current and current.get('generation') == configuration_id:
                        current['busy_until'] = 0
                store.update(release_configuration)
    _, _, context = profiles_context(request)
    context.update(page='connections', form=form, fingerprint=fingerprint, error_stage=error_stage, editing=bool(existing))
    return render(request, 'portal/connect.html', context)

def refresh_profile(profile_id):
    lock = locality_lock(profile_id)
    if not lock.acquire(blocking=False):
        raise ValueError('La localidad tiene una operación en curso. Espera a que termine.')
    try:
        return _refresh_profile(profile_id)
    finally:
        lock.release()


def _refresh_profile(profile_id):
    store = Store()
    now = time.time()
    generation = uuid.uuid4().hex
    def start(data):
        profile = data['profiles'].get(profile_id)
        if not profile or not profile.get('connected'): raise ValueError('La localidad está desconectada.')
        if profile.get('busy_until',0) > now: raise ValueError('Esta localidad ya está leyendo el MikroTik. Espera a que termine.')
        profile['generation'], profile['busy_until'] = generation, now+65
        profile['operation_active'] = True
        return dict(profile)
    profile = store.update(start)
    error = ''
    sample = None
    deadline = time.monotonic()+60
    try: sample = normalize(collect(profile), time.time(), deadline=deadline, inclusions=profile.get('inclusions', ()))
    except ConnectionFailure as exc: error = str(exc)
    except (ValueError, KeyError, TypeError): error = 'La lectura está incompleta; se conserva la última lectura válida.'
    except Exception: error = 'No se pudo completar la lectura; se conserva la última lectura válida.'
    def finish(data):
        current = data['profiles'].get(profile_id)
        if not current or current.get('generation') != generation: return
        current['busy_until'] = 0
        current['operation_active'] = False
        current['last_error'] = error
        current['last_attempt'] = time.time()
        if error: current['last_error_at'] = current['last_attempt']
        finish_schedule(current, time.time(), error)
        if sample:
            carry_counter_validity(current.get('history', []), sample)
            current['history'] = (current.get('history',[]) + [sample])[-1440:]
            current['last_read'] = sample['timestamp']
    store.update(finish)
    return error

@require_POST
@protected
def refresh(request, profile_id):
    try: error = refresh_profile(profile_id)
    except ValueError as exc: error = str(exc)
    request.session['notice'] = error or 'Lectura actualizada desde MikroTik.'
    request.session['site'] = profile_id
    request.session.pop('mode', None)
    return redirect('clients' if request.POST.get('next') == 'clients' else 'analytics')

@require_POST
@protected
@exclusive_view
def disconnect(request, profile_id):
    def stop(data):
        profile = data['profiles'].get(profile_id)
        if profile:
            if profile.get('busy_until', 0) > time.time():
                return False
            profile['connected'] = False
            profile['generation'] = uuid.uuid4().hex
            profile['busy_until'] = 0
            profile.setdefault('automatic', {'enabled': False, 'interval': 5})['next_at'] = None
            # Se conserva la lectura anterior y los datos editables; no las contraseñas.
            profile['ssh_password'] = profile['router_password'] = ''
            if profile.get('diagnostic'): profile['diagnostic']['stale'] = True
        return True
    if Store().update(stop) is False:
        request.session['notice'] = 'Espera a que termine la operación de la localidad antes de desconectarla.'
        return redirect('connections')
    request.session['notice'] = 'Localidad desconectada. Se conservaron sus lecturas y notas; se retiraron las contraseñas guardadas.'
    return redirect('connections')

@require_POST
@protected
def edit_client(request, profile_id, client_id):
    fields = {'alias':120, 'contact':160, 'location':200, 'notes':2000}
    values = {name:request.POST.get(name,'').strip() for name in fields}
    if any(len(values[name]) > maximum for name,maximum in fields.items()):
        return HttpResponseBadRequest('Uno de los campos excede su longitud permitida.')
    def update(data):
        profile = data['profiles'].get(profile_id)
        if not profile or not profile.get('history'): raise ValueError()
        client = next((c for c in profile['history'][-1]['clients'] if c['id'] == client_id),None)
        if not client: raise ValueError()
        profile.setdefault('metadata',{})[client_id+'|'+client['ip']] = values
    try: Store().update(update)
    except ValueError: return HttpResponseBadRequest('Ese cliente no pertenece a esta localidad.')
    if request.session.get('site') != 'all': request.session['site'] = profile_id
    request.session['notice'] = 'Datos del cliente guardados en esta instalación. La configuración de MikroTik se conserva.'
    return redirect('clients')


@require_POST
@protected
@exclusive_view
def morosity(request, profile_id, client_id):
    action = request.POST.get('action')
    if action not in ('suspend', 'restore') or request.POST.get('confirmed') != 'yes':
        return HttpResponseBadRequest('Confirma la acción de morosidad para este cliente.')
    store = Store()
    generation = uuid.uuid4().hex

    def claim(data):
        profile = data['profiles'].get(profile_id)
        if not profile or not profile.get('connected') or not profile.get('history'):
            raise ValueError('Conecta la localidad antes de cambiar Morosos.')
        if profile.get('busy_until', 0) > time.time():
            raise ValueError('La localidad tiene una operación en curso. Espera y sincroniza.')
        if profile.get('last_error'):
            raise ValueError('Sincroniza la localidad para confirmar su estado antes de cambiar Morosos.')
        sample = profile['history'][-1]
        client = next((c for c in sample['clients'] if c['id'] == client_id), None)
        if (not client or client['ambiguous'] or client['disabled'] or client.get('restriction_unsafe') or
                client['fingerprint'] != request.POST.get('fingerprint') or
                client['restricted'] == (action == 'suspend')):
            raise ValueError('El cliente o su estado cambió. Sincroniza y vuelve a seleccionarlo.')
        profile['generation'], profile['busy_until'] = generation, time.time()+90
        profile['operation_active'] = True
        operation = {k: client[k] for k in ('id', 'name', 'ip')}
        operation.update(action=action, identity=sample['identity'])
        return dict(profile), operation

    try:
        profile, operation = store.update(claim)
    except ValueError as exc:
        request.session['notice'] = str(exc)
        if request.session.get('site') != 'all': request.session['site'] = profile_id
        return redirect('clients')
    sample, error = None, ''
    try:
        deadline = time.monotonic()+60
        sample = normalize(collect(profile, morosity=operation), time.time(), deadline=deadline, inclusions=profile.get('inclusions', ()))
        observed = next((c for c in sample['clients'] if c['fingerprint'] == request.POST['fingerprint']), None)
        if not observed or observed.get('restriction_unsafe') or observed['restricted'] != (action == 'suspend'):
            error = 'No se pudo confirmar el estado del cliente. Sincroniza antes de reintentar.'
    except ConnectionFailure as exc:
        error = str(exc) + ' El resultado puede ser incierto; sincroniza antes de reintentar.'
    except (ValueError, KeyError, TypeError):
        error = 'Respuesta incompleta. El resultado puede ser incierto; sincroniza antes de reintentar.'
    except Exception:
        error = 'No se pudo completar la operación. El resultado puede ser incierto; sincroniza antes de reintentar.'

    def finish(data):
        current = data['profiles'].get(profile_id)
        if not current or current.get('generation') != generation:
            return
        current['busy_until'] = 0
        current['operation_active'] = False
        current['last_error'] = error
        current['last_attempt'] = time.time()
        if error: current['last_error_at'] = current['last_attempt']
        if sample:
            carry_counter_validity(current.get('history', []), sample)
            current['history'] = (current.get('history', []) + [sample])[-1440:]
            current['last_read'] = sample['timestamp']
    store.update(finish)
    if request.session.get('site') != 'all': request.session['site'] = profile_id
    request.session['notice'] = error or (
        'IP agregada a Morosos; estado confirmado en MikroTik. El corte depende de sus reglas de firewall.'
        if action == 'suspend' else
        'IP retirada de Morosos; estado confirmado en MikroTik. Comprueba el acceso del cliente.')
    return redirect('clients')


@protected
@exclusive_view
def inventory(request, profile_id):
    store = Store()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action not in ('include', 'revert'):
            return HttpResponseBadRequest('Selecciona una acción disponible.')
        def save(data):
            profile = data['profiles'].get(profile_id)
            if not profile or not profile.get('history'):
                raise ValueError('Sincroniza la localidad para revisar su inventario.')
            if profile.get('busy_until', 0) > time.time():
                raise ValueError('Espera a que termine la operación y sincroniza.')
            sample = profile['history'][-1]
            candidate = next((c for c in sample.get('inventory', [])
                              if c['fingerprint'] == request.POST.get('fingerprint')), None)
            if (not candidate or not candidate.get('inclusion_eligible') or
                    str(sample['timestamp']) != request.POST.get('reading')):
                raise ValueError('La cola cambió o no es individual válida. Sincroniza y vuelve a revisarla.')
            inclusions = set(profile.get('inclusions', ()))
            if action == 'include': inclusions.add(candidate['fingerprint'])
            else: inclusions.discard(candidate['fingerprint'])
            profile['inclusions'] = sorted(inclusions)
            apply_inclusions(sample, inclusions)
            profile['inventory_revision'] = uuid.uuid4().hex
        try:
            store.update(save)
            request.session['notice'] = 'Excepción de inventario guardada. No se envió ningún cambio al router.'
        except ValueError as exc:
            request.session['notice'] = str(exc)
        return redirect('inventory', profile_id=profile_id)
    data, _, context = profiles_context(request, profile_id=profile_id)
    profile = data['profiles'].get(profile_id)
    if not profile: raise Http404()
    sample = profile['history'][-1] if profile.get('history') else {}
    context.update(page='clients', inventory_profile={'id': profile_id, 'name': profile['name']},
        excluded_queues=sample.get('excluded_queues', []), reading=str(sample.get('timestamp', '')),
        included_queues=[c for c in sample.get('clients', []) if c.get('infrastructure')],
        inventory_available='inventory' in sample, message=notice(request))
    return render(request, 'portal/inventory.html', context)


@require_POST
@protected
@exclusive_view
def automatic(request, profile_id):
    try:
        interval = int(request.POST.get('interval', '5'))
        if interval not in INTERVALS: raise ValueError()
    except ValueError:
        return HttpResponseBadRequest('Selecciona un intervalo disponible.')
    def save(data):
        profile = data['profiles'].get(profile_id)
        if not profile: raise Http404()
        if profile.get('busy_until', 0) > time.time():
            return False
        enabled = request.POST.get('enabled') == 'on'
        profile['automatic'] = dict(enabled=enabled, interval=interval, failures=0,
            next_at=time.time()+interval*60 if enabled and profile.get('connected') else None)
        return True
    saved = Store().update(save)
    request.session['notice'] = ('Preferencia de actualización automática guardada.' if saved else
        'La localidad tiene una operación en curso. Espera a que termine.')
    return redirect('connections')
