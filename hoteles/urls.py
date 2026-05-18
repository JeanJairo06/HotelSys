from django.urls import path

from . import views

app_name = 'hoteles'

urlpatterns = [
    path('', views.listar_hoteles, name='listar_hoteles'),
    path('crear/', views.crear_hotel, name='crear_hotel'),
    path('<int:pk>/editar/', views.editar_hotel, name='editar_hotel'),
]
