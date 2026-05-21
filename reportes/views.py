from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.choices import (
    EstadoEstancia,
    EstadoFolio,
    EstadoHabitacion,
    EstadoReserva,
)
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA
from api.permissions import HasAnyRole
from estancias.models import CargoEstancia, Estancia
from facturacion.models import Folio
from habitaciones.models import Habitacion, TipoHabitacion
from huespedes.models import Huesped
from reservas.models import Reserva


def _decimal_to_float(value):
    """Convierte Decimals agregados por el ORM a valores simples para JSON."""
    return float(value or Decimal('0.00'))


def _parse_fecha_reporte(fecha_texto):
    """Obtiene una fecha valida desde ?fecha=YYYY-MM-DD o usa la fecha local actual."""
    if not fecha_texto:
        return timezone.localdate(), None

    fecha = parse_date(fecha_texto)
    if fecha is None:
        return None, 'El parametro fecha debe tener formato YYYY-MM-DD.'

    return fecha, None


def calcular_reporte_ocupacion(fecha):
    """
    Centraliza los indicadores operativos del dashboard.
    Se reutiliza en la pantalla HTML y en la API para mantener el mismo criterio.
    """
    estados_reserva_operativos = [
        EstadoReserva.PENDIENTE,
        EstadoReserva.CONFIRMADA,
        EstadoReserva.CHECKIN,
    ]

    habitaciones_por_estado = Habitacion.objects.aggregate(
        total=Count('id'),
        disponibles=Count('id', filter=Q(estado=EstadoHabitacion.DISPONIBLE)),
        ocupadas=Count('id', filter=Q(estado=EstadoHabitacion.OCUPADA)),
        limpieza=Count('id', filter=Q(estado=EstadoHabitacion.LIMPIEZA)),
        mantenimiento=Count('id', filter=Q(estado=EstadoHabitacion.MANTENIMIENTO)),
    )

    total_habitaciones = habitaciones_por_estado['total'] or 0
    habitaciones_ocupadas = habitaciones_por_estado['ocupadas'] or 0
    ocupacion_porcentaje = (
        round((habitaciones_ocupadas / total_habitaciones) * 100, 2)
        if total_habitaciones
        else 0
    )

    reservas_en_fecha = Reserva.objects.filter(
        fecha_entrada__lte=fecha,
        fecha_salida__gt=fecha,
    ).exclude(
        estado__in=[EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA]
    )
    reservas_en_fecha_count = reservas_en_fecha.count()

    reservas_del_dia = Reserva.objects.filter(fecha_entrada=fecha)

    folios_pagados = Folio.objects.filter(
        estado__in=[EstadoFolio.PAGADO, EstadoFolio.CERRADO]
    )

    ingresos_folios = folios_pagados.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    ingresos_reservas_fecha = reservas_del_dia.aggregate(total=Sum('precio_total'))['total'] or Decimal('0.00')
    cargos_totales = CargoEstancia.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    tipos_habitacion = TipoHabitacion.objects.annotate(
        total_habitaciones=Count('habitaciones'),
        disponibles=Count(
            'habitaciones',
            filter=Q(habitaciones__estado=EstadoHabitacion.DISPONIBLE),
        ),
        ocupadas=Count(
            'habitaciones',
            filter=Q(habitaciones__estado=EstadoHabitacion.OCUPADA),
        ),
    ).order_by('nombre')

    proximas_reservas = Reserva.objects.select_related(
        'huesped',
        'habitacion',
    ).filter(
        fecha_entrada__gte=fecha,
        estado__in=estados_reserva_operativos,
    ).order_by('fecha_entrada')[:5]

    return {
        'fecha': fecha,
        'habitaciones': {
            'total': total_habitaciones,
            'disponibles': habitaciones_por_estado['disponibles'] or 0,
            'ocupadas': habitaciones_ocupadas,
            'reservadas_en_fecha': reservas_en_fecha_count,
            'reservadas_u_ocupadas': min(
                total_habitaciones,
                habitaciones_ocupadas + reservas_en_fecha_count,
            ),
            'limpieza': habitaciones_por_estado['limpieza'] or 0,
            'mantenimiento': habitaciones_por_estado['mantenimiento'] or 0,
            'ocupacion_porcentaje': ocupacion_porcentaje,
        },
        'reservas': {
            'total': Reserva.objects.count(),
            'en_fecha': reservas_en_fecha_count,
            'registradas_fecha': reservas_del_dia.count(),
            'pendientes': Reserva.objects.filter(estado=EstadoReserva.PENDIENTE).count(),
            'confirmadas': Reserva.objects.filter(estado=EstadoReserva.CONFIRMADA).count(),
            'checkin': Reserva.objects.filter(estado=EstadoReserva.CHECKIN).count(),
            'finalizadas': Reserva.objects.filter(estado=EstadoReserva.FINALIZADA).count(),
            'canceladas': Reserva.objects.filter(estado=EstadoReserva.CANCELADA).count(),
        },
        'huespedes': {
            'total': Huesped.objects.count(),
        },
        'estancias': {
            'activas': Estancia.objects.filter(estado=EstadoEstancia.ACTIVA).count(),
            'finalizadas': Estancia.objects.filter(estado=EstadoEstancia.FINALIZADA).count(),
        },
        'ingresos': {
            'folios_pagados': _decimal_to_float(ingresos_folios),
            'reservas_fecha': _decimal_to_float(ingresos_reservas_fecha),
            'cargos_totales': _decimal_to_float(cargos_totales),
        },
        'tipos_habitacion': [
            {
                'nombre': tipo.nombre,
                'total': tipo.total_habitaciones,
                'disponibles': tipo.disponibles,
                'ocupadas': tipo.ocupadas,
            }
            for tipo in tipos_habitacion
        ],
        'proximas_reservas': [
            {
                'id': reserva.id,
                'huesped': str(reserva.huesped),
                'habitacion': reserva.habitacion.numero,
                'fecha_entrada': reserva.fecha_entrada,
                'fecha_salida': reserva.fecha_salida,
                'estado': reserva.estado,
                'estado_display': reserva.get_estado_display(),
            }
            for reserva in proximas_reservas
        ],
    }


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA, ROLE_HOUSEKEEPING),
    name='dispatch',
)
class DashboardView(TemplateView):
    """Dashboard operativo renderizado con datos reales del modulo de reportes."""

    template_name = 'pages/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fecha, error = _parse_fecha_reporte(self.request.GET.get('fecha'))

        if error:
            fecha = timezone.localdate()
            context['fecha_error'] = error

        context['reporte'] = calcular_reporte_ocupacion(fecha)
        return context


class ReporteOcupacionAPIView(APIView):
    """
    API del dashboard operativo.
    Devuelve ocupacion y otros indicadores principales para la fecha consultada.
    """

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA, ROLE_HOUSEKEEPING]

    def get(self, request):
        fecha, error = _parse_fecha_reporte(request.query_params.get('fecha'))

        if error:
            return Response(
                {
                    'error': True,
                    'message': error,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = calcular_reporte_ocupacion(fecha)
        data['fecha'] = fecha.isoformat()

        for reserva in data['proximas_reservas']:
            reserva['fecha_entrada'] = reserva['fecha_entrada'].isoformat()
            reserva['fecha_salida'] = reserva['fecha_salida'].isoformat()

        return Response(data)
