"""Bloqueos siempre router -> servicio -> tarea. PostgreSQL es obligatorio."""
import hashlib
import secrets
import uuid
from datetime import timedelta
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from agent.contract import ACTIONS, validate_state
from .models import Agent, Attempt, Event, Membership, Router, Service, Task

LEASE_SECONDS = 30
MAX_ATTEMPTS = 5

def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def authenticate(agent_id, token):
    try:
        agent = Agent.objects.get(pk=agent_id, active=True)
    except (Agent.DoesNotExist, ValueError, ValidationError):
        raise PermissionDenied('Identidad no autorizada.')
    if not token or not secrets.compare_digest(agent.token_hash, token_digest(token)):
        raise PermissionDenied('Identidad no autorizada.')
    Agent.objects.filter(pk=agent.pk).update(last_seen=timezone.now())
    return agent

def can_edit(user, site_id):
    return Membership.objects.filter(user=user, site_id=site_id, role__in=['admin', 'operator']).exists()

def require_edit(user, site_id):
    if not can_edit(user, site_id):
        raise PermissionDenied('No tienes permiso de operación en este sitio.')

def check_inventory(service):
    router = service.router
    site_id = router.site_id
    if (router.agent.site_id != site_id or router.node.site_id != site_id
            or service.customer.site_id != site_id or service.plan.site_id != site_id
            or (service.equipment_id and service.equipment.node.site_id != site_id)):
        raise ValueError('El inventario pertenece a otro sitio.')
    if not router.simulation:
        raise ValueError('Las operaciones reales están deshabilitadas en este MVP.')

@transaction.atomic
def request_action(user, service_id, action, plan_id, reason, expected_revision):
    if action not in ACTIONS or not reason.strip() or len(reason) > 240:
        raise ValueError('Selecciona una acción y escribe un motivo de hasta 240 caracteres.')
    reference = Service.objects.get(pk=service_id)
    require_edit(user, reference.router.site_id)
    Router.objects.select_for_update().get(pk=reference.router_id)
    service = Service.objects.select_for_update().get(pk=service_id)
    if type(expected_revision) is not int or expected_revision != service.revision:
        raise ValueError('La ficha cambió; recarga antes de solicitar otra acción.')
    if action == 'plan':
        from .models import Plan
        service.plan = Plan.objects.get(pk=plan_id, site_id=service.router.site_id)
    check_inventory(service)
    if action == 'suspend' and service.plan.commercial_free:
        raise ValueError('Plan FREE: requiere una decisión comercial fuera de este MVP.')
    if action in ('suspend', 'resume', 'plan') and not service.observed:
        raise ValueError('Primero solicita y verifica el alta técnica.')
    if action in ('provision', 'resume'):
        service.desired_enabled = True
    elif action == 'suspend':
        service.desired_enabled = False
    service.revision += 1
    state = {'service': service.id, 'ip': service.ip, 'revision': service.revision,
             'enabled': service.desired_enabled, 'up_kbps': service.plan.up_kbps, 'down_kbps': service.plan.down_kbps}
    validate_state(state, service.router.allowed_ips)
    service.save()
    now = timezone.now()
    # No invalidar una concesión activa: sigue reteniendo el router hasta reporte/vencimiento.
    for old in Task.objects.filter(service=service, status='pending'):
        old.status = 'obsolete'
        old.save(update_fields=['status'])
        Event.objects.create(task=old, message='Sustituida por una revisión posterior.')
    task = Task.objects.create(service=service, revision=service.revision, action=action, snapshot=state,
        requested_by=user, reason=reason.strip(), expires_at=now + timedelta(minutes=15), available_at=now)
    Event.objects.create(task=task, message='Intención y tarea guardadas en la misma transacción.')
    return task

def finish(task, status, error):
    task.status, task.error = status, error
    task.save()
    Event.objects.create(task=task, message=error)
    if task.attempt_token:
        Attempt.objects.filter(pk=task.attempt_token, finished_at=None).update(
            finished_at=timezone.now(), outcome=status)

@transaction.atomic
def claim(agent):
    now = timezone.now()
    for router in Router.objects.filter(agent=agent, site_id=agent.site_id).select_for_update(skip_locked=True).order_by('pk'):
        tasks = list(Task.objects.filter(service__router=router, status__in=['pending', 'leased']).order_by('created_at'))
        if any(t.status == 'leased' and t.lease_until > now for t in tasks):
            continue
        for task in tasks:
            if task.revision != task.service.revision:
                finish(task, 'obsolete', 'Revisión sustituida; no ejecutar.')
            elif task.expires_at <= now:
                finish(task, 'expired', 'Solicitud vencida; no ejecutar. El estado observado conserva su fecha anterior.')
            elif task.attempts >= MAX_ATTEMPTS:
                finish(task, 'verification', 'Límite de intentos; requiere verificación.')
            elif task.available_at <= now:
                check_inventory(task.service)
                validate_state(task.snapshot, router.allowed_ips)
                if task.attempt_token:
                    Attempt.objects.filter(pk=task.attempt_token, finished_at=None).update(finished_at=now, outcome='lease_expired')
                task.status = 'leased'
                task.attempts += 1
                task.attempt_token = uuid.uuid4()
                task.lease_until = now + timedelta(seconds=LEASE_SECONDS)
                task.save()
                Attempt.objects.create(token=task.attempt_token, task=task, number=task.attempts)
                Event.objects.create(task=task, message=f'Intento {task.attempts} reclamado durante {LEASE_SECONDS} s.')
                return envelope(task)
    return None

def envelope(task):
    return {'contract': 1, 'task': str(task.pk), 'attempt': str(task.attempt_token),
            'site': task.service.router.site_id, 'router': task.service.router_id, 'action': task.action,
            'state': task.snapshot, 'expires_at': task.expires_at.timestamp(), 'lease_until': task.lease_until.timestamp()}

def lock_task(agent, task_id):
    ref = Task.objects.filter(pk=task_id, service__router__agent=agent, service__router__site_id=agent.site_id).first()
    if ref is None:
        raise PermissionDenied('Tarea fuera del inventario del agente.')
    Router.objects.select_for_update().get(pk=ref.service.router_id)
    Service.objects.select_for_update().get(pk=ref.service_id)
    return Task.objects.select_for_update().get(pk=task_id)

def current(task, attempt):
    now = timezone.now()
    return (str(task.attempt_token) == str(attempt) and task.status == 'leased'
            and task.lease_until > now and task.expires_at > now and task.revision == task.service.revision)

@transaction.atomic
def validate_execution(agent, task_id, attempt):
    task = lock_task(agent, task_id)
    if not current(task, attempt):
        return None
    check_inventory(task.service)
    return envelope(task)

@transaction.atomic
def report(agent, task_id, attempt, body):
    task = lock_task(agent, task_id)
    history = Attempt.objects.filter(pk=attempt, task=task).first()
    if history and history.report:
        # Repetir exactamente el mismo reporte es seguro, incluso tras una revisión posterior.
        return 'duplicate' if history.report == body else 'conflict'
    if not current(task, attempt):
        return 'conflict'
    if set(body) != {'ok', 'state', 'error'} or type(body['ok']) is not bool:
        raise ValueError('Reporte fuera de contrato.')
    now = timezone.now()
    if body['ok']:
        validate_state(body['state'], task.service.router.allowed_ips)
        if body['state'] != task.snapshot or body['error']:
            raise ValueError('La comprobación del simulador no coincide con la intención.')
        task.result = body['state']
        task.status = 'verified'
        task.error = ''
        service = task.service
        service.observed, service.observed_at = body['state'], now
        service.save(update_fields=['observed', 'observed_at'])
    else:
        if body['state'] is not None or body['error'] not in ('execution_failed', 'verification_failed'):
            raise ValueError('Error fuera de contrato; no se aceptan mensajes arbitrarios.')
        task.error = 'No se pudo comprobar la aplicación; se reintentará leyendo el simulador.'
        task.status = 'pending' if task.attempts < MAX_ATTEMPTS else 'verification'
        task.available_at = now + timedelta(seconds=min(60, 2 ** task.attempts))
    task.save()
    history.finished_at, history.outcome, history.report = now, task.status, body
    history.save()
    Event.objects.create(task=task, message='Estado leído y verificado en simulación.' if body['ok'] else task.error)
    return 'accepted'
