from django.core.exceptions import ValidationError
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
        return f'{self.num_doc} - {self.nombre_completo}'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    def clean(self):
        if self.num_doc:
            self.num_doc = self.num_doc.strip().upper()

        if self.telefono:
            telefono_limpio = self.telefono.replace('+', '').replace('-', '').replace(' ', '')
            if not telefono_limpio.isdigit():
                raise ValidationError({'telefono': 'El telefono solo debe contener numeros, espacios, + o -.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
