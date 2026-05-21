from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.auth import HotelSysTokenObtainPairView
from api.views import (
    EmpleadosDisponiblesUsuarioAPIView,
    EstanciaDetailAPIView,
    EstanciaListAPIView,
    HabitacionCambiarEstadoAPIView,
    HabitacionDetailAPIView,
    HabitacionesDisponiblesReservaAutocompleteAPIView,
    HabitacionListCreateAPIView,
    HuespedesReservaAutocompleteAPIView,
    LimpiezaMarcarDisponibleAPIView,
    LimpiezaMarcarMantenimientoAPIView,
    LimpiezaPanelAPIView,
    RealizarCheckinAPIView,
    RealizarCheckoutAPIView,
    ReservasCheckinListAPIView,
    TipoHabitacionDetailAPIView,
    TipoHabitacionListCreateAPIView,
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
    path('habitaciones/tipos/', TipoHabitacionListCreateAPIView.as_view(), name='tipos_habitacion_list_create'),
    path('habitaciones/tipos/<int:pk>/', TipoHabitacionDetailAPIView.as_view(), name='tipos_habitacion_detail'),
    path('habitaciones/', HabitacionListCreateAPIView.as_view(), name='habitaciones_list_create'),
    path('habitaciones/<int:pk>/', HabitacionDetailAPIView.as_view(), name='habitaciones_detail'),
    path('habitaciones/<int:pk>/estado/', HabitacionCambiarEstadoAPIView.as_view(), name='habitaciones_cambiar_estado'),
    path('estancias/', EstanciaListAPIView.as_view(), name='estancias_list'),
    path('estancias/<int:pk>/', EstanciaDetailAPIView.as_view(), name='estancias_detail'),
    path('estancias/checkin/', ReservasCheckinListAPIView.as_view(), name='reservas_checkin_list'),
    path('estancias/checkin/<int:reserva_id>/', RealizarCheckinAPIView.as_view(), name='realizar_checkin'),
    path('estancias/<int:estancia_id>/checkout/', RealizarCheckoutAPIView.as_view(), name='realizar_checkout'),
    path('limpieza/', LimpiezaPanelAPIView.as_view(), name='limpieza_panel'),
    path(
        'limpieza/<int:habitacion_id>/disponible/',
        LimpiezaMarcarDisponibleAPIView.as_view(),
        name='limpieza_marcar_disponible',
    ),
    path(
        'limpieza/<int:habitacion_id>/mantenimiento/',
        LimpiezaMarcarMantenimientoAPIView.as_view(),
        name='limpieza_marcar_mantenimiento',
    ),
]
