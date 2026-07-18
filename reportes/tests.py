from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from config.choices import (
    EstadoEstancia,
    EstadoFolio,
    EstadoHabitacion,
    EstadoReserva,
    TipoCargo,
)
from estancias.models import CargoEstancia, Estancia
from facturacion.models import Factura, Folio
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reportes.services import DashboardService, ReporteService
from reservas.models import Reserva


class ReporteDashboardServiceTests(TestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.hotel = Hotel.objects.create(
            nombre='Hotel Central',
            ruc='20123456789',
            direccion='Av. Central 123',
            estrellas=4,
            telefono='999999999',
        )
        self.tipo = TipoHabitacion.objects.create(
            nombre='Simple',
            capacidad=2,
            precio_base=Decimal('100.00'),
        )
        self.habitaciones = [
            Habitacion.objects.create(
                hotel=self.hotel,
                tipo=self.tipo,
                numero=str(numero),
                piso=1,
                estado=estado,
            )
            for numero, estado in [
                (101, EstadoHabitacion.DISPONIBLE),
                (102, EstadoHabitacion.OCUPADA),
                (103, EstadoHabitacion.OCUPADA),
            ]
        ]
        self.huespedes = [
            Huesped.objects.create(
                tipo_doc='DNI',
                num_doc=f'7000000{indice}',
                nombres=f'Huesped {indice}',
                apellidos='Prueba',
                fecha_nacimiento=date(1990, 1, indice),
                nacionalidad='Peruana',
            )
            for indice in range(1, 4)
        ]

        self.reserva_llegada = self._crear_reserva(
            self.habitaciones[0], self.huespedes[0], EstadoReserva.CONFIRMADA,
        )
        self.reserva_alojado = self._crear_reserva(
            self.habitaciones[1], self.huespedes[1], EstadoReserva.CHECKIN,
        )
        self.estancia_activa = Estancia.objects.create(
            reserva=self.reserva_alojado,
            habitacion=self.habitaciones[1],
            fecha_checkin=timezone.now(),
            precio_final=Decimal('100.00'),
            estado=EstadoEstancia.ACTIVA,
        )
        self.folio_pagado = Folio.objects.create(
            estancia=self.estancia_activa,
            subtotal=Decimal('100.00'),
            igv=Decimal('18.00'),
            total=Decimal('118.00'),
            estado=EstadoFolio.PAGADO,
        )
        self.cargo = CargoEstancia.objects.create(
            estancia=self.estancia_activa,
            concepto='Minibar',
            monto=Decimal('20.00'),
            tipo=TipoCargo.MINIBAR,
        )
        self.factura = Factura.objects.create(
            folio=self.folio_pagado,
            ruc_dni='20123456789',
            razon_social='HotelSys Prueba',
            monto_subtotal=Decimal('100.00'),
            monto_igv=Decimal('18.00'),
            monto_total=Decimal('118.00'),
        )

        self.reserva_salida = self._crear_reserva(
            self.habitaciones[2], self.huespedes[2], EstadoReserva.FINALIZADA,
        )
        Reserva.objects.filter(pk=self.reserva_salida.pk).update(
            fecha_entrada=self.hoy - timedelta(days=1),
            fecha_salida=self.hoy,
        )
        self.reserva_salida.refresh_from_db()
        self.estancia_finalizada = Estancia.objects.create(
            reserva=self.reserva_salida,
            habitacion=self.habitaciones[2],
            fecha_checkin=timezone.now() - timedelta(days=1),
            fecha_checkout=timezone.now(),
            precio_final=Decimal('100.00'),
            estado=EstadoEstancia.FINALIZADA,
        )

    def _crear_reserva(self, habitacion, huesped, estado):
        return Reserva.objects.create(
            hotel=self.hotel,
            huesped=huesped,
            habitacion=habitacion,
            fecha_entrada=self.hoy,
            fecha_salida=self.hoy + timedelta(days=1),
            estado=estado,
            precio_total=Decimal('100.00'),
        )

    def test_ocupacion_usa_estancias_reales_y_no_reservas_confirmadas(self):
        ocupacion = ReporteService.calcular_ocupacion(self.hoy)
        serie = ReporteService.calcular_serie_ocupacion(self.hoy, self.hoy)

        self.assertEqual(ocupacion['criterio'], 'ESTANCIAS_REALES')
        self.assertEqual(ocupacion['ocupadas'], 2)
        self.assertEqual(serie['diaria'][0]['ocupadas'], 2)
        self.assertEqual(ocupacion['por_tipo'][0]['ocupadas'], 2)

    def test_dashboard_diferencia_ingreso_confirmado_de_reserva_estimada(self):
        reporte = DashboardService.obtener_dashboard(self.hoy)

        self.assertEqual(reporte['ingresos']['confirmados'], 118.0)
        self.assertEqual(reporte['ingresos']['reservas_estimadas_fecha'], 200.0)
        self.assertEqual(reporte['panel_diario']['totales'], {
            'llegadas': 1,
            'alojados': 1,
            'salidas': 1,
        })

    def test_reporte_por_tipo_suma_folios_confirmados(self):
        reporte = ReporteService.obtener_analiticos(
            self.hoy,
            self.hoy,
            hotel=self.hotel,
        )

        self.assertEqual(reporte['ingresos']['criterio'], 'FOLIOS_PAGADOS_O_CERRADOS')
        self.assertEqual(reporte['ingresos']['total'], 118.0)
        self.assertEqual(reporte['ingresos']['por_tipo_habitacion'][0]['folios'], 1)
        self.assertEqual(reporte['ingresos']['folios_confirmados'], 1)
        self.assertEqual(reporte['ingresos']['facturas_emitidas'], 1)
        self.assertEqual(reporte['ingresos']['estancias_evaluadas'], 1)
        self.assertEqual(reporte['ingresos']['cargos_adicionales'], 20.0)
        self.assertEqual(reporte['establecimiento']['numero_pisos'], 1)
        self.assertEqual(reporte['tipos_habitacion'][0]['capacidad'], 2)


class ReporteDashboardViewTests(ReporteDashboardServiceTests):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser(
            username='admin_reportes',
            email='admin@example.com',
            password='ClaveSegura123!',
        )
        self.client.force_login(self.user)

    @override_settings(
        ROOM_PLAN_WEBSOCKET_URL_TEMPLATE='/ws/hoteles/{hotel_id}/habitaciones/',
    )
    def test_dashboard_renderiza_panel_diario_y_configuracion_websocket(self):
        response = self.client.get(reverse('dashboard'), {'fecha': self.hoy.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Llegadas, alojados y salidas')
        self.assertContains(response, '/ws/hoteles/{hotel_id}/habitaciones/')
        self.assertEqual(response.context['reporte']['panel_diario']['totales']['llegadas'], 1)

    def test_endpoint_ocupacion_reutiliza_reporte_service(self):
        response = self.client.get(
            reverse('api_reporte_ocupacion'),
            {'fecha': self.hoy.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ocupacion']['criterio'], 'ESTANCIAS_REALES')
        self.assertEqual(response.json()['ingresos']['confirmados'], 118.0)

    def test_pagina_reportes_muestra_boton_pdf_y_conserva_fechas(self):
        response = self.client.get(
            reverse('reportes'),
            {
                'fecha_desde': self.hoy.isoformat(),
                'fecha_hasta': self.hoy.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('reporte_pdf'))
        self.assertContains(response, 'Descargar PDF')
        self.assertContains(response, 'name="fecha_desde"')
        self.assertContains(response, 'name="fecha_hasta"')

    def test_reporte_pdf_se_descarga_con_el_periodo_filtrado(self):
        response = self.client.get(
            reverse('reporte_pdf'),
            {
                'fecha_desde': self.hoy.isoformat(),
                'fecha_hasta': self.hoy.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertGreater(len(response.content), 5000)

    def test_reporte_pdf_rechaza_rango_invalido_sin_exponer_error_tecnico(self):
        response = self.client.get(
            reverse('reporte_pdf'),
            {
                'fecha_desde': self.hoy.isoformat(),
                'fecha_hasta': (self.hoy - timedelta(days=1)).isoformat(),
            },
            HTTP_ACCEPT='application/pdf',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            'La fecha inicial no puede ser mayor que la fecha final.',
        )

    def test_reporte_pdf_requiere_autenticacion(self):
        self.client.logout()

        response = self.client.get(
            reverse('reporte_pdf'),
            {
                'fecha_desde': self.hoy.isoformat(),
                'fecha_hasta': self.hoy.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_plano_muestra_detalle_del_huesped_actual(self):
        response = self.client.get(reverse('habitaciones:listar_habitaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.huespedes[1].nombre_completo)
        self.assertContains(response, 'roomDetailModal')
