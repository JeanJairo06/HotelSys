"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from config.views import DashboardView, home
from cuentas.views import CuentaLoginView, CuentaLogoutView

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('login/', CuentaLoginView.as_view(), name='login'),
    path('logout/', CuentaLogoutView.as_view(), name='logout'),
    path('usuarios/', include('cuentas.urls')),
    path('empleados/', include('empleados.urls')),
    path('huespedes/', include('huespedes.urls')),
    path('api/v1/', include('api.urls')),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
]

handler403 = 'config.views.error_403'
handler404 = 'config.views.error_404'
handler500 = 'config.views.error_500'
