from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from config.choices import EstadoEstancia, EstadoReserva
from hoteles.models import Hotel
from habitaciones.models import Habitacion, TipoHabitacion
from huespedes.exceptions import HuespedDuplicado
from huespedes.models import Huesped
from huespedes.services import (
    crear_huesped,
    eliminar_huesped,
    estancia_actual_huesped,
    historial_huesped,
)
from reservas.models import Reserva
from estancias.models import Estancia


class HuespedServiceTests(TestCase):
    def test_crear_huesped_normaliza_y_valida_documento(self):
        huesped = crear_huesped(
            tipo_doc='DNI',
            num_doc=' 12345678 ',
            nombres=' Ana ',
            apellidos=' Torres ',
            fecha_nacimiento=date(1990, 1, 1),
            email='ANA@CORREO.COM',
            telefono='999 888 777',
            nacionalidad=' Peru ',
        )

        self.assertEqual(huesped.num_doc, '12345678')
        self.assertEqual(huesped.nombres, 'Ana')
        self.assertEqual(huesped.email, 'ana@correo.com')

    def test_no_permite_documento_duplicado(self):
        datos = {
            'tipo_doc': 'DNI',
            'num_doc': '12345678',
            'nombres': 'Ana',
            'apellidos': 'Torres',
            'fecha_nacimiento': date(1990, 1, 1),
        }
        crear_huesped(**datos)

        with self.assertRaises(HuespedDuplicado):
            crear_huesped(**datos)

    def test_eliminar_huesped_es_soft_delete(self):
        huesped = crear_huesped(
            tipo_doc='DNI',
            num_doc='12345678',
            nombres='Ana',
            apellidos='Torres',
            fecha_nacimiento=date(1990, 1, 1),
        )

        eliminar_huesped(huesped)

        self.assertFalse(Huesped.objects.filter(pk=huesped.pk).exists())
        self.assertTrue(Huesped.todos.filter(pk=huesped.pk, activo=False).exists())

    def test_historial_y_estancia_actual(self):
        huesped = crear_huesped(
            tipo_doc='DNI',
            num_doc='12345678',
            nombres='Ana',
            apellidos='Torres',
            fecha_nacimiento=date(1990, 1, 1),
        )
        hotel = Hotel.objects.create(
            nombre='Hotel Central',
            ruc='12345678901',
            direccion='Av. Principal 123',
            estrellas=3,
            telefono='999999999',
        )
        tipo = TipoHabitacion.objects.create(
            nombre='Simple',
            capacidad=2,
            precio_base=Decimal('120.00'),
        )
        habitacion = Habitacion.objects.create(
            hotel=hotel,
            tipo=tipo,
            numero='101',
            piso=1,
        )
        reserva = Reserva.todos.create(
            hotel=hotel,
            huesped=huesped,
            habitacion=habitacion,
            fecha_entrada=date.today(),
            fecha_salida=date.today() + timedelta(days=2),
            num_adultos=1,
            estado=EstadoReserva.CHECKIN,
            precio_total=Decimal('240.00'),
        )
        estancia = Estancia.objects.create(
            reserva=reserva,
            habitacion=habitacion,
            fecha_checkin=timezone.now(),
            precio_final=Decimal('240.00'),
            estado=EstadoEstancia.ACTIVA,
        )

        self.assertEqual(list(historial_huesped(huesped)), [reserva])
        self.assertEqual(estancia_actual_huesped(huesped), estancia)
