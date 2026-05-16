from django.core.exceptions import ValidationError
from django.db import models

from config.choices import CargoEmpleado, EstadoGeneral


class Empleado(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cargo = models.CharField(
        max_length=30,
        choices=CargoEmpleado.choices,
        default=CargoEmpleado.RECEPCIONISTA,
    )
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    estado = models.IntegerField(
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO,
    )
    fecha_ingreso = models.DateField()

    class Meta:
        db_table = 'empleados'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.codigo} - {self.nombre_completo}'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.strip().upper()

        if self.telefono:
            telefono_limpio = self.telefono.replace('+', '').replace('-', '').replace(' ', '')
            if not telefono_limpio.isdigit():
                raise ValidationError({'telefono': 'El teléfono solo debe contener números, espacios, + o -.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
