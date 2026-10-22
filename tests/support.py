import secrets
from django.contrib.auth import get_user_model
from ops.models import Agent, Customer, Equipment, Membership, Node, Plan, Router, Service, Site
from ops.queue import token_digest

def fixture(suffix='a'):
    site = Site.objects.create(name='Sitio ficticio ' + suffix)
    node = Node.objects.create(site=site, name='Nodo ' + suffix, location='Laboratorio')
    equipment = Equipment.objects.create(node=node, name='CPE ' + suffix, kind='cpe')
    token = secrets.token_urlsafe(32)
    agent = Agent.objects.create(site=site, name='Agente ' + suffix, token_hash=token_digest(token))
    router = Router.objects.create(site=site, node=node, agent=agent, name='Router ' + suffix,
        allowed_ips=['198.51.100.20', '198.51.100.21', '198.51.100.22'])
    plan = Plan.objects.create(site=site, name='Base', up_kbps=2000, down_kbps=4000)
    faster = Plan.objects.create(site=site, name='Más', up_kbps=5000, down_kbps=10000)
    customer = Customer.objects.create(site=site, name='Cliente ' + suffix)
    service = Service.objects.create(customer=customer, router=router, equipment=equipment,
        plan=plan, ip='198.51.100.20', location='Casa ficticia')
    user = get_user_model().objects.create_user('operador_' + suffix, password=secrets.token_urlsafe(16))
    Membership.objects.create(site=site, user=user, role='operator')
    return locals()
