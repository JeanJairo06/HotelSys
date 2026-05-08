from django.db import models
from django.core.validators import MinValueValidator
from config.choices import EstadoEstancia, TipoCargo
from habitaciones.models import Habitacion
from reservas.models import Reserva


class Estancia(models.Model):
    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.PROTECT,
        related_name='estancia'
    )
    habitacion = models.ForeignKey(
        Habitacion,
        on_delete=models.PROTECT,
        related_name='estancias'
    )
    fecha_checkin = models.DateTimeField()
    fecha_checkout = models.DateTimeField(blank=True, null=True)
    precio_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoEstancia.choices,
        default=EstadoEstancia.ACTIVA
    )

    class Meta:
        db_table = 'estancias'
        verbose_name = 'Estancia'
        verbose_name_plural = 'Estancias'
        ordering = ['-fecha_checkin']

    def __str__(self):
        return f'Estancia #{self.id} - {self.reserva.huesped}'


class CargoEstancia(models.Model):
    estancia = models.ForeignKey(
        Estancia,
        on_delete=models.CASCADE,
        related_name='cargos'
    )
    concepto = models.CharField(max_length=150)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(
        max_length=30,
        choices=TipoCargo.choices,
        default=TipoCargo.OTRO
    )

    class Meta:
        db_table = 'cargos_estancia'
        verbose_name = 'Cargo de Estancia'
        verbose_name_plural = 'Cargos de Estancia'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.concepto} - S/ {self.monto}'