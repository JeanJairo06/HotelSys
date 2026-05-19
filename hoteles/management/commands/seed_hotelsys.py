from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from config.choices import (
    EstadoHabitacion,
    EstadoReserva,
    OrigenReserva,
)

from hoteles.models import Hotel
from habitaciones.models import TipoHabitacion, Habitacion, Tarifa
from huespedes.models import Huesped
from reservas.models import Reserva


class Command(BaseCommand):
    help = 'Carga datos iniciales para HotelSys'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Creando datos iniciales...'))

        hotel, _ = Hotel.objects.get_or_create(
            ruc='20481234567',
            defaults={
                'nombre': 'HotelSys Palace',
                'direccion': 'Av. Principal 123 - Chiclayo',
                'estrellas': 4,
                'telefono': '074-555555',
            }
        )

        simple, _ = TipoHabitacion.objects.get_or_create(
            nombre='Simple',
            defaults={
                'capacidad': 1,
                'precio_base': Decimal('120.00'),
                'amenidades': {
                    'wifi': True,
                    'tv': True,
                    'aire_acondicionado': False,
                }
            }
        )

        doble, _ = TipoHabitacion.objects.get_or_create(
            nombre='Doble',
            defaults={
                'capacidad': 2,
                'precio_base': Decimal('180.00'),
                'amenidades': {
                    'wifi': True,
                    'tv': True,
                    'aire_acondicionado': True,
                }
            }
        )

        suite, _ = TipoHabitacion.objects.get_or_create(
            nombre='Suite',
            defaults={
                'capacidad': 4,
                'precio_base': Decimal('320.00'),
                'amenidades': {
                    'wifi': True,
                    'tv': True,
                    'aire_acondicionado': True,
                    'jacuzzi': True,
                    'minibar': True,
                }
            }
        )

        habitaciones_data = [
            ('101', 1, simple, EstadoHabitacion.DISPONIBLE),
            ('102', 1, simple, EstadoHabitacion.DISPONIBLE),
            ('103', 1, doble, EstadoHabitacion.LIMPIEZA),
            ('104', 1, doble, EstadoHabitacion.MANTENIMIENTO),
            ('201', 2, doble, EstadoHabitacion.DISPONIBLE),
            ('202', 2, doble, EstadoHabitacion.DISPONIBLE),
            ('203', 2, suite, EstadoHabitacion.DISPONIBLE),
            ('204', 2, suite, EstadoHabitacion.OCUPADA),
            ('301', 3, simple, EstadoHabitacion.DISPONIBLE),
            ('302', 3, suite, EstadoHabitacion.DISPONIBLE),
        ]

        habitaciones = []

        for numero, piso, tipo, estado in habitaciones_data:
            habitacion, _ = Habitacion.objects.get_or_create(
                hotel=hotel,
                numero=numero,
                defaults={
                    'tipo': tipo,
                    'piso': piso,
                    'estado': estado,
                }
            )
            habitaciones.append(habitacion)

        hoy = timezone.now().date()

        inicio_temporada_alta = date(hoy.year, 12, 1)
        fin_temporada_regular = inicio_temporada_alta - timedelta(days=1)

        tarifas_data = [
            (simple, 'Tarifa Regular Simple', Decimal('120.00'), hoy, fin_temporada_regular),
            (doble, 'Tarifa Regular Doble', Decimal('180.00'), hoy, fin_temporada_regular),
            (suite, 'Tarifa Regular Suite', Decimal('320.00'), hoy, fin_temporada_regular),
            (simple, 'Temporada Alta Simple', Decimal('160.00'), inicio_temporada_alta, date(hoy.year, 12, 31)),
            (doble, 'Temporada Alta Doble', Decimal('230.00'), inicio_temporada_alta, date(hoy.year, 12, 31)),
            (suite, 'Temporada Alta Suite', Decimal('420.00'), inicio_temporada_alta, date(hoy.year, 12, 31)),
        ]

        for tipo, nombre, precio, inicio, fin in tarifas_data:
            Tarifa.objects.get_or_create(
                tipo_habitacion=tipo,
                nombre=nombre,
                fecha_inicio=inicio,
                fecha_fin=fin,
                defaults={
                    'precio_noche': precio,
                }
            )

        huespedes_data = [
            ('DNI', '71234567', 'Carlos', 'Ramírez Torres', 'carlos@mail.com', '987654321', 'Peruana'),
            ('DNI', '72345678', 'Ana', 'Flores Díaz', 'ana@mail.com', '912345678', 'Peruana'),
            ('DNI', '73456789', 'Luis', 'Mendoza Cruz', 'luis@mail.com', '923456789', 'Peruana'),
            ('PASAPORTE', 'P1234567', 'John', 'Smith', 'john@mail.com', '934567890', 'Estadounidense'),
            ('CARNET_EXTRANJERIA', 'CE987654', 'María', 'Gómez Pérez', 'maria@mail.com', '945678901', 'Colombiana'),
        ]

        huespedes = []

        for tipo_doc, num_doc, nombres, apellidos, email, telefono, nacionalidad in huespedes_data:
            huesped, _ = Huesped.objects.get_or_create(
                num_doc=num_doc,
                defaults={
                    'tipo_doc': tipo_doc,
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'telefono': telefono,
                    'nacionalidad': nacionalidad,
                }
            )
            huespedes.append(huesped)

        Reserva.objects.get_or_create(
            hotel=hotel,
            huesped=huespedes[0],
            habitacion=habitaciones[0],
            fecha_entrada=hoy + timedelta(days=1),
            fecha_salida=hoy + timedelta(days=3),
            defaults={
                'num_adultos': 1,
                'estado': EstadoReserva.CONFIRMADA,
                'precio_total': Decimal('240.00'),
                'origen': OrigenReserva.RECEPCION,
            }
        )

        Reserva.objects.get_or_create(
            hotel=hotel,
            huesped=huespedes[1],
            habitacion=habitaciones[4],
            fecha_entrada=hoy + timedelta(days=2),
            fecha_salida=hoy + timedelta(days=5),
            defaults={
                'num_adultos': 2,
                'estado': EstadoReserva.PENDIENTE,
                'precio_total': Decimal('540.00'),
                'origen': OrigenReserva.WEB,
            }
        )

        self.stdout.write(self.style.SUCCESS('Datos iniciales creados correctamente.'))
