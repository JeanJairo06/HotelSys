from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date

from hoteles.models import Hotel
from habitaciones.forms import TipoHabitacionForm
from habitaciones.models import TipoHabitacion, Tarifa
from habitaciones.services import guardar_tipo_habitacion_desde_formulario


class TipoHabitacionServiceTests(TestCase):
    def test_guardar_tipo_habitacion_desde_formulario(self):
        form = TipoHabitacionForm(data={
            'nombre': 'Simple',
            'capacidad': 1,
            'precio_base': '120.00',
            'amenidades': [],
        })

        self.assertTrue(form.is_valid())
        tipo = guardar_tipo_habitacion_desde_formulario(form)

        self.assertEqual(TipoHabitacion.objects.count(), 1)
        self.assertEqual(tipo.nombre, 'Simple')


class TarifaModelTests(TestCase):
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
            precio_base=200,
        )

    def test_rechaza_tarifa_con_fechas_invalidas(self):
        tarifa = Tarifa(
            tipo_habitacion=self.tipo,
            nombre='Temporada inválida',
            precio_noche=250,
            fecha_inicio=date(2026, 5, 10),
            fecha_fin=date(2026, 5, 9),
        )

        with self.assertRaises(ValidationError):
            tarifa.full_clean()

    def test_rechaza_tarifas_solapadas_por_tipo_habitacion(self):
        Tarifa.objects.create(
            tipo_habitacion=self.tipo,
            nombre='Temporada alta',
            precio_noche=300,
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 31),
        )

        tarifa_solapada = Tarifa(
            tipo_habitacion=self.tipo,
            nombre='Promoción julio',
            precio_noche=280,
            fecha_inicio=date(2026, 7, 15),
            fecha_fin=date(2026, 8, 15),
        )

        with self.assertRaises(ValidationError):
            tarifa_solapada.full_clean()
