from django.db import models
from config.choices import TipoDocumento


class Huesped(models.Model):
    tipo_doc = models.CharField(
        max_length=30,
        choices=TipoDocumento.choices,
        default=TipoDocumento.DNI
    )
    num_doc = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    nacionalidad = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        db_table = 'huespedes'
        verbose_name = 'Huésped'
        verbose_name_plural = 'Huéspedes'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.apellidos}, {self.nombres}'