from datetime import date

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
    nombres = models.CharField(max_length=100, blank=True)
    apellidos = models.CharField(max_length=100, blank=True)
    razon_social = models.CharField(max_length=200, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
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
        if self.tipo_doc == TipoDocumento.RUC and self.razon_social:
            return self.razon_social

        return f'{self.nombres} {self.apellidos}'

    def clean(self):
        errors = {}

        # Normalización
        if self.num_doc:
            self.num_doc = self.num_doc.strip().upper().replace(' ', '')

        if self.nombres:
            self.nombres = self.nombres.strip()

        if self.apellidos:
            self.apellidos = self.apellidos.strip()

        if self.razon_social:
            self.razon_social = self.razon_social.strip()

        if self.email:
            self.email = self.email.strip().lower()

        if self.nacionalidad:
            self.nacionalidad = self.nacionalidad.strip()

        # Validar teléfono
        if self.telefono:
            telefono_limpio = (
                self.telefono
                .replace('+', '')
                .replace('-', '')
                .replace(' ', '')
            )

            if not telefono_limpio.isdigit():
                errors['telefono'] = (
                    'El telefono solo debe contener numeros, espacios, + o -.'
                )

            elif len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
                errors['telefono'] = (
                    'El telefono debe tener entre 7 y 15 digitos.'
                )

        # Validaciones por tipo de documento
        if self.tipo_doc == TipoDocumento.RUC:

            if not self.num_doc or not self.num_doc.isdigit():
                errors['num_doc'] = 'El RUC debe contener solo numeros.'

            elif len(self.num_doc) != 11:
                errors['num_doc'] = (
                    'El RUC debe tener exactamente 11 digitos.'
                )

            if not self.razon_social:
                errors['razon_social'] = (
                    'La razon social es obligatoria para RUC.'
                )

        if self.tipo_doc == TipoDocumento.DNI:

            if not self.num_doc or not self.num_doc.isdigit():
                errors['num_doc'] = 'El DNI debe contener solo numeros.'

            elif len(self.num_doc) != 8:
                errors['num_doc'] = (
                    'El DNI debe tener exactamente 8 digitos.'
                )

            if not self.nombres:
                errors['nombres'] = (
                    'Los nombres son obligatorios para DNI.'
                )

            if not self.apellidos:
                errors['apellidos'] = (
                    'Los apellidos son obligatorios para DNI.'
                )

            if not self.fecha_nacimiento:
                errors['fecha_nacimiento'] = (
                    'La fecha de nacimiento es obligatoria para DNI.'
                )

        # Fecha válida
        if self.fecha_nacimiento and self.fecha_nacimiento >= date.today():
            errors['fecha_nacimiento'] = (
                'La fecha de nacimiento debe ser anterior a hoy.'
            )

        if self.fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - self.fecha_nacimiento.year

            if (hoy.month, hoy.day) < (
                self.fecha_nacimiento.month,
                self.fecha_nacimiento.day,
            ):
                edad -= 1

            if edad < 18:
                errors['fecha_nacimiento'] = (
                    'El huesped debe ser mayor de 18 años.'
                )

        # Validar email único
        if self.email:
            existe_email = Huesped.objects.filter(email=self.email)

            if self.pk:
                existe_email = existe_email.exclude(pk=self.pk)

            if existe_email.exists():
                errors['email'] = 'Este correo ya esta registrado.'

        # Validar teléfono único
        if self.telefono:
            existe_telefono = Huesped.objects.filter(
                telefono=self.telefono
            )

            if self.pk:
                existe_telefono = existe_telefono.exclude(pk=self.pk)

            if existe_telefono.exists():
                errors['telefono'] = (
                    'Este telefono ya esta registrado.'
                )

        # Lanzar errores
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
