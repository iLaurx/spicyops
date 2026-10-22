import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q

class Site(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.name

class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    role = models.CharField(max_length=12, choices=[('admin', 'Administrador'), ('operator', 'Operador'), ('viewer', 'Consulta')])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'site'], name='membership_unique')]

class Node(models.Model):
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    def __str__(self): return self.name

class Equipment(models.Model):
    node = models.ForeignKey(Node, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=20, choices=[('ap', 'AP'), ('cpe', 'CPE'), ('infrastructure', 'Infraestructura')])
    upstream = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
    confirmed = models.BooleanField(default=False)
    def __str__(self): return self.name

class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True)

class Router(models.Model):
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    node = models.ForeignKey(Node, on_delete=models.PROTECT)
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=40, default='simulador v1')
    allowed_ips = models.JSONField(default=list)
    simulation = models.BooleanField(default=True)
    def __str__(self): return self.name

class Customer(models.Model):
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    contact = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name

class Plan(models.Model):
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    up_kbps = models.PositiveIntegerField()
    down_kbps = models.PositiveIntegerField()
    commercial_free = models.BooleanField(default=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(up_kbps__gt=0, down_kbps__gt=0, up_kbps__lte=1000000, down_kbps__lte=1000000), name='plan_rates')]
    def __str__(self): return f'{self.name} ({self.up_kbps}/{self.down_kbps} kbps)'

class Service(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    router = models.ForeignKey(Router, on_delete=models.PROTECT)
    equipment = models.ForeignKey(Equipment, null=True, blank=True, on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    ip = models.GenericIPAddressField(protocol='IPv4')
    location = models.CharField(max_length=200)
    desired_enabled = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=0)
    observed = models.JSONField(default=dict)
    observed_at = models.DateTimeField(null=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['router', 'ip'], name='service_unique_target')]

class Task(models.Model):
    STATUS = [('pending', 'Pendiente'), ('leased', 'En proceso'), ('verified', 'Verificada'),
              ('failed', 'Fallida'), ('expired', 'Vencida'), ('obsolete', 'Obsoleta'), ('verification', 'Requiere verificación')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    action = models.CharField(max_length=12, choices=[('provision', 'Alta técnica'), ('suspend', 'Suspensión'), ('resume', 'Reactivación'), ('plan', 'Cambio de plan')])
    snapshot = models.JSONField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    available_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    lease_until = models.DateTimeField(null=True)
    attempt_token = models.UUIDField(null=True)
    result = models.JSONField(default=dict)
    error = models.CharField(max_length=240, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['service', 'revision'], name='task_revision_unique')]
        indexes = [models.Index(fields=['status', 'available_at'])]

class Attempt(models.Model):
    token = models.UUIDField(primary_key=True, default=uuid.uuid4)
    task = models.ForeignKey(Task, related_name='history', on_delete=models.PROTECT)
    number = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    outcome = models.CharField(max_length=32, default='leased', choices=Task.STATUS + [('lease_expired', 'Concesión vencida')])
    report = models.JSONField(default=dict)

class Event(models.Model):
    task = models.ForeignKey(Task, related_name='events', on_delete=models.PROTECT)
    at = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=240)

class LoginWindow(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    start = models.DateTimeField()
