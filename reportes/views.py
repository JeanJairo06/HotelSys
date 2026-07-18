from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views import View
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
    OrigenReserva,
    TipoCargo,
)
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA
from api.permissions import HasAnyRole
from estancias.models import CargoEstancia, Estancia
from facturacion.models import Factura, Folio
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reportes.services import DashboardService
from reservas.models import Reserva


logger = logging.getLogger(__name__)

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


def _safe_percentage(value, total):
    """Calcula porcentajes evitando divisiones por cero en reportes visuales."""
    return round((value / total) * 100, 2) if total else 0


def _date_range(desde, hasta):
    """Genera fechas inclusivas para tendencias diarias dentro del rango consultado."""
    fecha = desde
    while fecha <= hasta:
        yield fecha
        fecha += timedelta(days=1)


def _parse_rango_reportes(desde_texto, hasta_texto):
    """
    Obtiene el rango de fechas para reportes analiticos.
    Si no se envia rango, se consulta por defecto los ultimos 30 dias.
    """
    hoy = timezone.localdate()
    desde = parse_date(desde_texto) if desde_texto else hoy - timedelta(days=29)
    hasta = parse_date(hasta_texto) if hasta_texto else hoy

    if desde is None or hasta is None:
        return None, None, 'Las fechas deben tener formato YYYY-MM-DD.'

    if desde > hasta:
        return None, None, 'La fecha inicial no puede ser mayor que la fecha final.'

    return desde, hasta, None


def _build_distribution(queryset, field_name, choices):
    """Normaliza conteos por choices para que la plantilla siempre reciba todos los estados."""
    conteos = dict(
        queryset.values(field_name)
        .annotate(total=Count('id'))
        .values_list(field_name, 'total')
    )
    total = sum(conteos.values())

    return [
        {
            'codigo': codigo,
            'nombre': nombre,
            'total': conteos.get(codigo, 0),
            'porcentaje': _safe_percentage(conteos.get(codigo, 0), total),
        }
        for codigo, nombre in choices
    ]


def _group_reservas_by_periodo(reservas):
    """Agrupa reservas por dia, semana ISO y mes usando fecha de entrada."""
    diario = defaultdict(int)
    semanal = defaultdict(int)
    mensual = defaultdict(int)

    for reserva in reservas:
        fecha = reserva.fecha_entrada
        diario[fecha] += 1
        semanal[f'{fecha.isocalendar().year}-S{fecha.isocalendar().week:02d}'] += 1
        mensual[fecha.strftime('%Y-%m')] += 1

    return {
        'diario': [{'fecha': fecha, 'total': total} for fecha, total in sorted(diario.items())],
        'semanal': [{'periodo': periodo, 'total': total} for periodo, total in sorted(semanal.items())],
        'mensual': [{'periodo': periodo, 'total': total} for periodo, total in sorted(mensual.items())],
    }


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
    estancias_en_fecha = Estancia.objects.filter(
        fecha_checkin__date__lte=fecha,
    ).filter(
        Q(fecha_checkout__date__gt=fecha) | Q(fecha_checkout__isnull=True),
    ).exclude(
        estado=EstadoEstancia.CANCELADA,
    )
    habitaciones_ocupadas = estancias_en_fecha.values('habitacion_id').distinct().count()
    ocupadas_por_tipo = dict(
        estancias_en_fecha.values('habitacion__tipo_id').annotate(
            total=Count('habitacion_id', distinct=True),
        ).values_list('habitacion__tipo_id', 'total')
    )
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
    ).order_by('nombre')

    proximas_reservas = Reserva.objects.select_related(
        'huesped',
        'habitacion',
    ).filter(
        fecha_entrada__gte=fecha,
        estado__in=estados_reserva_operativos,
    ).order_by('fecha_entrada')[:5]

    serie_ocupacion = calcular_reportes_analiticos(
        fecha - timedelta(days=6),
        fecha,
    )['ocupacion']['diaria']

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
        'ocupacion': {
            'criterio': 'ESTANCIAS_REALES',
            'ocupadas': habitaciones_ocupadas,
            'total': total_habitaciones,
            'ocupacion_porcentaje': ocupacion_porcentaje,
            'diaria': serie_ocupacion,
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
                'ocupadas': ocupadas_por_tipo.get(tipo.id, 0),
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


def calcular_reportes_analiticos(desde, hasta, hotel=None):
    """
    Centraliza los indicadores historicos del modulo de reportes.
    Mantiene la pantalla desacoplada del ORM y evita duplicar consultas en la plantilla.
    """
    fechas = list(_date_range(desde, hasta))
    total_dias = len(fechas)

    habitaciones = Habitacion.objects.all()
    if hotel is not None:
        habitaciones = habitaciones.filter(hotel=hotel)

    habitaciones_por_estado = habitaciones.aggregate(
        total=Count('id'),
        disponibles=Count('id', filter=Q(estado=EstadoHabitacion.DISPONIBLE)),
        ocupadas=Count('id', filter=Q(estado=EstadoHabitacion.OCUPADA)),
        limpieza=Count('id', filter=Q(estado=EstadoHabitacion.LIMPIEZA)),
        mantenimiento=Count('id', filter=Q(estado=EstadoHabitacion.MANTENIMIENTO)),
    )
    total_habitaciones = habitaciones_por_estado['total'] or 0

    reservas_rango = Reserva.objects.select_related(
        'huesped',
        'habitacion',
        'habitacion__tipo',
    ).filter(
        fecha_entrada__range=(desde, hasta),
    )
    if hotel is not None:
        reservas_rango = reservas_rango.filter(hotel=hotel)
    reservas_validas_rango = reservas_rango.exclude(estado=EstadoReserva.CANCELADA)

    estancias_ocupacion = Estancia.objects.select_related('habitacion').filter(
        fecha_checkin__date__lte=hasta,
    ).filter(
        Q(fecha_checkout__date__gt=desde) | Q(fecha_checkout__isnull=True),
    ).exclude(estado=EstadoEstancia.CANCELADA)
    if hotel is not None:
        estancias_ocupacion = estancias_ocupacion.filter(habitacion__hotel=hotel)

    ocupacion_diaria = []
    ocupacion_semanal = defaultdict(lambda: {'ocupadas': 0, 'capacidad': 0})
    ocupacion_mensual = defaultdict(lambda: {'ocupadas': 0, 'capacidad': 0})
    habitaciones_noche_ocupadas = 0

    for fecha in fechas:
        ocupadas = estancias_ocupacion.filter(
            fecha_checkin__date__lte=fecha,
        ).filter(
            Q(fecha_checkout__date__gt=fecha) | Q(fecha_checkout__isnull=True),
        ).values('habitacion_id').distinct().count()
        capacidad = total_habitaciones
        habitaciones_noche_ocupadas += ocupadas

        semana = f'{fecha.isocalendar().year}-S{fecha.isocalendar().week:02d}'
        mes = fecha.strftime('%Y-%m')
        ocupacion_semanal[semana]['ocupadas'] += ocupadas
        ocupacion_semanal[semana]['capacidad'] += capacidad
        ocupacion_mensual[mes]['ocupadas'] += ocupadas
        ocupacion_mensual[mes]['capacidad'] += capacidad

        ocupacion_diaria.append({
            'fecha': fecha,
            'ocupadas': ocupadas,
            'porcentaje': _safe_percentage(ocupadas, capacidad),
        })

    capacidad_total_periodo = total_habitaciones * total_dias

    estancias_al_cierre = estancias_ocupacion.filter(
        fecha_checkin__date__lte=hasta,
    ).filter(
        Q(fecha_checkout__date__gt=hasta) | Q(fecha_checkout__isnull=True),
    )
    ocupadas_por_tipo = dict(
        estancias_al_cierre.values('habitacion__tipo_id').annotate(
            total=Count('habitacion_id', distinct=True),
        ).values_list('habitacion__tipo_id', 'total')
    )
    filtro_hotel = Q(habitaciones__hotel=hotel) if hotel is not None else Q()
    tipos_habitacion = TipoHabitacion.objects.annotate(
        total_habitaciones=Count('habitaciones', filter=filtro_hotel),
    ).order_by('nombre')
    if hotel is not None:
        tipos_habitacion = tipos_habitacion.filter(total_habitaciones__gt=0)

    ocupacion_por_tipo = [
        {
            'nombre': tipo.nombre,
            'total': tipo.total_habitaciones,
            'ocupadas': ocupadas_por_tipo.get(tipo.id, 0),
            'porcentaje': _safe_percentage(
                ocupadas_por_tipo.get(tipo.id, 0),
                tipo.total_habitaciones,
            ),
        }
        for tipo in tipos_habitacion
    ]

    reservas_estado = _build_distribution(
        reservas_rango,
        'estado',
        EstadoReserva.choices,
    )
    reservas_origen = _build_distribution(
        reservas_rango,
        'origen',
        OrigenReserva.choices,
    )
    tendencias_reservas = _group_reservas_by_periodo(reservas_rango)

    folios_rango = Folio.objects.select_related(
        'estancia',
        'estancia__habitacion',
        'estancia__habitacion__tipo',
    ).filter(
        estancia__fecha_checkin__date__range=(desde, hasta),
        estado__in=[EstadoFolio.PAGADO, EstadoFolio.CERRADO],
    )
    if hotel is not None:
        folios_rango = folios_rango.filter(estancia__habitacion__hotel=hotel)
    ingresos_folios = folios_rango.aggregate(
        subtotal=Sum('subtotal'),
        igv=Sum('igv'),
        total=Sum('total'),
    )
    cargos_rango = CargoEstancia.objects.filter(fecha__date__range=(desde, hasta))
    if hotel is not None:
        cargos_rango = cargos_rango.filter(estancia__habitacion__hotel=hotel)
    total_cargos = cargos_rango.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    estancias_rango = Estancia.objects.filter(
        fecha_checkin__date__range=(desde, hasta),
    ).exclude(estado=EstadoEstancia.CANCELADA)
    if hotel is not None:
        estancias_rango = estancias_rango.filter(habitacion__hotel=hotel)
    total_estancias = estancias_rango.count()
    facturas_rango = Factura.objects.filter(
        folio__in=folios_rango,
        fecha_emision__date__range=(desde, hasta),
    )

    ingresos_por_tipo = folios_rango.values(
        'estancia__habitacion__tipo__nombre',
    ).annotate(
        total=Sum('total'),
        folios=Count('id'),
    ).order_by('-total')[:6]

    cargos_por_tipo = cargos_rango.values('tipo').annotate(
        total=Sum('monto'),
        cantidad=Count('id'),
    ).order_by('-total')
    labels_cargos = dict(TipoCargo.choices)

    ingresos_diarios = defaultdict(Decimal)
    ingresos_mensuales = defaultdict(Decimal)
    for folio in folios_rango:
        fecha = timezone.localtime(folio.estancia.fecha_checkin).date()
        total = folio.total or Decimal('0.00')
        ingresos_diarios[fecha] += total
        ingresos_mensuales[fecha.strftime('%Y-%m')] += total

    reservas_huespedes = reservas_validas_rango.select_related('huesped')
    huesped_stats = {}
    total_noches = 0

    for reserva in reservas_huespedes:
        noches = max(reserva.noches, 0)
        total_noches += noches
        stats = huesped_stats.setdefault(
            reserva.huesped_id,
            {
                'huesped': reserva.huesped,
                'reservas': 0,
                'noches': 0,
            },
        )
        stats['reservas'] += 1
        stats['noches'] += noches

    huespedes_frecuentes = sorted(
        huesped_stats.values(),
        key=lambda item: (item['reservas'], item['noches']),
        reverse=True,
    )[:5]
    nacionalidades = Huesped.objects.filter(
        id__in=reservas_huespedes.values_list('huesped_id', flat=True),
    ).exclude(
        Q(nacionalidad__isnull=True) | Q(nacionalidad='')
    ).values('nacionalidad').annotate(
        total=Count('id'),
    ).order_by('-total')[:6]

    total_folios = ingresos_folios['total'] or Decimal('0.00')
    subtotal_folios = ingresos_folios['subtotal'] or Decimal('0.00')
    igv_folios = ingresos_folios['igv'] or Decimal('0.00')

    return {
        'periodo': {
            'desde': desde,
            'hasta': hasta,
            'dias': total_dias,
        },
        'ocupacion': {
            'porcentaje_periodo': _safe_percentage(
                habitaciones_noche_ocupadas,
                capacidad_total_periodo,
            ),
            'porcentaje_actual': _safe_percentage(
                habitaciones_por_estado['ocupadas'] or 0,
                total_habitaciones,
            ),
            'habitaciones': {
                'total': total_habitaciones,
                'disponibles': habitaciones_por_estado['disponibles'] or 0,
                'ocupadas': habitaciones_por_estado['ocupadas'] or 0,
                'limpieza': habitaciones_por_estado['limpieza'] or 0,
                'mantenimiento': habitaciones_por_estado['mantenimiento'] or 0,
            },
            'por_tipo': ocupacion_por_tipo,
            'diaria': ocupacion_diaria[-14:],
            'semanal': [
                {
                    'periodo': periodo,
                    'porcentaje': _safe_percentage(datos['ocupadas'], datos['capacidad']),
                }
                for periodo, datos in sorted(ocupacion_semanal.items())
            ],
            'mensual': [
                {
                    'periodo': periodo,
                    'porcentaje': _safe_percentage(datos['ocupadas'], datos['capacidad']),
                }
                for periodo, datos in sorted(ocupacion_mensual.items())
            ],
        },
        'reservas': {
            'total': reservas_rango.count(),
            'activas': reservas_validas_rango.count(),
            'por_estado': reservas_estado,
            'por_origen': reservas_origen,
            'tendencias': tendencias_reservas,
        },
        'ingresos': {
            'total': _decimal_to_float(total_folios),
            'subtotal': _decimal_to_float(subtotal_folios),
            'igv': _decimal_to_float(igv_folios),
            'cargos_adicionales': _decimal_to_float(total_cargos),
            'folios_confirmados': folios_rango.count(),
            'facturas_emitidas': facturas_rango.count(),
            'estancias_evaluadas': total_estancias,
            'promedio_estancia': _decimal_to_float(total_folios / total_estancias if total_estancias else Decimal('0.00')),
            'por_tipo_habitacion': [
                {
                    'nombre': item['estancia__habitacion__tipo__nombre'] or 'Sin tipo',
                    'total': _decimal_to_float(item['total']),
                    'folios': item['folios'],
                    'reservas': item['folios'],
                }
                for item in ingresos_por_tipo
            ],
            'por_cargos': [
                {
                    'tipo': item['tipo'],
                    'nombre': labels_cargos.get(item['tipo'], item['tipo']),
                    'total': _decimal_to_float(item['total']),
                    'cantidad': item['cantidad'],
                }
                for item in cargos_por_tipo
            ],
            'diarios': [
                {'fecha': fecha, 'total': _decimal_to_float(total)}
                for fecha, total in sorted(ingresos_diarios.items())[-14:]
            ],
            'mensuales': [
                {'periodo': periodo, 'total': _decimal_to_float(total)}
                for periodo, total in sorted(ingresos_mensuales.items())
            ],
        },
        'huespedes': {
            'total': Huesped.objects.count(),
            'con_reservas': len(huesped_stats),
            'frecuentes': huespedes_frecuentes,
            'nacionalidades': list(nacionalidades),
            'promedio_noches': round(total_noches / len(huesped_stats), 2) if huesped_stats else 0,
        },
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

        reporte = calcular_reporte_ocupacion(fecha)
        reporte['panel_diario'] = DashboardService.obtener_panel_diario(fecha)
        context['reporte'] = reporte
        return context


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA),
    name='dispatch',
)
class ReportesView(TemplateView):
    """Pantalla de reportes analiticos con metricas historicas del hotel."""

    template_name = 'pages/reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        desde, hasta, error = _parse_rango_reportes(
            self.request.GET.get('fecha_desde') or self.request.GET.get('desde'),
            self.request.GET.get('fecha_hasta') or self.request.GET.get('hasta'),
        )

        if error:
            hasta = timezone.localdate()
            desde = hasta - timedelta(days=29)
            context['rango_error'] = error

        hotel = Hotel.objects.order_by('id').first()
        context['hotel_reporte'] = hotel
        context['reportes'] = calcular_reportes_analiticos(desde, hasta, hotel=hotel)
        return context


def _respuesta_error_pdf(request, mensaje, desde='', hasta=''):
    if 'application/pdf' in request.headers.get('Accept', ''):
        return JsonResponse({'error': True, 'message': mensaje}, status=400)

    messages.error(request, mensaje)
    parametros = urlencode({'fecha_desde': desde, 'fecha_hasta': hasta})
    return redirect(f"{reverse('reportes')}?{parametros}")


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA),
    name='dispatch',
)
class ReportePDFView(View):
    """Genera el reporte operativo MINCETUR para el rango solicitado."""

    template_name = 'reportes/reporte_pdf.html'

    def get(self, request):
        desde_texto = request.GET.get('fecha_desde', '')
        hasta_texto = request.GET.get('fecha_hasta', '')
        desde, hasta, error = _parse_rango_reportes(desde_texto, hasta_texto)

        if not desde_texto or not hasta_texto:
            error = 'Debes seleccionar la fecha inicial y la fecha final.'

        if error:
            return _respuesta_error_pdf(request, error, desde_texto, hasta_texto)

        hotel = Hotel.objects.order_by('id').first()
        if hotel is None:
            return _respuesta_error_pdf(
                request,
                'No existe un establecimiento registrado para generar el reporte.',
                desde_texto,
                hasta_texto,
            )

        fecha_generacion = timezone.localtime()
        contexto = {
            'hotel': hotel,
            'reportes': calcular_reportes_analiticos(desde, hasta, hotel=hotel),
            'fecha_desde': desde,
            'fecha_hasta': hasta,
            'fecha_generacion': fecha_generacion,
            'usuario_generador': request.user.get_full_name().strip() or request.user.username,
            'codigo_reporte': f'HS-{fecha_generacion:%Y%m%d-%H%M%S}',
        }

        try:
            from weasyprint import HTML

            html = render_to_string(self.template_name, contexto, request=request)
            pdf = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
        except Exception:
            logger.exception('No fue posible generar el PDF de reportes.')
            return _respuesta_error_pdf(
                request,
                'No fue posible generar el PDF. Intenta nuevamente.',
                desde_texto,
                hasta_texto,
            )

        nombre = f'reporte_mincetur_{desde.isoformat()}_{hasta.isoformat()}.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nombre}"'
        response['Content-Length'] = len(pdf)
        return response


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

        for dia in data['ocupacion']['diaria']:
            dia['fecha'] = dia['fecha'].isoformat()

        for reserva in data['proximas_reservas']:
            reserva['fecha_entrada'] = reserva['fecha_entrada'].isoformat()
            reserva['fecha_salida'] = reserva['fecha_salida'].isoformat()

        return Response(data)
