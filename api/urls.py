from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.auth import HotelSysTokenObtainPairView
from api.views import (
    EmpleadosDisponiblesUsuarioAPIView,
    EstanciaDetailAPIView,
    HabitacionHousekeepingAPIView,
    HabitacionesDisponiblesAPIView,
    RealizarCheckinAPIView,
    RealizarCheckoutAPIView,
)

app_name = 'api'

urlpatterns = [
    path('auth/token/', HotelSysTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(
        'empleados/disponibles-para-usuario/',
        EmpleadosDisponiblesUsuarioAPIView.as_view(),
        name='empleados_disponibles_usuario',
    ),
    path(
        'reservas/huespedes-autocomplete/',
        HuespedesReservaAutocompleteAPIView.as_view(),
        name='reservas_huespedes_autocomplete',
    ),
    path(
        'reservas/habitaciones-disponibles/',
        HabitacionesDisponiblesReservaAutocompleteAPIView.as_view(),
        name='reservas_habitaciones_disponibles',
    ),

    # Endpoints del modulo Habitaciones y Estancias.
    path('habitaciones/disponibles/', HabitacionesDisponiblesAPIView.as_view(), name='habitaciones_disponibles'),
    path('reservas/<int:reserva_id>/checkin/', RealizarCheckinAPIView.as_view(), name='realizar_checkin'),
    path('estancias/<int:pk>/', EstanciaDetailAPIView.as_view(), name='estancias_detail'),
    path('estancias/<int:estancia_id>/checkout/', RealizarCheckoutAPIView.as_view(), name='realizar_checkout'),
    path('habitaciones/<int:habitacion_id>/housekeeping/', HabitacionHousekeepingAPIView.as_view(), name='habitacion_housekeeping'),
]
