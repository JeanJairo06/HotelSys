from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.auth import HotelSysTokenObtainPairView
from api.views import EmpleadosDisponiblesUsuarioAPIView

app_name = 'api'

urlpatterns = [
    path('auth/token/', HotelSysTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(
        'empleados/disponibles-para-usuario/',
        EmpleadosDisponiblesUsuarioAPIView.as_view(),
        name='empleados_disponibles_usuario',
    ),
]
