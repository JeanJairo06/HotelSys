from django.db import models

from config.choices import TipoDocumento
from core.models import ModeloBase
from huespedes.services import normalizar_datos_huesped, validar_datos_huesped


class Huesped(ModeloBase):
    tipo_doc = models.CharField(
        max_length=30,
        choices=TipoDocumento.choices,
        default=TipoDocumento.DNI,
    )
    num_doc = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100, blank=True)
    apellidos = models.CharField(max_length=100, blank=True)
    razon_social = models.CharField(max_length=200, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    nacionalidad = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        db_table = 'huespedes'
        verbose_name = 'Huesped'
        verbose_name_plural = 'Huespedes'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.num_doc} - {self.nombre_completo}'

    @property
    def nombre_completo(self):
        if self.tipo_doc == TipoDocumento.RUC and self.razon_social:
            return self.razon_social

        return f'{self.nombres} {self.apellidos}'.strip()

    def clean(self):
        datos = normalizar_datos_huesped({
            'tipo_doc': self.tipo_doc,
            'num_doc': self.num_doc,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'razon_social': self.razon_social,
            'fecha_nacimiento': self.fecha_nacimiento,
            'email': self.email,
            'telefono': self.telefono,
            'nacionalidad': self.nacionalidad,
        })
        for campo, valor in datos.items():
            setattr(self, campo, valor)
        validar_datos_huesped(datos, huesped_id=self.pk)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
