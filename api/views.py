from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.permissions import IsAdminRole
from api.serializers import EmpleadoAutocompleteSerializer
from api.throttles import AutocompleteRateThrottle
from config.choices import EstadoGeneral
from empleados.models import Empleado


@extend_schema_view(
    get=extend_schema(
        tags=['Empleados'],
        summary='Lista empleados activos disponibles para crear usuarios',
        description='Endpoint paginado y filtrable para autocompletados como Tom Select.',
    )
)
class EmpleadosDisponiblesUsuarioAPIView(generics.ListAPIView):
    serializer_class = EmpleadoAutocompleteSerializer
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [AutocompleteRateThrottle]
    throttle_scope = 'autocomplete'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo', 'nombres', 'apellidos', 'email']
    ordering_fields = ['codigo', 'apellidos', 'nombres']
    ordering = ['apellidos', 'nombres']

    def get_queryset(self):
        queryset = Empleado.objects.filter(
            estado=EstadoGeneral.ACTIVO,
            cuenta_usuario__isnull=True,
        )
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search)
                | Q(nombres__icontains=search)
                | Q(apellidos__icontains=search)
                | Q(email__icontains=search)
            )
        return queryset
