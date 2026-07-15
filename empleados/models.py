from datetime import date
import re

from django.core.exceptions import ValidationError
from django.db import models

from config.choices import CargoEmpleado, EstadoGeneral
from core.models import ModeloBase


class Empleado(ModeloBase):
    CODIGO_PREFIX = 'EMP-'

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

    @classmethod
    def generar_codigo(cls):
        ultimo_numero = 0
        patron = re.compile(rf'{re.escape(cls.CODIGO_PREFIX)}(\d+)$')

        for codigo in cls.objects.filter(codigo__startswith=cls.CODIGO_PREFIX).values_list('codigo', flat=True):
            match = patron.fullmatch(codigo)
            if match:
                ultimo_numero = max(ultimo_numero, int(match.group(1)))

        return f'{cls.CODIGO_PREFIX}{ultimo_numero + 1:04d}'

    def clean(self):
        errors = {}

        if self.codigo:
            self.codigo = self.codigo.strip().upper()

        if self.nombres:
            self.nombres = self.nombres.strip()

        if self.apellidos:
            self.apellidos = self.apellidos.strip()

        if self.email:
            self.email = self.email.strip().lower()

        if self.telefono:
            self.telefono = self.telefono.strip()

        if self.telefono:
            telefono_limpio = self.telefono.replace('+', '').replace('-', '').replace(' ', '')

            if not telefono_limpio.isdigit():
                errors['telefono'] = 'El telefono solo debe contener numeros, espacios, + o -.'

            elif len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
                errors['telefono'] = 'El telefono debe tener entre 7 y 15 digitos.'

        if self.fecha_ingreso and self.fecha_ingreso > date.today():
            errors['fecha_ingreso'] = 'La fecha de ingreso no puede ser futura.'

        if self.email:
            existe_email = Empleado.objects.filter(email=self.email)

            if self.pk:
                existe_email = existe_email.exclude(pk=self.pk)

            if existe_email.exists():
                errors['email'] = 'Este correo ya esta registrado.'

        if self.telefono:
            existe_telefono = Empleado.objects.filter(telefono=self.telefono)

            if self.pk:
                existe_telefono = existe_telefono.exclude(pk=self.pk)

            if existe_telefono.exists():
                errors['telefono'] = 'Este telefono ya esta registrado.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()

        self.full_clean()
        super().save(*args, **kwargs)
