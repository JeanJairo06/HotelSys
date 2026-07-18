import logging
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

from django.contrib import messages
from django.conf import settings
from django.contrib.staticfiles import finders
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

from api.permissions import HasAnyRole
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA
from reportes.services import DashboardService, ReporteService


logger = logging.getLogger(__name__)


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


def _parse_rango_pdf(desde_texto, hasta_texto):
    if not desde_texto or not hasta_texto:
        return None, None, 'Debes seleccionar la fecha inicial y la fecha final.'
    return _parse_rango_reportes(desde_texto, hasta_texto)


def _respuesta_error_pdf(request, mensaje, desde_texto='', hasta_texto=''):
    if 'application/pdf' in request.headers.get('Accept', ''):
        return JsonResponse({'error': True, 'message': mensaje}, status=400)

    messages.error(request, mensaje)
    parametros = urlencode({
        'fecha_desde': desde_texto,
        'fecha_hasta': hasta_texto,
    })
    return redirect(f"{reverse('reportes')}?{parametros}")


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
            self.request.GET.get('fecha_desde') or self.request.GET.get('desde'),
            self.request.GET.get('fecha_hasta') or self.request.GET.get('hasta'),
        )
        if error:
            hasta = timezone.localdate()
            desde = hasta - timedelta(days=29)
            context['rango_error'] = error

        hotel = ReporteService.obtener_hotel_principal()
        context['hotel_reporte'] = hotel
        context['reportes'] = ReporteService.obtener_analiticos(
            desde,
            hasta,
            hotel=hotel,
        )
        return context


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA),
    name='dispatch',
)
class ReportePDFView(View):
    template_name = 'reportes/reporte_pdf.html'

    def get(self, request):
        desde_texto = request.GET.get('fecha_desde', '')
        hasta_texto = request.GET.get('fecha_hasta', '')
        desde, hasta, error = _parse_rango_pdf(desde_texto, hasta_texto)
        if error:
            return _respuesta_error_pdf(
                request,
                error,
                desde_texto,
                hasta_texto,
            )

        hotel = ReporteService.obtener_hotel_principal()
        if hotel is None:
            return _respuesta_error_pdf(
                request,
                'No existe un establecimiento registrado para generar el reporte.',
                desde_texto,
                hasta_texto,
            )

        logo_path = finders.find('img/Minsa.png')
        if not logo_path:
            logger.error('No se encontro el recurso estatico img/Minsa.png.')
            return _respuesta_error_pdf(
                request,
                'No fue posible cargar la imagen institucional del reporte.',
                desde_texto,
                hasta_texto,
            )

        fecha_generacion = timezone.localtime()
        reporte = ReporteService.obtener_analiticos(
            desde,
            hasta,
            hotel=hotel,
        )
        usuario_nombre = request.user.get_full_name().strip() or request.user.username
        contexto = {
            'hotel': hotel,
            'reporte': reporte,
            'fecha_desde': desde,
            'fecha_hasta': hasta,
            'fecha_generacion': fecha_generacion,
            'usuario_generador': usuario_nombre,
            'codigo_reporte': f'HS-{fecha_generacion:%Y%m%d-%H%M%S}',
            'logo_uri': Path(logo_path).resolve().as_uri(),
        }

        try:
            from weasyprint import HTML

            html = render_to_string(self.template_name, contexto, request=request)
            pdf = HTML(
                string=html,
                base_url=settings.BASE_DIR.as_uri(),
            ).write_pdf()
        except Exception:
            logger.exception('No fue posible generar el PDF de reportes.')
            return _respuesta_error_pdf(
                request,
                'No fue posible generar el PDF. Intenta nuevamente.',
                desde_texto,
                hasta_texto,
            )

        nombre = f'reporte_hotelsys_{desde.isoformat()}_{hasta.isoformat()}.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nombre}"'
        response['Content-Length'] = len(pdf)
        return response


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
