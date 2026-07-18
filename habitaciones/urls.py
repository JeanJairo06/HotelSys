from django.urls import path

from . import views

app_name = 'habitaciones'

urlpatterns = [
    path('', views.listar_habitaciones, name='listar_habitaciones'),
    path('estado-json/', views.estado_habitaciones_json, name='estado_habitaciones_json'),
    path('crear/', views.crear_habitacion, name='crear_habitacion'),
    path('<int:pk>/editar/', views.editar_habitacion, name='editar_habitacion'),
    path('<int:pk>/estado/', views.cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    path('tipos/', views.listar_tipos_habitacion, name='listar_tipos_habitacion'),
    path('tipos/crear/', views.crear_tipo_habitacion, name='crear_tipo_habitacion'),
    path('tipos/<int:pk>/editar/', views.editar_tipo_habitacion, name='editar_tipo_habitacion'),
]
