from django.test import TestCase
from datetime import date
from decimal import Decimal
from django.utils import timezone

from config.choices import TipoCargo
from estancias.models import CargoEstancia, Estancia
from facturacion.models import Folio
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.models import Reserva


class FolioModelTests(TestCase):
    def test_calcular_totales_incluye_estancia_y_cargos_con_decimal(self):
        hotel = Hotel.objects.create(
            nombre='Hotel Central',
            ruc='12345678901',
            direccion='Av. Principal 123',
            estrellas=4,
            telefono='999999999',
        )
        tipo = TipoHabitacion.objects.create(
            nombre='Doble',
            capacidad=2,
            precio_base=150,
        )
        habitacion = Habitacion.objects.create(
            hotel=hotel,
            tipo=tipo,
            numero='201',
            piso=2,
        )
        huesped = Huesped.objects.create(
            tipo_doc='DNI',
            num_doc='12345678',
            nombres='Ana',
            apellidos='Torres',
            fecha_nacimiento=date(1991, 5, 20),
        )
        reserva = Reserva.objects.create(
            hotel=hotel,
            huesped=huesped,
            habitacion=habitacion,
            fecha_entrada=date(2026, 6, 1),
            fecha_salida=date(2026, 6, 3),
            precio_total=Decimal('300.00'),
        )
        estancia = Estancia.objects.create(
            reserva=reserva,
            habitacion=habitacion,
            fecha_checkin=timezone.now(),
            precio_final=Decimal('300.00'),
        )
        CargoEstancia.objects.create(
            estancia=estancia,
            concepto='Minibar',
            monto=Decimal('50.00'),
            tipo=TipoCargo.MINIBAR,
        )
        folio = Folio.objects.create(estancia=estancia)

        total = folio.calcular_totales()

        self.assertEqual(folio.subtotal, Decimal('350.00'))
        self.assertEqual(folio.igv, Decimal('63.0000'))
        self.assertEqual(total, Decimal('413.0000'))
