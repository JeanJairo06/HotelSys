from django.db import models


class Hotel(models.Model):
    nombre = models.CharField(max_length=150)
    ruc = models.CharField(max_length=11, unique=True)
    direccion = models.TextField()
    estrellas = models.PositiveSmallIntegerField()
    telefono = models.CharField(max_length=20)

    class Meta:
        db_table = 'hoteles'
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hoteles'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre