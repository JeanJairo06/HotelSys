from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from config.choices import (
    EstadoEstancia,
    EstadoFolio,
    EstadoHabitacion,
    EstadoReserva,
    OrigenReserva,
    TipoCargo,
)
from estancias.models import CargoEstancia, Estancia
from facturacion.models import Factura, Folio
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.models import Reserva


def _decimal_to_float(value):
    return float(value or Decimal('0.00'))


def _safe_percentage(value, total):
    return round((value / total) * 100, 2) if total else 0


def _date_range(desde, hasta):
    fecha = desde
    while fecha <= hasta:
        yield fecha
        fecha += timedelta(days=1)


def _local_day_bounds(fecha):
    inicio = datetime.combine(fecha, time.min)
    fin = inicio + timedelta(days=1)
    zona = timezone.get_current_timezone()
    return timezone.make_aware(inicio, zona), timezone.make_aware(fin, zona)


def _build_distribution(queryset, field_name, choices):
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


class ReporteService:
    """
    Fuente unica de metricas operativas e historicas.

    La ocupacion representa estancias reales: una habitacion se considera ocupada
    desde el check-in (inclusive) hasta el checkout (exclusive). Reservas futuras
    o impagas se muestran por separado y nunca se contabilizan como ingreso recibido.
    """

    ESTADOS_INGRESO_CONFIRMADO = [EstadoFolio.PAGADO, EstadoFolio.CERRADO]

    @classmethod
    def _estancias_en_fecha(cls, fecha, hotel=None):
        inicio, fin = _local_day_bounds(fecha)
        estancias = Estancia.objects.select_related(
            'reserva',
            'reserva__huesped',
            'habitacion',
            'habitacion__hotel',
            'habitacion__tipo',
        ).filter(
            fecha_checkin__lt=fin,
        ).filter(
            Q(fecha_checkout__gt=inicio) | Q(fecha_checkout__isnull=True),
        ).exclude(
            estado=EstadoEstancia.CANCELADA,
        )
        if hotel is not None:
            estancias = estancias.filter(habitacion__hotel=hotel)
        return estancias

    @classmethod
    def calcular_ocupacion(cls, fecha, hotel=None):
        habitaciones = Habitacion.objects.all()
        if hotel is not None:
            habitaciones = habitaciones.filter(hotel=hotel)

        total_habitaciones = habitaciones.count()
        estancias = cls._estancias_en_fecha(fecha, hotel=hotel)
        habitaciones_ocupadas = estancias.values('habitacion_id').distinct().count()

        ocupadas_por_tipo = dict(
            estancias.values('habitacion__tipo_id')
            .annotate(total=Count('habitacion_id', distinct=True))
            .values_list('habitacion__tipo_id', 'total')
        )
        filtro_hotel = Q(habitaciones__hotel=hotel) if hotel is not None else Q()
        tipos = TipoHabitacion.objects.annotate(
            total_habitaciones=Count('habitaciones', filter=filtro_hotel),
        )
        if hotel is not None:
            tipos = tipos.filter(total_habitaciones__gt=0)
        tipos = tipos.order_by('nombre')

        return {
            'criterio': 'ESTANCIAS_REALES',
            'fecha': fecha,
            'ocupadas': habitaciones_ocupadas,
            'total': total_habitaciones,
            'porcentaje': _safe_percentage(habitaciones_ocupadas, total_habitaciones),
            'por_tipo': [
                {
                    'id': tipo.id,
                    'nombre': tipo.nombre,
                    'total': tipo.total_habitaciones,
                    'ocupadas': ocupadas_por_tipo.get(tipo.id, 0),
                    'porcentaje': _safe_percentage(
                        ocupadas_por_tipo.get(tipo.id, 0),
                        tipo.total_habitaciones,
                    ),
                }
                for tipo in tipos
            ],
        }

    @classmethod
    def calcular_serie_ocupacion(cls, desde, hasta, hotel=None):
        fechas = list(_date_range(desde, hasta))
        habitaciones = Habitacion.objects.all()
        if hotel is not None:
            habitaciones = habitaciones.filter(hotel=hotel)
        total_habitaciones = habitaciones.count()
        inicio, _ = _local_day_bounds(desde)
        _, fin = _local_day_bounds(hasta)
        estancias_query = (
            Estancia.objects.filter(fecha_checkin__lt=fin)
            .filter(Q(fecha_checkout__gt=inicio) | Q(fecha_checkout__isnull=True))
            .exclude(estado=EstadoEstancia.CANCELADA)
        )
        if hotel is not None:
            estancias_query = estancias_query.filter(habitacion__hotel=hotel)
        estancias = list(
            estancias_query.values('habitacion_id', 'fecha_checkin', 'fecha_checkout')
        )

        diaria = []
        semanal = defaultdict(lambda: {'ocupadas': 0, 'capacidad': 0})
        mensual = defaultdict(lambda: {'ocupadas': 0, 'capacidad': 0})

        for fecha in fechas:
            ocupadas = set()
            dia_inicio, dia_fin = _local_day_bounds(fecha)
            for estancia in estancias:
                if estancia['fecha_checkin'] < dia_fin and (
                    estancia['fecha_checkout'] is None
                    or estancia['fecha_checkout'] > dia_inicio
                ):
                    ocupadas.add(estancia['habitacion_id'])

            cantidad = len(ocupadas)
            semana = f'{fecha.isocalendar().year}-S{fecha.isocalendar().week:02d}'
            mes = fecha.strftime('%Y-%m')
            semanal[semana]['ocupadas'] += cantidad
            semanal[semana]['capacidad'] += total_habitaciones
            mensual[mes]['ocupadas'] += cantidad
            mensual[mes]['capacidad'] += total_habitaciones
            diaria.append({
                'fecha': fecha,
                'ocupadas': cantidad,
                'porcentaje': _safe_percentage(cantidad, total_habitaciones),
            })

        return {
            'criterio': 'ESTANCIAS_REALES',
            'diaria': diaria,
            'semanal': [
                {
                    'periodo': periodo,
                    'porcentaje': _safe_percentage(datos['ocupadas'], datos['capacidad']),
                }
                for periodo, datos in sorted(semanal.items())
            ],
            'mensual': [
                {
                    'periodo': periodo,
                    'porcentaje': _safe_percentage(datos['ocupadas'], datos['capacidad']),
                }
                for periodo, datos in sorted(mensual.items())
            ],
        }

    @classmethod
    def obtener_resumen_operativo(cls, fecha):
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
        ocupacion = cls.calcular_ocupacion(fecha)
        serie = cls.calcular_serie_ocupacion(fecha - timedelta(days=6), fecha)

        reservas_en_fecha = Reserva.objects.filter(
            fecha_entrada__lte=fecha,
            fecha_salida__gt=fecha,
        ).exclude(estado__in=[EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA])
        habitaciones_comprometidas = set(reservas_en_fecha.values_list('habitacion_id', flat=True))
        habitaciones_comprometidas.update(
            Habitacion.objects.filter(estado=EstadoHabitacion.OCUPADA).values_list('id', flat=True)
        )
        reservas_del_dia = Reserva.objects.filter(fecha_entrada=fecha)

        folios_confirmados = Folio.objects.filter(estado__in=cls.ESTADOS_INGRESO_CONFIRMADO)
        ingresos_confirmados = folios_confirmados.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        reservas_estimadas_fecha = reservas_del_dia.exclude(
            estado=EstadoReserva.CANCELADA,
        ).aggregate(total=Sum('precio_total'))['total'] or Decimal('0.00')
        cargos_totales = CargoEstancia.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

        tipos_habitacion = TipoHabitacion.objects.annotate(
            total_habitaciones=Count('habitaciones'),
            disponibles=Count('habitaciones', filter=Q(habitaciones__estado=EstadoHabitacion.DISPONIBLE)),
            ocupadas=Count('habitaciones', filter=Q(habitaciones__estado=EstadoHabitacion.OCUPADA)),
        ).order_by('nombre')
        proximas_reservas = Reserva.objects.select_related('huesped', 'habitacion').filter(
            fecha_entrada__gte=fecha,
            estado__in=estados_reserva_operativos,
        ).order_by('fecha_entrada')[:5]

        return {
            'fecha': fecha,
            'habitaciones': {
                'total': total_habitaciones,
                'disponibles': habitaciones_por_estado['disponibles'] or 0,
                'ocupadas': habitaciones_por_estado['ocupadas'] or 0,
                'reservadas_en_fecha': reservas_en_fecha.count(),
                'reservadas_u_ocupadas': len(habitaciones_comprometidas),
                'limpieza': habitaciones_por_estado['limpieza'] or 0,
                'mantenimiento': habitaciones_por_estado['mantenimiento'] or 0,
            },
            'ocupacion': {
                **ocupacion,
                'ocupacion_porcentaje': ocupacion['porcentaje'],
                'diaria': serie['diaria'],
                'semanal': serie['semanal'],
            },
            'reservas': {
                'total': Reserva.objects.count(),
                'en_fecha': reservas_en_fecha.count(),
                'registradas_fecha': reservas_del_dia.count(),
                'pendientes': Reserva.objects.filter(estado=EstadoReserva.PENDIENTE).count(),
                'confirmadas': Reserva.objects.filter(estado=EstadoReserva.CONFIRMADA).count(),
                'checkin': Reserva.objects.filter(estado=EstadoReserva.CHECKIN).count(),
                'finalizadas': Reserva.objects.filter(estado=EstadoReserva.FINALIZADA).count(),
                'canceladas': Reserva.objects.filter(estado=EstadoReserva.CANCELADA).count(),
            },
            'huespedes': {'total': Huesped.objects.count()},
            'estancias': {
                'activas': Estancia.objects.filter(estado=EstadoEstancia.ACTIVA).count(),
                'finalizadas': Estancia.objects.filter(estado=EstadoEstancia.FINALIZADA).count(),
            },
            'ingresos': {
                'confirmados': _decimal_to_float(ingresos_confirmados),
                'folios_pagados': _decimal_to_float(ingresos_confirmados),
                'reservas_estimadas_fecha': _decimal_to_float(reservas_estimadas_fecha),
                'reservas_fecha': _decimal_to_float(reservas_estimadas_fecha),
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
                    'huesped': reserva.huesped.nombre_completo,
                    'habitacion': reserva.habitacion.numero,
                    'fecha_entrada': reserva.fecha_entrada,
                    'fecha_salida': reserva.fecha_salida,
                    'estado': reserva.estado,
                    'estado_display': reserva.get_estado_display(),
                }
                for reserva in proximas_reservas
            ],
            'hoteles_ids': list(
                Habitacion.objects.order_by().values_list('hotel_id', flat=True).distinct()
            ),
        }

    @classmethod
    def obtener_hotel_principal(cls):
        """
        Devuelve el establecimiento operativo del proyecto.

        El modelo de empleados actual no incluye una relacion con Hotel. Para
        evitar que el endpoint acepte un hotel manipulable por URL, Reportes
        trabaja con el establecimiento principal configurado en la base.
        """
        return Hotel.objects.order_by('id').first()

    @classmethod
    def obtener_analiticos(cls, desde, hasta, hotel=None):
        total_dias = (hasta - desde).days + 1
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
        serie_ocupacion = cls.calcular_serie_ocupacion(desde, hasta, hotel=hotel)
        ocupacion_fin = cls.calcular_ocupacion(hasta, hotel=hotel)

        reservas_rango = Reserva.objects.select_related(
            'huesped', 'habitacion', 'habitacion__tipo',
        ).filter(fecha_entrada__range=(desde, hasta))
        if hotel is not None:
            reservas_rango = reservas_rango.filter(hotel=hotel)
        reservas_validas_rango = reservas_rango.exclude(estado=EstadoReserva.CANCELADA)
        reservas_estado = _build_distribution(reservas_rango, 'estado', EstadoReserva.choices)
        reservas_origen = _build_distribution(reservas_rango, 'origen', OrigenReserva.choices)
        tendencias_reservas = _group_reservas_by_periodo(reservas_rango)

        folios_rango = Folio.objects.select_related(
            'estancia', 'estancia__habitacion', 'estancia__habitacion__tipo',
        ).filter(
            estancia__fecha_checkin__date__range=(desde, hasta),
            estado__in=cls.ESTADOS_INGRESO_CONFIRMADO,
        )
        if hotel is not None:
            folios_rango = folios_rango.filter(estancia__habitacion__hotel=hotel)
        ingresos_folios = folios_rango.aggregate(
            subtotal=Sum('subtotal'), igv=Sum('igv'), total=Sum('total'),
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
            total=Sum('monto'), cantidad=Count('id'),
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
                {'huesped': reserva.huesped, 'reservas': 0, 'noches': 0},
            )
            stats['reservas'] += 1
            stats['noches'] += noches

        huespedes_frecuentes = sorted(
            huesped_stats.values(),
            key=lambda item: (item['reservas'], item['noches']),
            reverse=True,
        )[:5]
        huespedes_periodo = Huesped.objects.filter(
            id__in=reservas_huespedes.values_list('huesped_id', flat=True),
        ).distinct()
        nacionalidades_query = huespedes_periodo.exclude(
            Q(nacionalidad__isnull=True) | Q(nacionalidad=''),
        ).values('nacionalidad').annotate(total=Count('id')).order_by('-total')[:6]
        nacionalidades = list(nacionalidades_query)
        total_nacionalidades = sum(item['total'] for item in nacionalidades)
        for item in nacionalidades:
            item['porcentaje'] = _safe_percentage(item['total'], total_nacionalidades)

        total_folios = ingresos_folios['total'] or Decimal('0.00')
        subtotal_folios = ingresos_folios['subtotal'] or Decimal('0.00')
        igv_folios = ingresos_folios['igv'] or Decimal('0.00')
        total_folios_confirmados = folios_rango.count()

        ingresos_por_tipo_lista = [
            {
                'nombre': item['estancia__habitacion__tipo__nombre'] or 'Sin tipo',
                'total': _decimal_to_float(item['total']),
                'folios': item['folios'],
                'reservas': item['folios'],
                'porcentaje': _safe_percentage(item['total'] or 0, total_folios),
            }
            for item in ingresos_por_tipo
        ]
        cargos_por_tipo_lista = [
            {
                'tipo': item['tipo'],
                'nombre': labels_cargos.get(item['tipo'], item['tipo']),
                'total': _decimal_to_float(item['total']),
                'cantidad': item['cantidad'],
                'porcentaje': _safe_percentage(item['total'] or 0, total_cargos),
            }
            for item in cargos_por_tipo
        ]

        ocupacion_por_tipo = {
            item['id']: item['ocupadas']
            for item in ocupacion_fin['por_tipo']
        }
        filtro_hotel = Q(habitaciones__hotel=hotel) if hotel is not None else Q()
        tipos_habitacion = TipoHabitacion.objects.annotate(
            total_habitaciones=Count('habitaciones', filter=filtro_hotel),
        )
        if hotel is not None:
            tipos_habitacion = tipos_habitacion.filter(total_habitaciones__gt=0)
        tipos_habitacion = tipos_habitacion.order_by('nombre')

        return {
            'periodo': {'desde': desde, 'hasta': hasta, 'dias': total_dias},
            'establecimiento': {
                'hotel': hotel,
                'total_habitaciones': total_habitaciones,
                'numero_pisos': habitaciones.values('piso').distinct().count(),
            },
            'ocupacion': {
                'criterio': serie_ocupacion['criterio'],
                'porcentaje_periodo': _safe_percentage(
                    sum(item['ocupadas'] for item in serie_ocupacion['diaria']),
                    total_habitaciones * total_dias,
                ),
                'porcentaje_actual': ocupacion_fin['porcentaje'],
                'habitaciones': {
                    'total': total_habitaciones,
                    'disponibles': habitaciones_por_estado['disponibles'] or 0,
                    'ocupadas': habitaciones_por_estado['ocupadas'] or 0,
                    'limpieza': habitaciones_por_estado['limpieza'] or 0,
                    'mantenimiento': habitaciones_por_estado['mantenimiento'] or 0,
                },
                'por_tipo': ocupacion_fin['por_tipo'],
                'diaria': serie_ocupacion['diaria'][-14:],
                'semanal': serie_ocupacion['semanal'],
                'mensual': serie_ocupacion['mensual'],
            },
            'reservas': {
                'total': reservas_rango.count(),
                'activas': reservas_validas_rango.count(),
                'por_estado': reservas_estado,
                'por_origen': reservas_origen,
                'tendencias': tendencias_reservas,
            },
            'ingresos': {
                'criterio': 'FOLIOS_PAGADOS_O_CERRADOS',
                'total': _decimal_to_float(total_folios),
                'subtotal': _decimal_to_float(subtotal_folios),
                'igv': _decimal_to_float(igv_folios),
                'cargos_adicionales': _decimal_to_float(total_cargos),
                'folios_confirmados': total_folios_confirmados,
                'facturas_emitidas': facturas_rango.count(),
                'estancias_evaluadas': estancias_rango.count(),
                'promedio_estancia': _decimal_to_float(
                    total_folios / total_folios_confirmados
                    if total_folios_confirmados
                    else Decimal('0.00')
                ),
                'por_tipo_habitacion': ingresos_por_tipo_lista,
                'por_cargos': cargos_por_tipo_lista,
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
                'total': huespedes_periodo.count(),
                'con_reservas': len(huesped_stats),
                'frecuentes': huespedes_frecuentes,
                'nacionalidades': nacionalidades,
                'promedio_noches': round(total_noches / len(huesped_stats), 2) if huesped_stats else 0,
            },
            'tipos_habitacion': [
                {
                    'nombre': tipo.nombre,
                    'capacidad': tipo.capacidad,
                    'precio_base': _decimal_to_float(tipo.precio_base),
                    'total_habitaciones': tipo.total_habitaciones,
                    'ocupadas': ocupacion_por_tipo.get(tipo.id, 0),
                }
                for tipo in tipos_habitacion
            ],
        }


class DashboardService:
    """Compone el dashboard y el panel diario sobre las metricas de ReporteService."""

    @classmethod
    def obtener_dashboard(cls, fecha):
        reporte = ReporteService.obtener_resumen_operativo(fecha)
        reporte['panel_diario'] = cls.obtener_panel_diario(fecha)
        return reporte

    @classmethod
    def obtener_panel_diario(cls, fecha):
        llegadas = list(
            Reserva.objects.select_related('huesped', 'habitacion', 'habitacion__tipo')
            .filter(
                fecha_entrada=fecha,
                estado__in=[EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA],
            )
            .order_by('habitacion__numero', 'huesped__apellidos')
        )
        alojados = list(
            ReporteService._estancias_en_fecha(fecha)
            .filter(estado=EstadoEstancia.ACTIVA)
            .select_related('folio')
            .order_by('habitacion__numero')
        )
        inicio, fin = _local_day_bounds(fecha)
        salidas = list(
            Estancia.objects.select_related(
                'reserva',
                'reserva__huesped',
                'habitacion',
                'habitacion__tipo',
                'folio',
            ).filter(
                Q(reserva__fecha_salida=fecha)
                | Q(fecha_checkout__gte=inicio, fecha_checkout__lt=fin),
            ).exclude(
                estado=EstadoEstancia.CANCELADA,
            ).order_by('habitacion__numero')
        )

        return {
            'fecha': fecha,
            'llegadas': llegadas,
            'alojados': alojados,
            'salidas': salidas,
            'totales': {
                'llegadas': len(llegadas),
                'alojados': len(alojados),
                'salidas': len(salidas),
            },
        }
