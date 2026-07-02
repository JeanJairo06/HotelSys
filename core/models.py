from django.conf import settings
from django.db import models


class ActivosQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)

    def inactivos(self):
        return self.filter(activo=False)


class ManagerActivos(models.Manager):
    def get_queryset(self):
        return ActivosQuerySet(self.model, using=self._db).activos()


class ModeloBase(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='%(app_label)s_%(class)s_creados',
    )
    activo = models.BooleanField(default=True)

    objects = ManagerActivos()
    todos = models.Manager()

    class Meta:
        abstract = True

    def eliminar(self, *, usuario=None):
        self.activo = False
        self.save(update_fields=['activo', 'actualizado_en'])
        return self
