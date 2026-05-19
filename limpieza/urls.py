from django.urls import path

from . import views

app_name = 'limpieza'

urlpatterns = [
    path('', views.panel_limpieza, name='panel_limpieza'),
    path('<int:habitacion_id>/disponible/', views.marcar_habitacion_disponible, name='marcar_habitacion_disponible'),
    path('<int:habitacion_id>/mantenimiento/', views.marcar_habitacion_mantenimiento, name='marcar_habitacion_mantenimiento'),
]
