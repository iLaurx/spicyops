from datetime import datetime
from django import template
from django.utils import timezone
register = template.Library()

@register.filter
def gb(value): return '—' if value in (None,'') else f'{value/1e9:,.2f}'
@register.filter
def mbps(value): return 'Sin límite' if value == 0 else f'{value:g}' if value is not None else '—'
@register.filter
def mbs(value): return 'Sin límite' if value == 0 else f'{value/8:g}' if value is not None else '—'
@register.filter
def elapsed(value):
    if value in (None,''): return '—'
    minutes = int(value/60)
    if minutes < 60: return f'{minutes} min'
    hours, minute = divmod(minutes,60)
    return f'{hours//24} d {hours%24} h' if hours >= 24 else f'{hours} h {minute} min'
@register.filter
def at(value):
    if not value: return 'Sin lectura'
    return timezone.localtime(datetime.fromtimestamp(value, timezone.get_current_timezone())).strftime('%d/%m · %H:%M:%S')
@register.filter
def clock(value):
    return timezone.localtime(datetime.fromtimestamp(value, timezone.get_current_timezone())).strftime('%H:%M')
@register.filter
def initial(value): return str(value or '?')[0].upper()

@register.filter
def chart_datetime(value):
    return datetime.fromtimestamp(value, timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M')

@register.filter
def diagnostic_datetime(value):
    if not value: return '—'
    return datetime.fromtimestamp(value, timezone.get_current_timezone()).strftime('%d/%m/%Y · %H:%M:%S')
