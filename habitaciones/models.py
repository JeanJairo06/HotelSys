from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from config.choices import EstadoHabitacion
from hoteles.models import Hotel


class TipoHabitacion(models.Model):
    nombre = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amenidades = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tipos_habitacion'
        verbose_name = 'Tipo de Habitación'
        verbose_name_plural = 'Tipos de Habitación'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def amenidades_lista(self):
        """Devuelve amenidades como lista legible sin exponer el JSON crudo."""
        if isinstance(self.amenidades, list):
            return [self._normalizar_amenidad(amenidad) for amenidad in self.amenidades if amenidad]
        if isinstance(self.amenidades, dict):
            return [
                self._normalizar_amenidad(clave)
                for clave, activo in self.amenidades.items()
                if activo
            ]
        if isinstance(self.amenidades, str) and self.amenidades.strip():
            return [self._normalizar_amenidad(self.amenidades)]
        return []

    @staticmethod
    def _normalizar_amenidad(amenidad):
        texto = str(amenidad).replace('_', ' ').strip()
        especiales = {
            'tv': 'TV',
            'wifi': 'Wifi',
            'wi fi': 'Wifi',
        }
        return especiales.get(texto.lower(), texto.capitalize())


class Habitacion(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        related_name='habitaciones'
    )
    tipo = models.ForeignKey(
        TipoHabitacion,
        on_delete=models.PROTECT,
        related_name='habitaciones'
    )
    numero = models.CharField(max_length=10)
    piso = models.PositiveSmallIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoHabitacion.choices,
        default=EstadoHabitacion.DISPONIBLE
    )

    class Meta:
        db_table = 'habitaciones'
        verbose_name = 'Habitación'
        verbose_name_plural = 'Habitaciones'
        ordering = ['hotel', 'piso', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['hotel', 'numero'],
                name='unique_habitacion_por_hotel'
            )
        ]

    def __str__(self):
        return f'{self.hotel.nombre} - Hab. {self.numero}'


class Tarifa(models.Model):
    tipo_habitacion = models.ForeignKey(
        TipoHabitacion,
        on_delete=models.PROTECT,
        related_name='tarifas'
    )
    nombre = models.CharField(max_length=100)
    precio_noche = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        db_table = 'tarifas'
        verbose_name = 'Tarifa'
        verbose_name_plural = 'Tarifas'
        ordering = ['tipo_habitacion', 'fecha_inicio']

    def __str__(self):
        return f'{self.nombre} - {self.tipo_habitacion.nombre}'

    def clean(self):
        errors = {}

        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                errors['fecha_fin'] = 'La fecha final debe ser mayor o igual a la fecha inicial.'

        if self.tipo_habitacion_id and self.fecha_inicio and self.fecha_fin:
            tarifas_solapadas = Tarifa.objects.filter(
                tipo_habitacion=self.tipo_habitacion,
                fecha_inicio__lte=self.fecha_fin,
                fecha_fin__gte=self.fecha_inicio,
            ).exclude(pk=self.pk)

            if tarifas_solapadas.exists():
                errors['fecha_inicio'] = 'Ya existe una tarifa vigente para ese tipo de habitación en ese rango.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
