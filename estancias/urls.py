from django.urls import path

from . import views

app_name = 'estancias'

urlpatterns = [
    path('', views.listar_estancias, name='listar_estancias'),
    path('checkin/', views.listar_reservas_checkin, name='listar_reservas_checkin'),
    path('checkin/<int:reserva_id>/', views.realizar_checkin, name='realizar_checkin'),
    path('<int:estancia_id>/', views.detalle_estancia, name='detalle_estancia'),
    path('<int:estancia_id>/checkout/', views.realizar_checkout, name='realizar_checkout'),
]
