from datetime import date
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from config.choices import EstadoReserva, OrigenReserva
from core.models import ModeloBase
from habitaciones.models import Habitacion
from hoteles.models import Hotel
from huespedes.models import Huesped


class Reserva(ModeloBase):
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        related_name='reservas',
    )
    huesped = models.ForeignKey(
        Huesped,
        on_delete=models.PROTECT,
        related_name='reservas',
    )
    habitacion = models.ForeignKey(
        Habitacion,
        on_delete=models.PROTECT,
        related_name='reservas',
    )
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    num_adultos = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20,
        choices=EstadoReserva.choices,
        default=EstadoReserva.PENDIENTE,
    )
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenReserva.choices,
        default=OrigenReserva.RECEPCION,
    )

    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha_entrada']

    def __str__(self):
        return f'{self.codigo or f"Reserva #{self.id}"} - {self.huesped}'

    @property
    def noches(self):
        return (self.fecha_salida - self.fecha_entrada).days

    @property
    def es_modificable(self):
        return self.estado not in [
            EstadoReserva.CHECKIN,
            EstadoReserva.FINALIZADA,
            EstadoReserva.CANCELADA,
        ]

    def clean(self):
        errors = {}

        if self.fecha_entrada and self.fecha_salida:
            if self.fecha_salida <= self.fecha_entrada:
                errors['fecha_salida'] = 'La fecha de salida debe ser mayor a la fecha de entrada.'

        if not self.pk and self.fecha_entrada and self.fecha_entrada < date.today():
            errors['fecha_entrada'] = 'La fecha de entrada no puede ser anterior a hoy.'

        if self.num_adultos is not None and self.num_adultos < 1:
            errors['num_adultos'] = 'Debe registrar al menos un adulto.'

        if self.habitacion_id and not self.hotel_id:
            self.hotel = self.habitacion.hotel

        if self.habitacion_id and self.num_adultos and self.num_adultos > self.habitacion.tipo.capacidad:
            errors['num_adultos'] = 'La cantidad de adultos supera la capacidad del tipo de habitacion.'

        if self.hotel_id and self.habitacion_id and self.habitacion.hotel_id != self.hotel_id:
            errors['habitacion'] = 'La habitacion no pertenece al hotel seleccionado.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.habitacion_id and not self.hotel_id:
            self.hotel = self.habitacion.hotel
        if not self.codigo:
            self.codigo = self._generar_codigo()
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def _generar_codigo(cls):
        prefijo = f'RSV-{date.today():%Y%m%d}'
        for _ in range(8):
            codigo = f'{prefijo}-{uuid4().hex[:4].upper()}'
            if not cls.todos.filter(codigo=codigo).exists():
                return codigo
        return f'{prefijo}-{uuid4().hex[:8].upper()}'
