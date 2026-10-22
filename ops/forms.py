from django import forms
from agent.contract import validate_target
from .models import Customer, Equipment, Membership, Plan, Router

class ServiceForm(forms.Form):
    customer = forms.ModelChoiceField(label='Cliente existente (opcional)', queryset=Customer.objects.none(), required=False)
    name = forms.CharField(label='Nombre del nuevo cliente', max_length=120, required=False)
    contact = forms.CharField(label='Contacto', max_length=160, required=False)
    router = forms.ModelChoiceField(label='Router simulado / sitio', queryset=Router.objects.none())
    equipment = forms.ModelChoiceField(label='CPE o AP asociado', queryset=Equipment.objects.none(), required=False)
    ip = forms.GenericIPAddressField(label='IP ficticia aprobada', protocol='IPv4', help_text='Demo: 198.51.100.20 a 198.51.100.29')
    location = forms.CharField(label='Ubicación del servicio', max_length=200)
    plan = forms.ModelChoiceField(label='Plan inicial', queryset=Plan.objects.none())

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sites = Membership.objects.filter(user=user, role__in=['admin', 'operator']).values('site_id')
        self.fields['customer'].queryset = Customer.objects.filter(site_id__in=sites)
        self.fields['router'].queryset = Router.objects.filter(site_id__in=sites, simulation=True)
        self.fields['equipment'].queryset = Equipment.objects.filter(node__site_id__in=sites, kind__in=['ap', 'cpe'])
        self.fields['plan'].queryset = Plan.objects.filter(site_id__in=sites)

    def clean(self):
        data = super().clean()
        router, plan = data.get('router'), data.get('plan')
        if not data.get('customer') and not data.get('name'):
            self.add_error('name', 'Escribe un nombre o selecciona un cliente existente.')
        if router:
            if plan and plan.site_id != router.site_id:
                self.add_error('plan', 'El plan debe pertenecer al mismo sitio.')
            if data.get('customer') and data['customer'].site_id != router.site_id:
                self.add_error('customer', 'El cliente pertenece a otro sitio.')
            if data.get('equipment') and data['equipment'].node.site_id != router.site_id:
                self.add_error('equipment', 'El equipo pertenece a otro sitio.')
            if data.get('ip'):
                try: validate_target(data['ip'], router.allowed_ips)
                except ValueError as exc: self.add_error('ip', str(exc))
        return data

class ActionForm(forms.Form):
    action = forms.ChoiceField(label='Acción', choices=[('provision', 'Alta técnica'), ('suspend', 'Suspender'), ('resume', 'Reactivar'), ('plan', 'Cambiar plan')])
    plan = forms.ModelChoiceField(label='Plan para cambio de velocidad', required=False, queryset=Plan.objects.none())
    reason = forms.CharField(label='Motivo', max_length=240)
    revision = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].queryset = Plan.objects.filter(site_id=service.router.site_id)
        self.initial['revision'] = service.revision

    def clean(self):
        data = super().clean()
        if data.get('action') == 'plan' and not data.get('plan'):
            self.add_error('plan', 'Selecciona el nuevo plan.')
        return data
