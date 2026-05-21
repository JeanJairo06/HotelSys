from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import filters, generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.permissions import HasAnyRole, IsAdminRole
from api.serializers import (
    EmpleadoAutocompleteSerializer,
    EstanciaSerializer,
    HabitacionEstadoSerializer,
    HabitacionReservaAutocompleteSerializer,
    HabitacionSerializer,
    HuespedAutocompleteSerializer,
    ReservaCheckinSerializer,
    TipoHabitacionSerializer,
)
from api.throttles import AutocompleteRateThrottle, UserApiRateThrottle, WriteRateThrottle
from config.choices import EstadoGeneral, EstadoHabitacion, EstadoReserva
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA
from empleados.models import Empleado
from estancias.models import Estancia
from estancias.services import registrar_checkin, registrar_checkout
from habitaciones.models import Habitacion, TipoHabitacion
from huespedes.models import Huesped
from habitaciones.services import cambiar_estado_manual
from limpieza.services import marcar_disponible, marcar_mantenimiento
from reservas.models import Reserva


API_AUTHENTICATION_CLASSES = [SessionAuthentication, JWTAuthentication]


class ApiThrottleMixin:
    def get_throttles(self):
        throttle_classes = [UserApiRateThrottle]
        if self.request.method not in SAFE_METHODS:
            throttle_classes.append(WriteRateThrottle)
        return [throttle() for throttle in throttle_classes]


def _validation_error_response(error):
    if hasattr(error, 'message_dict'):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': error.messages}, status=status.HTTP_400_BAD_REQUEST)


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


@extend_schema_view(
    get=extend_schema(
        tags=['Reservas'],
        summary='Lista huespedes disponibles para reservas',
        description='Endpoint paginado para autocompletado lazy loading de huespedes.',
    )
)
class HuespedesReservaAutocompleteAPIView(generics.ListAPIView):
    serializer_class = HuespedAutocompleteSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    throttle_classes = [AutocompleteRateThrottle]
    throttle_scope = 'autocomplete'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['num_doc', 'nombres', 'apellidos', 'email', 'telefono']
    ordering_fields = ['apellidos', 'nombres', 'num_doc']
    ordering = ['apellidos', 'nombres']

    def get_queryset(self):
        queryset = Huesped.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(num_doc__icontains=search)
                | Q(nombres__icontains=search)
                | Q(apellidos__icontains=search)
                | Q(email__icontains=search)
                | Q(telefono__icontains=search)
            )
        return queryset


@extend_schema_view(
    get=extend_schema(
        tags=['Reservas'],
        summary='Lista habitaciones disponibles para reservas',
        description='Endpoint paginado para autocompletado lazy loading de habitaciones segun hotel, tipo y fechas.',
    )
)
class HabitacionesDisponiblesReservaAutocompleteAPIView(generics.ListAPIView):
    serializer_class = HabitacionReservaAutocompleteSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    throttle_classes = [AutocompleteRateThrottle]
    throttle_scope = 'autocomplete'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'hotel__nombre', 'tipo__nombre']
    ordering_fields = ['hotel__nombre', 'piso', 'numero']
    ordering = ['hotel__nombre', 'piso', 'numero']

    def get_queryset(self):
        queryset = Habitacion.objects.select_related('hotel', 'tipo')
        hotel = self.request.query_params.get('hotel')
        tipo = self.request.query_params.get('tipo')
        fecha_entrada = parse_date(self.request.query_params.get('fecha_entrada') or '')
        fecha_salida = parse_date(self.request.query_params.get('fecha_salida') or '')
        reserva_id = self.request.query_params.get('reserva_id')
        search = self.request.query_params.get('search')

        if hotel and hotel.isdigit():
            queryset = queryset.filter(hotel_id=hotel)

        if tipo and tipo.isdigit():
            queryset = queryset.filter(tipo_id=tipo)

        if fecha_entrada and fecha_salida and fecha_salida > fecha_entrada:
            reservas_ocupadas = Reserva.objects.filter(
                fecha_entrada__lt=fecha_salida,
                fecha_salida__gt=fecha_entrada,
            ).exclude(
                estado__in=[EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA],
            )
            if reserva_id and reserva_id.isdigit():
                reservas_ocupadas = reservas_ocupadas.exclude(pk=reserva_id)
            queryset = queryset.exclude(pk__in=reservas_ocupadas.values('habitacion_id'))

        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search)
                | Q(hotel__nombre__icontains=search)
                | Q(tipo__nombre__icontains=search)
            )

        return queryset


# API del modulo Habitaciones y Estancias.
@extend_schema_view(
    get=extend_schema(tags=['Habitaciones'], summary='Lista tipos de habitacion'),
    post=extend_schema(tags=['Habitaciones'], summary='Crea tipo de habitacion'),
)
class TipoHabitacionListCreateAPIView(ApiThrottleMixin, generics.ListCreateAPIView):
    serializer_class = TipoHabitacionSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'capacidad', 'precio_base']
    ordering = ['nombre']

    def get_queryset(self):
        return TipoHabitacion.objects.all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminRole()]
        return super().get_permissions()


@extend_schema_view(
    get=extend_schema(tags=['Habitaciones'], summary='Detalle tipo de habitacion'),
    put=extend_schema(tags=['Habitaciones'], summary='Actualiza tipo de habitacion'),
    patch=extend_schema(tags=['Habitaciones'], summary='Actualiza parcialmente tipo de habitacion'),
)
class TipoHabitacionDetailAPIView(ApiThrottleMixin, generics.RetrieveUpdateAPIView):
    serializer_class = TipoHabitacionSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        return TipoHabitacion.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=['Habitaciones'],
        summary='Lista habitaciones',
        description='Permite filtrar por hotel, tipo, estado y piso.',
    ),
    post=extend_schema(tags=['Habitaciones'], summary='Crea habitacion'),
)
class HabitacionListCreateAPIView(ApiThrottleMixin, generics.ListCreateAPIView):
    serializer_class = HabitacionSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hotel', 'tipo', 'estado', 'piso']
    search_fields = ['numero', 'hotel__nombre', 'tipo__nombre']
    ordering_fields = ['hotel__nombre', 'piso', 'numero', 'estado']
    ordering = ['hotel__nombre', 'piso', 'numero']

    def get_queryset(self):
        return Habitacion.objects.select_related('hotel', 'tipo')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminRole()]
        return super().get_permissions()


@extend_schema_view(
    get=extend_schema(tags=['Habitaciones'], summary='Detalle habitacion'),
    put=extend_schema(tags=['Habitaciones'], summary='Actualiza habitacion'),
    patch=extend_schema(tags=['Habitaciones'], summary='Actualiza parcialmente habitacion'),
)
class HabitacionDetailAPIView(ApiThrottleMixin, generics.RetrieveUpdateAPIView):
    serializer_class = HabitacionSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        return Habitacion.objects.select_related('hotel', 'tipo')


@extend_schema(
    tags=['Habitaciones'],
    summary='Cambia estado de habitacion',
    request=HabitacionEstadoSerializer,
    responses={200: HabitacionSerializer, 400: OpenApiResponse(description='Cambio de estado no permitido')},
)
class HabitacionCambiarEstadoAPIView(APIView):
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    throttle_classes = [WriteRateThrottle]
    throttle_scope = 'write'
    serializer_class = HabitacionSerializer

    def post(self, request, pk):
        habitacion = get_object_or_404(Habitacion.objects.select_related('hotel', 'tipo'), pk=pk)
        serializer = HabitacionEstadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            habitacion = cambiar_estado_manual(habitacion, serializer.validated_data['estado'])
        except DjangoValidationError as error:
            return _validation_error_response(error)
        return Response(HabitacionSerializer(habitacion).data)


@extend_schema_view(
    get=extend_schema(
        tags=['Estancias'],
        summary='Lista estancias',
        description='Lista estancias con filtro por estado.',
    )
)
class EstanciaListAPIView(generics.ListAPIView):
    serializer_class = EstanciaSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'habitacion', 'reserva']
    search_fields = ['reserva__huesped__nombres', 'reserva__huesped__apellidos', 'habitacion__numero']
    ordering_fields = ['fecha_checkin', 'fecha_checkout', 'estado']
    ordering = ['-fecha_checkin']

    def get_queryset(self):
        return Estancia.objects.select_related('reserva', 'reserva__huesped', 'habitacion', 'habitacion__hotel')


@extend_schema_view(
    get=extend_schema(tags=['Estancias'], summary='Detalle estancia')
)
class EstanciaDetailAPIView(generics.RetrieveAPIView):
    serializer_class = EstanciaSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]

    def get_queryset(self):
        return Estancia.objects.select_related('reserva', 'reserva__huesped', 'habitacion', 'habitacion__hotel')


@extend_schema_view(
    get=extend_schema(tags=['Estancias'], summary='Lista reservas disponibles para check-in')
)
class ReservasCheckinListAPIView(generics.ListAPIView):
    serializer_class = ReservaCheckinSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['huesped__nombres', 'huesped__apellidos', 'habitacion__numero', 'hotel__nombre']
    ordering_fields = ['fecha_entrada', 'fecha_salida']
    ordering = ['fecha_entrada']

    def get_queryset(self):
        return Reserva.objects.select_related('hotel', 'huesped', 'habitacion').filter(
            estado=EstadoReserva.CONFIRMADA,
        )


@extend_schema(
    tags=['Estancias'],
    summary='Realiza check-in',
    responses={201: EstanciaSerializer, 400: OpenApiResponse(description='Check-in no permitido')},
)
class RealizarCheckinAPIView(APIView):
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    throttle_classes = [WriteRateThrottle]
    throttle_scope = 'write'
    serializer_class = EstanciaSerializer

    def post(self, request, reserva_id):
        reserva = get_object_or_404(
            Reserva.objects.select_related('hotel', 'huesped', 'habitacion'),
            pk=reserva_id,
        )
        try:
            estancia = registrar_checkin(reserva)
        except DjangoValidationError as error:
            return _validation_error_response(error)
        return Response(EstanciaSerializer(estancia).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Estancias'],
    summary='Realiza checkout',
    responses={200: EstanciaSerializer, 400: OpenApiResponse(description='Checkout no permitido')},
)
class RealizarCheckoutAPIView(APIView):
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
    throttle_classes = [WriteRateThrottle]
    throttle_scope = 'write'
    serializer_class = EstanciaSerializer

    def post(self, request, estancia_id):
        estancia = get_object_or_404(
            Estancia.objects.select_related('reserva', 'reserva__huesped', 'habitacion'),
            pk=estancia_id,
        )
        try:
            estancia = registrar_checkout(estancia)
        except DjangoValidationError as error:
            return _validation_error_response(error)
        return Response(EstanciaSerializer(estancia).data)


@extend_schema_view(
    get=extend_schema(
        tags=['Habitaciones'],
        summary='Lista habitaciones pendientes de limpieza o mantenimiento',
    )
)
class LimpiezaPanelAPIView(generics.ListAPIView):
    serializer_class = HabitacionSerializer
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_HOUSEKEEPING]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['piso', 'estado']
    ordering_fields = ['piso', 'numero', 'estado']
    ordering = ['piso', 'numero']

    def get_queryset(self):
        return Habitacion.objects.select_related('hotel', 'tipo').filter(
            estado__in=[EstadoHabitacion.LIMPIEZA, EstadoHabitacion.MANTENIMIENTO],
        )


@extend_schema(
    tags=['Habitaciones'],
    summary='Marca habitacion como disponible desde limpieza',
    responses={200: HabitacionSerializer, 400: OpenApiResponse(description='Cambio no permitido')},
)
class LimpiezaMarcarDisponibleAPIView(APIView):
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_HOUSEKEEPING]
    throttle_classes = [WriteRateThrottle]
    throttle_scope = 'write'
    serializer_class = HabitacionSerializer

    def post(self, request, habitacion_id):
        habitacion = get_object_or_404(Habitacion.objects.select_related('hotel', 'tipo'), pk=habitacion_id)
        try:
            habitacion = marcar_disponible(habitacion)
        except DjangoValidationError as error:
            return _validation_error_response(error)
        return Response(HabitacionSerializer(habitacion).data)


@extend_schema(
    tags=['Habitaciones'],
    summary='Envia habitacion a mantenimiento desde limpieza',
    responses={200: HabitacionSerializer, 400: OpenApiResponse(description='Cambio no permitido')},
)
class LimpiezaMarcarMantenimientoAPIView(APIView):
    authentication_classes = API_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_HOUSEKEEPING]
    throttle_classes = [WriteRateThrottle]
    throttle_scope = 'write'
    serializer_class = HabitacionSerializer

    def post(self, request, habitacion_id):
        habitacion = get_object_or_404(Habitacion.objects.select_related('hotel', 'tipo'), pk=habitacion_id)
        try:
            habitacion = marcar_mantenimiento(habitacion)
        except DjangoValidationError as error:
            return _validation_error_response(error)
        return Response(HabitacionSerializer(habitacion).data)
