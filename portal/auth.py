from functools import wraps
import hashlib
import hmac
from django.conf import settings
from django.core import signing
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

def identity():
    return hmac.new(settings.SECRET_KEY.encode(), b'spicyops-desktop-session-v1', hashlib.sha256).hexdigest()

def protected(view):
    @wraps(view)
    def inner(request, *args, **kwargs):
        if request.META.get('REMOTE_ADDR') not in ('127.0.0.1', '::1'):
            return HttpResponseForbidden('SpicyOps para Windows acepta solo su interfaz local.')
        if request.session.get('desktop') != identity():
            return render(request, 'portal/locked.html', status=401)
        response=view(request, *args, **kwargs)
        response['Cache-Control']='no-store'
        response['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
        return response
    return inner

def open_panel(request, token):
    if request.META.get('REMOTE_ADDR') not in ('127.0.0.1', '::1'):
        return HttpResponseForbidden()
    try:
        payload = signing.loads(token, salt='spicyops-desktop-open', max_age=120)
        if payload != 'open': raise signing.BadSignature()
    except signing.BadSignature:
        return render(request, 'portal/locked.html', status=401)
    request.session.cycle_key()
    request.session['desktop'] = identity()
    response = redirect('analytics')
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response
