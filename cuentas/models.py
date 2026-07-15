from django.contrib.auth.models import User
from django.db import models

from core.models import ModeloBase
from empleados.models import Empleado


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
