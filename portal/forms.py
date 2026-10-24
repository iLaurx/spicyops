from django import forms
import re

class ConnectionForm(forms.Form):
    name = forms.CharField(label='Nombre de la localidad', max_length=100, widget=forms.TextInput(attrs={'placeholder':'Nombre de tu localidad'}))
    host = forms.CharField(label='Dirección de la Raspberry', max_length=253, widget=forms.TextInput(attrs={'placeholder':'IP o nombre de Tailscale', 'autocomplete':'off'}))
    port = forms.IntegerField(label='Puerto SSH', min_value=1, max_value=65535, initial=22)
    ssh_user = forms.CharField(label='Usuario de Raspberry', max_length=80, widget=forms.TextInput(attrs={'autocomplete':'off'}))
    ssh_method = forms.ChoiceField(label='Autenticación SSH', choices=[('password','Contraseña'),('key','Clave SSH de Windows')], initial='password')
    ssh_password = forms.CharField(label='Contraseña o frase de clave', max_length=256, required=False, strip=False, widget=forms.PasswordInput(attrs={'autocomplete':'new-password'}))
    key_file = forms.CharField(label='Archivo de clave privada en Windows', max_length=500, required=False, help_text='Opcional: vacío para usar tu agente SSH o claves habituales.')
    router_host = forms.GenericIPAddressField(label='IP del MikroTik', protocol='IPv4', required=False, help_text='Vacío: se usa la puerta de enlace de la Raspberry.')
    router_user = forms.CharField(label='Usuario API del MikroTik', max_length=80)
    router_password = forms.CharField(label='Contraseña API del MikroTik', max_length=256, strip=False, widget=forms.PasswordInput(attrs={'autocomplete':'new-password'}))
    ca_file = forms.CharField(label='Certificado CA en Raspberry', max_length=300, widget=forms.TextInput(attrs={'placeholder': '/ruta/al/certificado-ca.crt'}))
    python_path = forms.CharField(label='Python con librouteros en Raspberry', max_length=300, initial='/usr/bin/python3', help_text='Ejecutable de Python que ya tiene librouteros en Raspberry.')
    fingerprint = forms.CharField(label='Huella SSH confirmada', max_length=100, required=False, widget=forms.HiddenInput)
    def clean_host(self):
        host = self.cleaned_data['host'].strip()
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:-]{0,252}', host):
            raise forms.ValidationError('Escribe solo una IP o nombre de equipo, sin URL ni comandos.')
        return host
    def clean_fingerprint(self):
        value = self.cleaned_data['fingerprint']
        if value and not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}', value): raise forms.ValidationError('Huella SSH inválida.')
        return value
    def clean(self):
        data = super().clean()
        if data.get('ssh_method') == 'password' and not data.get('ssh_password'):
            self.add_error('ssh_password', 'Escribe la contraseña de esta Raspberry.')
        for key in ('python_path', 'ca_file'):
            if key in data and (any(c in data[key] for c in ('\n', '\r', '\x00')) or not data[key].startswith(('/', '~/'))):
                self.add_error(key, 'Indica una ruta absoluta o que empiece por ~/.')
        return data
