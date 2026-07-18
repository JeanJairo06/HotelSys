from django.contrib.auth.models import User
from django.db import models

from core.models import ModeloBase
from empleados.models import Empleado


class MotivoExpiracionSesion(models.TextChoices):
    INACTIVIDAD = 'idle_timeout', 'Inactividad'
    LIMITE_ABSOLUTO = 'absolute_timeout', 'Límite absoluto'
    SESION_LEGADA = 'legacy_session', 'Sesión sin política vigente'


class UsuarioEmpleado(ModeloBase):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil_empleado',
    )
    empleado = models.OneToOneField(
        Empleado,
        on_delete=models.PROTECT,
        related_name='cuenta_usuario',
    )

    class Meta:
        db_table = 'usuarios_empleados'
        verbose_name = 'Usuario empleado'
        verbose_name_plural = 'Usuarios empleados'

    def __str__(self):
        return f'{self.usuario.username} - {self.empleado.nombre_completo}'


class AuditoriaSesion(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias_sesion',
    )
    roles_efectivos = models.CharField(max_length=100, blank=True)
    motivo = models.CharField(max_length=20, choices=MotivoExpiracionSesion.choices)
    ruta = models.CharField(max_length=255)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auditorias_sesion'
        ordering = ('-creado_en',)
        indexes = [
            models.Index(fields=('usuario', 'creado_en')),
            models.Index(fields=('motivo', 'creado_en')),
        ]
        verbose_name = 'Auditoría de sesión'
        verbose_name_plural = 'Auditorías de sesión'

    def __str__(self):
        return f'{self.get_motivo_display()} - {self.creado_en:%Y-%m-%d %H:%M}'
