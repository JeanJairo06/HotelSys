from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from config.choices import EstadoReserva, OrigenReserva
from habitaciones.models import Habitacion, Tarifa, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.forms import ReservaForm
from reservas.services import calcular_precio_total_reserva


class CalculoPrecioReservaTests(TestCase):
    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre='Hotel Central',
            ruc='12345678901',
            direccion='Av. Principal 123',
            estrellas=4,
            telefono='999999999',
        )
        self.tipo = TipoHabitacion.objects.create(
            nombre='Suite',
            capacidad=2,
            precio_base=Decimal('200.00'),
        )
        self.habitacion = Habitacion.objects.create(
            hotel=self.hotel,
            tipo=self.tipo,
            numero='101',
            piso=1,
        )
        self.huesped = Huesped.objects.create(
            num_doc='71234567',
            nombres='Carlos',
            apellidos='Ramirez',
            fecha_nacimiento=date(1990, 1, 1),
        )

    def test_calcula_total_con_precio_base_si_no_hay_tarifa(self):
        total = calcular_precio_total_reserva(
            self.tipo,
            date(2026, 6, 1),
            date(2026, 6, 4),
        )

        self.assertEqual(total, Decimal('600.00'))

    def test_calcula_total_con_tarifa_de_temporada_completa(self):
        Tarifa.objects.create(
            tipo_habitacion=self.tipo,
            nombre='Temporada alta',
            precio_noche=Decimal('250.00'),
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 31),
        )

        total = calcular_precio_total_reserva(
            self.tipo,
            date(2026, 7, 10),
            date(2026, 7, 13),
        )

        self.assertEqual(total, Decimal('750.00'))

    def test_calcula_total_con_tarifa_parcial_y_no_cobra_fecha_salida(self):
        Tarifa.objects.create(
            tipo_habitacion=self.tipo,
            nombre='Fin de semana',
            precio_noche=Decimal('300.00'),
            fecha_inicio=date(2026, 8, 11),
            fecha_fin=date(2026, 8, 12),
        )

        total = calcular_precio_total_reserva(
            self.tipo,
            date(2026, 8, 10),
            date(2026, 8, 13),
        )

        self.assertEqual(total, Decimal('800.00'))

    def test_form_asigna_total_calculado_con_tarifa(self):
        hoy = timezone.localdate()
        fecha_entrada = hoy + timedelta(days=5)
        fecha_salida = hoy + timedelta(days=7)
        Tarifa.objects.create(
            tipo_habitacion=self.tipo,
            nombre='Temporada alta',
            precio_noche=Decimal('250.00'),
            fecha_inicio=hoy + timedelta(days=1),
            fecha_fin=hoy + timedelta(days=31),
        )
        form = ReservaForm(data={
            'hotel': self.hotel.id,
            'huesped': self.huesped.id,
            'tipo_habitacion': self.tipo.id,
            'habitacion': self.habitacion.id,
            'fecha_entrada': fecha_entrada.isoformat(),
            'fecha_salida': fecha_salida.isoformat(),
            'num_adultos': 2,
            'origen': OrigenReserva.RECEPCION,
            'estado': EstadoReserva.PENDIENTE,
            'precio_total': '',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['precio_total'], Decimal('500.00'))
