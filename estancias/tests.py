from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from config.choices import EstadoFolio, EstadoHabitacion, EstadoReserva
from estancias.services import registrar_checkin, registrar_checkout
from facturacion.models import Folio
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.models import Reserva


class CheckinFolioTests(TestCase):
    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre='Hotel Central',
            ruc='12345678901',
            direccion='Av. Principal 123',
            estrellas=4,
            telefono='999999999',
        )
        self.tipo = TipoHabitacion.objects.create(
            nombre='Simple',
            capacidad=1,
            precio_base=Decimal('120.00'),
        )
        self.habitacion = Habitacion.objects.create(
            hotel=self.hotel,
            tipo=self.tipo,
            numero='101',
            piso=1,
            estado=EstadoHabitacion.DISPONIBLE,
        )
        self.huesped = Huesped.objects.create(
            tipo_doc='DNI',
            num_doc='12345678',
            nombres='Ana',
            apellidos='Torres',
            fecha_nacimiento=date(1991, 5, 20),
        )

    def _crear_reserva_confirmada(self):
        hoy = timezone.localdate()
        return Reserva.objects.create(
            hotel=self.hotel,
            huesped=self.huesped,
            habitacion=self.habitacion,
            fecha_entrada=hoy,
            fecha_salida=hoy + timedelta(days=1),
            estado=EstadoReserva.CONFIRMADA,
            precio_total=Decimal('120.00'),
        )

    def test_registrar_checkin_crea_folio_abierto_con_totales(self):
        reserva = self._crear_reserva_confirmada()

        estancia = registrar_checkin(reserva)

        folio = Folio.objects.get(estancia=estancia)
        self.assertEqual(folio.estado, EstadoFolio.ABIERTO)
        self.assertEqual(folio.subtotal, Decimal('120.00'))
        self.assertEqual(folio.igv, Decimal('21.60'))
        self.assertEqual(folio.total, Decimal('141.60'))

    def test_registrar_checkout_bloquea_folio_abierto(self):
        reserva = self._crear_reserva_confirmada()
        estancia = registrar_checkin(reserva)

        with self.assertRaisesMessage(ValidationError, 'No se puede hacer checkout con folio pendiente de pago.'):
            registrar_checkout(estancia)
