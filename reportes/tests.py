from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from config.choices import EstadoEstancia, EstadoFolio, EstadoHabitacion, EstadoReserva
from estancias.models import Estancia
from facturacion.models import Folio
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reportes.views import calcular_reporte_ocupacion, calcular_reportes_analiticos
from reservas.models import Reserva


@override_settings(
    STORAGES={
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    },
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    },
)
class ReportesIntegrationTests(TestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.hotel = Hotel.objects.create(
            nombre='Hotel Central',
            ruc='20123456789',
            direccion='Av. Central 123',
            estrellas=3,
            telefono='999999999',
        )
        tipo = TipoHabitacion.objects.create(
            nombre='Simple',
            capacidad=2,
            precio_base=Decimal('100.00'),
        )
        self.habitacion = Habitacion.objects.create(
            hotel=self.hotel,
            tipo=tipo,
            numero='101',
            piso=1,
            estado=EstadoHabitacion.OCUPADA,
        )
        huesped = Huesped.objects.create(
            tipo_doc='DNI',
            num_doc='70000001',
            nombres='Huesped',
            apellidos='Prueba',
            fecha_nacimiento=date(1990, 1, 1),
            nacionalidad='Peruana',
        )
        reserva = Reserva.objects.create(
            hotel=self.hotel,
            huesped=huesped,
            habitacion=self.habitacion,
            fecha_entrada=self.hoy,
            fecha_salida=self.hoy + timedelta(days=1),
            estado=EstadoReserva.CHECKIN,
            precio_total=Decimal('100.00'),
        )
        estancia = Estancia.objects.create(
            reserva=reserva,
            habitacion=self.habitacion,
            fecha_checkin=timezone.now(),
            precio_final=Decimal('100.00'),
            estado=EstadoEstancia.ACTIVA,
        )
        Folio.objects.create(
            estancia=estancia,
            subtotal=Decimal('100.00'),
            igv=Decimal('18.00'),
            total=Decimal('118.00'),
            estado=EstadoFolio.PAGADO,
        )
        self.user = User.objects.create_superuser(
            username='admin_reportes',
            email='admin@example.com',
            password='ClaveSegura123!',
        )

    def test_metricas_usan_estancias_reales_y_folios_confirmados(self):
        dashboard = calcular_reporte_ocupacion(self.hoy)
        reporte = calcular_reportes_analiticos(self.hoy, self.hoy)

        self.assertEqual(dashboard['habitaciones']['ocupadas'], 1)
        self.assertEqual(reporte['ocupacion']['porcentaje_periodo'], 100.0)
        self.assertEqual(reporte['ingresos']['total'], 118.0)
        self.assertEqual(reporte['ingresos']['por_tipo_habitacion'][0]['folios'], 1)

    @patch('weasyprint.HTML')
    def test_pdf_mincetur_descarga_el_rango_seleccionado(self, html):
        html.return_value.write_pdf.return_value = b'%PDF-1.7 test'
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporte_pdf'),
            {'fecha_desde': self.hoy.isoformat(), 'fecha_hasta': self.hoy.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_mincetur_rechaza_un_rango_invalido(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporte_pdf'),
            {
                'fecha_desde': self.hoy.isoformat(),
                'fecha_hasta': (self.hoy - timedelta(days=1)).isoformat(),
            },
            HTTP_ACCEPT='application/pdf',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], True)

    def test_dashboard_redisenado_renderiza_metricas_operativas(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'), {'fecha': self.hoy.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumen del dia')
        self.assertContains(response, 'Ingresos confirmados')
        self.assertContains(response, 'Panel diario')

    def test_api_ocupacion_expone_serie_basada_en_estancias(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('api_reporte_ocupacion'),
            {'fecha': self.hoy.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ocupacion']['criterio'], 'ESTANCIAS_REALES')
        self.assertEqual(len(response.json()['ocupacion']['diaria']), 7)

    def test_reportes_renderiza_accion_pdf_y_nota_de_calculo(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reportes'),
            {'fecha_desde': self.hoy.isoformat(), 'fecha_hasta': self.hoy.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Descargar PDF')
        self.assertContains(response, 'folios pagados o cerrados')
