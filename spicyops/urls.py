from django.contrib.auth.views import LogoutView
from django.urls import path
from ops import views

urlpatterns = [path('', views.dashboard, name='dashboard'), path('login/', views.LimitedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), path('inventory/', views.inventory, name='inventory'),
    path('services/new/', views.create_service, name='create'), path('services/<int:pk>/', views.service_detail, name='service'),
    path('api/agent/<str:endpoint>/', views.agent_api)]
