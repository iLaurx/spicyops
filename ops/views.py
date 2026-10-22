import hashlib
import json
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import ActionForm, ServiceForm
from .models import Agent, Customer, Equipment, LoginWindow, Membership, Node, Plan, Router, Service, Task
from .queue import authenticate, can_edit, claim, report, request_action, require_edit, validate_execution

class LimitedLoginView(LoginView):
    template_name = 'registration/login.html'
    def post(self, request, *args, **kwargs):
        key = hashlib.sha256(request.META.get('REMOTE_ADDR', '').encode()).hexdigest()
        now = timezone.now()
        with transaction.atomic():
            LoginWindow.objects.get_or_create(key=key, defaults={'start': now})
            window = LoginWindow.objects.select_for_update().get(pk=key)
            if now - window.start > timedelta(minutes=5):
                window.count, window.start = 0, now
            if window.count >= 12:
                return render(request, self.template_name, {'form': self.get_form(), 'limited': True}, status=429)
            window.count += 1
            window.save()
        return super().post(request, *args, **kwargs)

def sites(user): return Membership.objects.filter(user=user).values('site_id')

def visible(user):
    return Service.objects.filter(router__site_id__in=sites(user)).select_related('customer', 'router__site', 'router__node', 'plan', 'equipment')

@login_required
def dashboard(request):
    return render(request, 'ops/dashboard.html', {'services': visible(request.user).order_by('customer__name'),
        'memberships': Membership.objects.filter(user=request.user).select_related('site'),
        'customers': Customer.objects.filter(site_id__in=sites(request.user)).order_by('name')})

@login_required
def inventory(request):
    scope = sites(request.user)
    return render(request, 'ops/inventory.html', {'routers': Router.objects.filter(site_id__in=scope).select_related('site', 'node', 'agent'),
        'nodes': Node.objects.filter(site_id__in=scope), 'equipment': Equipment.objects.filter(node__site_id__in=scope).select_related('node', 'upstream'),
        'plans': Plan.objects.filter(site_id__in=scope)})

@login_required
def create_service(request):
    form = ServiceForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        require_edit(request.user, data['router'].site_id)
        try:
            with transaction.atomic():
                router = Router.objects.select_for_update().get(pk=data['router'].pk)
                customer = data['customer'] or Customer.objects.create(site=router.site, name=data['name'], contact=data['contact'])
                service = Service.objects.create(customer=customer, router=router, equipment=data['equipment'],
                    ip=data['ip'], location=data['location'], plan=data['plan'])
            messages.success(request, 'Cliente y servicio registrados. Solicita el alta técnica para aplicarlo al simulador.')
            return redirect('service', pk=service.pk)
        except IntegrityError:
            form.add_error('ip', 'Esa IP ya tiene un servicio en el router.')
    return render(request, 'ops/create.html', {'form': form})

@login_required
def service_detail(request, pk):
    service = get_object_or_404(visible(request.user), pk=pk)
    editable = can_edit(request.user, service.router.site_id)
    form = ActionForm(service, request.POST or None)
    if request.method == 'POST':
        require_edit(request.user, service.router.site_id)
        if form.is_valid():
            try:
                if Task.objects.filter(requested_by=request.user, created_at__gte=timezone.now() - timedelta(minutes=1)).count() >= 30:
                    raise ValueError('Límite de solicitudes alcanzado; espera un minuto.')
                data = form.cleaned_data
                request_action(request.user, service.pk, data['action'], data['plan'].pk if data['plan'] else None, data['reason'], data['revision'])
                messages.success(request, 'Solicitud guardada; espera la comprobación del agente simulado.')
                return redirect('service', pk=pk)
            except (ValueError, Plan.DoesNotExist) as exc:
                form.add_error(None, str(exc))
    tasks = Task.objects.filter(service=service).select_related('requested_by').prefetch_related('history', 'events').order_by('-created_at')
    latest = tasks.first()
    return render(request, 'ops/service.html', {'service': service, 'form': form, 'editable': editable,
        'tasks': tasks, 'latest': latest, 'syncing': latest and latest.status in ('pending', 'leased')})

@csrf_exempt
@require_POST
def agent_api(request, endpoint):
    try:
        authorization = request.headers.get('Authorization', '')
        if not authorization.startswith('Bearer '): raise PermissionDenied('Identidad requerida.')
        agent = authenticate(request.headers.get('X-Agent-ID', ''), authorization[7:])
        if request.content_type != 'application/json': raise ValueError('JSON requerido.')
        body = json.loads(request.body)
        if type(body) is not dict: raise ValueError('Objeto JSON requerido.')
        if endpoint == 'claim' and not body:
            return JsonResponse({'task': claim(agent)})
        if endpoint == 'validate' and set(body) == {'task', 'attempt'}:
            task = validate_execution(agent, body['task'], body['attempt'])
            return JsonResponse({'task': task} if task else {'conflict': True}, status=200 if task else 409)
        if endpoint == 'report' and set(body) == {'task', 'attempt', 'report'}:
            result = report(agent, body['task'], body['attempt'], body['report'])
            return JsonResponse({'status': result}, status=409 if result == 'conflict' else 200)
        raise ValueError('Petición fuera de contrato.')
    except PermissionDenied:
        return JsonResponse({'error': 'Identidad o sitio no autorizado.'}, status=403)
    except (ValueError, TypeError, KeyError, ValidationError, Task.DoesNotExist):
        return JsonResponse({'error': 'Petición inválida o fuera de contrato.'}, status=400)
