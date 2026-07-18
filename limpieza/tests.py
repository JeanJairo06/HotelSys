from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from config.choices import EstadoEstancia, EstadoHabitacion, EstadoReserva
from core.events import EVENTO_HABITACION_DISPONIBLE, EVENTO_HABITACION_EN_MANTENIMIENTO
from estancias.models import Estancia
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from limpieza.services import marcar_disponible, marcar_mantenimiento
from limpieza.exceptions import HousekeepingTransicionInvalida
from reservas.models import Reserva


class HousekeepingServiceTests(TestCase):
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
            estado=EstadoHabitacion.LIMPIEZA,
        )

    def test_marcar_disponible_solo_permite_limpieza_o_mantenimiento(self):
        self.habitacion.estado = EstadoHabitacion.DISPONIBLE
        self.habitacion.save(update_fields=['estado'])

        with self.assertRaisesMessage(HousekeepingTransicionInvalida, 'Solo se pueden liberar habitaciones en limpieza o mantenimiento.'):
            marcar_disponible(self.habitacion)

    @patch('habitaciones.services.publicar_evento_habitacion')
    def test_marcar_disponible_libera_habitacion_en_mantenimiento_y_publica_evento(self, publicar_evento):
        self.habitacion.estado = EstadoHabitacion.MANTENIMIENTO
        self.habitacion.save(update_fields=['estado'])

        marcar_disponible(self.habitacion)

        self.habitacion.refresh_from_db()
        self.assertEqual(self.habitacion.estado, EstadoHabitacion.DISPONIBLE)
        publicar_evento.assert_called_once_with(
            self.habitacion,
            estado_anterior=EstadoHabitacion.MANTENIMIENTO,
            evento=EVENTO_HABITACION_DISPONIBLE,
        )

    @patch('habitaciones.services.publicar_evento_habitacion')
    def test_marcar_disponible_libera_habitacion_en_limpieza_y_publica_evento(self, publicar_evento):
        marcar_disponible(self.habitacion)

        self.habitacion.refresh_from_db()
        self.assertEqual(self.habitacion.estado, EstadoHabitacion.DISPONIBLE)
        publicar_evento.assert_called_once_with(
            self.habitacion,
            estado_anterior=EstadoHabitacion.LIMPIEZA,
            evento=EVENTO_HABITACION_DISPONIBLE,
        )

    def test_marcar_disponible_bloquea_habitacion_con_estancia_activa(self):
        estancia = self._crear_estancia_activa()
        self.habitacion.estado = EstadoHabitacion.LIMPIEZA
        self.habitacion.save(update_fields=['estado'])

        with self.assertRaisesMessage(HousekeepingTransicionInvalida, 'No se puede liberar una habitacion con estancia activa.'):
            marcar_disponible(self.habitacion)

        estancia.refresh_from_db()
        self.assertEqual(estancia.estado, EstadoEstancia.ACTIVA)

    @patch('habitaciones.services.publicar_evento_habitacion')
    def test_marcar_mantenimiento_publica_evento(self, publicar_evento):
        marcar_mantenimiento(self.habitacion)

        self.habitacion.refresh_from_db()
        self.assertEqual(self.habitacion.estado, EstadoHabitacion.MANTENIMIENTO)
        publicar_evento.assert_called_once_with(
            self.habitacion,
            estado_anterior=EstadoHabitacion.LIMPIEZA,
            evento=EVENTO_HABITACION_EN_MANTENIMIENTO,
        )

    def _crear_estancia_activa(self):
        huesped = Huesped.objects.create(
            tipo_doc='DNI',
            num_doc='12345678',
            nombres='Ana',
            apellidos='Torres',
            fecha_nacimiento=date(1990, 1, 1),
        )
        hoy = timezone.localdate()
        reserva = Reserva.objects.create(
            hotel=self.hotel,
            huesped=huesped,
            habitacion=self.habitacion,
            fecha_entrada=hoy,
            fecha_salida=hoy + timedelta(days=1),
            estado=EstadoReserva.CHECKIN,
            precio_total=Decimal('120.00'),
        )
        return Estancia.objects.create(
            reserva=reserva,
            habitacion=self.habitacion,
            fecha_checkin=timezone.now(),
            precio_final=Decimal('120.00'),
            estado=EstadoEstancia.ACTIVA,
        )
