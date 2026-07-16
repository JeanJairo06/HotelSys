from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from config.choices import EstadoHabitacion, EstadoReserva
from cuentas.roles import ROLE_RECEPCIONISTA
from estancias.services import registrar_checkin
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.models import Reserva


class EstanciasAPITests(TestCase):
    def setUp(self):
        grupo, _ = Group.objects.get_or_create(name=ROLE_RECEPCIONISTA)
        self.usuario = User.objects.create_user(username='recepcion', password='testpass123')
        self.usuario.groups.add(grupo)
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)

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
            fecha_nacimiento=date(1990, 1, 1),
        )

    def _crear_estancia_con_folio_pendiente(self):
        hoy = timezone.localdate()
        reserva = Reserva.objects.create(
            hotel=self.hotel,
            huesped=self.huesped,
            habitacion=self.habitacion,
            fecha_entrada=hoy,
            fecha_salida=hoy + timedelta(days=1),
            estado=EstadoReserva.CONFIRMADA,
            precio_total=Decimal('120.00'),
        )
        return registrar_checkin(reserva)

    def test_checkout_api_devuelve_error_estandar_con_saldo_pendiente(self):
        estancia = self._crear_estancia_con_folio_pendiente()

        response = self.client.post(f'/api/v1/estancias/{estancia.id}/checkout/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'CHECKOUT_BLOQUEADO')
        self.assertEqual(response.data['message'], 'No se puede hacer checkout. Saldo pendiente: S/ 141.60.')
