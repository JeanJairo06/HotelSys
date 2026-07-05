from django.urls import path

from core.consumers import HabitacionesPlanoConsumer


websocket_urlpatterns = [
    path('ws/hoteles/<int:hotel_id>/habitaciones/', HabitacionesPlanoConsumer.as_asgi()),
]
