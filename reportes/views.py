from datetime import timedelta

from django.conf import settings
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

from api.permissions import HasAnyRole
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA
from reportes.services import DashboardService, ReporteService


def _parse_fecha_reporte(fecha_texto):
    if not fecha_texto:
        return timezone.localdate(), None
    fecha = parse_date(fecha_texto)
    if fecha is None:
        return None, 'El parametro fecha debe tener formato YYYY-MM-DD.'
    return fecha, None


def _parse_rango_reportes(desde_texto, hasta_texto):
    hoy = timezone.localdate()
    desde = parse_date(desde_texto) if desde_texto else hoy - timedelta(days=29)
    hasta = parse_date(hasta_texto) if hasta_texto else hoy
    if desde is None or hasta is None:
        return None, None, 'Las fechas deben tener formato YYYY-MM-DD.'
    if desde > hasta:
        return None, None, 'La fecha inicial no puede ser mayor que la fecha final.'
    return desde, hasta, None


def _websocket_context(hoteles_ids):
    """
    El backend Channels pertenece al contrato global de integracion.

    Mientras ese contrato se integra, el cliente queda desactivado si Jean no
    proporciona ROOM_PLAN_WEBSOCKET_URL_TEMPLATE. El valor debe contener
    ``{hotel_id}`` y puede ser una ruta relativa o una URL ws/wss completa.
    """
    return {
        'websocket_url_template': getattr(
            settings,
            'ROOM_PLAN_WEBSOCKET_URL_TEMPLATE',
            '',
        ),
        'websocket_hoteles_ids': hoteles_ids,
    }


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA, ROLE_HOUSEKEEPING),
    name='dispatch',
)
class DashboardView(TemplateView):
    template_name = 'pages/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fecha, error = _parse_fecha_reporte(self.request.GET.get('fecha'))
        if error:
            fecha = timezone.localdate()
            context['fecha_error'] = error

        reporte = DashboardService.obtener_dashboard(fecha)
        context['reporte'] = reporte
        context.update(_websocket_context(reporte['hoteles_ids']))
        return context


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA),
    name='dispatch',
)
class ReportesView(TemplateView):
    template_name = 'pages/reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        desde, hasta, error = _parse_rango_reportes(
            self.request.GET.get('desde'),
            self.request.GET.get('hasta'),
        )
        if error:
            hasta = timezone.localdate()
            desde = hasta - timedelta(days=29)
            context['rango_error'] = error

        context['reportes'] = ReporteService.obtener_analiticos(desde, hasta)
        return context


class ReporteOcupacionAPIView(APIView):
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA, ROLE_HOUSEKEEPING]

    def get(self, request):
        fecha, error = _parse_fecha_reporte(request.query_params.get('fecha'))
        if error:
            return Response(
                {'error': True, 'message': error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = ReporteService.obtener_resumen_operativo(fecha)
        data['fecha'] = fecha.isoformat()
        data['ocupacion']['fecha'] = fecha.isoformat()
        for item in data['ocupacion']['diaria']:
            item['fecha'] = item['fecha'].isoformat()
        for reserva in data['proximas_reservas']:
            reserva['fecha_entrada'] = reserva['fecha_entrada'].isoformat()
            reserva['fecha_salida'] = reserva['fecha_salida'].isoformat()
        return Response(data)


# Alias temporales para consumidores internos antiguos. La decision de negocio
# permanece en las clases de servicio y puede retirarse cuando todos los modulos
# migren sus imports.
def calcular_reporte_ocupacion(fecha):
    return ReporteService.obtener_resumen_operativo(fecha)


def calcular_reportes_analiticos(desde, hasta):
    return ReporteService.obtener_analiticos(desde, hasta)
