from django.urls import path
from . import views
from .auth import open_panel

urlpatterns = [path('',views.analytics,name='analytics'), path('clientes/',views.clients,name='clients'),
    path('conexiones/',views.connections,name='connections'), path('conexiones/nueva/',views.connect,name='connect'),
    path('conexiones/<str:profile_id>/configurar/',views.connect,name='configure'),
    path('conexiones/<str:profile_id>/leer/',views.refresh,name='refresh'),
    path('conexiones/<str:profile_id>/diagnosticar/',views.diagnose,name='diagnose'),
    path('conexiones/<str:profile_id>/diagnostico/',views.diagnostic_status,name='diagnostic_status'),
    path('conexiones/<str:profile_id>/automatica/',views.automatic,name='automatic'),
    path('conexiones/<str:profile_id>/desconectar/',views.disconnect,name='disconnect'),
    path('clientes/<str:profile_id>/<str:client_id>/datos/',views.edit_client,name='edit_client'),
    path('clientes/<str:profile_id>/<str:client_id>/morosidad/',views.morosity,name='morosity'),
    path('open/<str:token>/',open_panel)]
