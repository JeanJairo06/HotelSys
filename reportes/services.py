from django.db.models import Q

from config.choices import EstadoEstancia, EstadoReserva
from estancias.models import Estancia
from reservas.models import Reserva


class DashboardService:
    """Consultas operativas especificas del dashboard."""

    @classmethod
    def obtener_panel_diario(cls, fecha):
        llegadas = Reserva.objects.select_related('huesped', 'habitacion').filter(
            fecha_entrada=fecha,
            estado__in=[EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA],
        ).order_by('habitacion__numero')
        alojados = Estancia.objects.select_related(
            'reserva',
            'reserva__huesped',
            'habitacion',
            'folio',
        ).filter(
            fecha_checkin__date__lte=fecha,
            estado=EstadoEstancia.ACTIVA,
        ).filter(
            Q(fecha_checkout__date__gt=fecha) | Q(fecha_checkout__isnull=True),
        ).order_by('habitacion__numero')
        salidas = Estancia.objects.select_related(
            'reserva',
            'reserva__huesped',
            'habitacion',
            'folio',
        ).filter(
            Q(reserva__fecha_salida=fecha) | Q(fecha_checkout__date=fecha),
        ).exclude(estado=EstadoEstancia.CANCELADA).order_by('habitacion__numero')

        return {
            'fecha': fecha,
            'llegadas': llegadas,
            'alojados': alojados,
            'salidas': salidas,
            'totales': {
                'llegadas': llegadas.count(),
                'alojados': alojados.count(),
                'salidas': salidas.count(),
            },
        }


class ReporteService:
    """Punto de entrada estable para consumidores internos de reportes."""

    @staticmethod
    def obtener_resumen_operativo(fecha):
        from reportes.views import calcular_reporte_ocupacion

        return calcular_reporte_ocupacion(fecha)

    @staticmethod
    def obtener_analiticos(desde, hasta, hotel=None):
        from reportes.views import calcular_reportes_analiticos

        return calcular_reportes_analiticos(desde, hasta, hotel=hotel)
