from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from config.choices import EstadoReserva, OrigenReserva
from hoteles.models import Hotel
from habitaciones.models import Habitacion
from huespedes.models import Huesped


class Reserva(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        related_name='reservas'
    )
    huesped = models.ForeignKey(
        Huesped,
        on_delete=models.PROTECT,
        related_name='reservas'
    )
    habitacion = models.ForeignKey(
        Habitacion,
        on_delete=models.PROTECT,
        related_name='reservas'
    )
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    num_adultos = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20,
        choices=EstadoReserva.choices,
        default=EstadoReserva.PENDIENTE
    )
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenReserva.choices,
        default=OrigenReserva.RECEPCION
    )

    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha_entrada']

    def __str__(self):
        return f'Reserva #{self.id} - {self.huesped}'

    @property
    def noches(self):
        return (self.fecha_salida - self.fecha_entrada).days

    def clean(self):
        errors = {}

        if self.fecha_entrada and self.fecha_salida:
            if self.fecha_salida <= self.fecha_entrada:
                errors['fecha_salida'] = 'La fecha de salida debe ser mayor a la fecha de entrada.'

        if self.hotel_id and self.habitacion_id:
            if self.habitacion.hotel_id != self.hotel_id:
                errors['habitacion'] = 'La habitación no pertenece al hotel seleccionado.'

        if self.habitacion_id and self.fecha_entrada and self.fecha_salida:
            reservas_solapadas = Reserva.objects.filter(
                habitacion=self.habitacion,
                fecha_entrada__lt=self.fecha_salida,
                fecha_salida__gt=self.fecha_entrada,
            ).exclude(pk=self.pk).exclude(
                estado__in=[
                    EstadoReserva.CANCELADA,
                    EstadoReserva.FINALIZADA,
                ]
            )

            if reservas_solapadas.exists():
                errors['habitacion'] = 'La habitación ya tiene una reserva activa en ese rango de fechas.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)