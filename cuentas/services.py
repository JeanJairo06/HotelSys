from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction

from config.choices import EstadoGeneral
from cuentas.exceptions import EmpleadoNoDisponible, UsuarioDuplicado, UsuarioNoDesactivable
from cuentas.models import UsuarioEmpleado
from cuentas.roles import ROLE_ADMIN
from empleados.models import Empleado


class UsuarioService:
    @staticmethod
    def usuarios_queryset():
        return User.objects.select_related('perfil_empleado__empleado').prefetch_related('groups').order_by('username')

    @staticmethod
    def detalle_queryset():
        return User.objects.select_related('perfil_empleado__empleado').prefetch_related('groups')

    @staticmethod
    def empleados_disponibles_queryset(*, empleado_actual=None, empleado_id=None):
        empleados_con_cuenta_historica = UsuarioEmpleado.todos.values('empleado_id')
        queryset = Empleado.objects.filter(estado=EstadoGeneral.ACTIVO).exclude(
            pk__in=empleados_con_cuenta_historica,
        )

        if empleado_actual:
            queryset = queryset | Empleado.objects.filter(pk=empleado_actual.pk)

        if empleado_id:
            queryset = queryset.filter(pk=empleado_id)

        return queryset.distinct().order_by('apellidos', 'nombres')

    @staticmethod
    @transaction.atomic
    def crear_usuario(*, username, password, empleado, groups, is_active=True, usuario_actor=None):
        UsuarioService._validar_empleado_disponible(empleado)
        UsuarioService._validar_username_disponible(username)

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=empleado.nombres,
                last_name=empleado.apellidos,
                email=empleado.email,
                is_active=is_active,
                is_staff=UsuarioService._incluye_rol_admin(groups),
            )
            user.groups.set(groups)
            UsuarioEmpleado.objects.create(
                usuario=user,
                empleado=empleado,
                creado_por=usuario_actor if UsuarioService._usuario_persistido(usuario_actor) else None,
            )
        except IntegrityError as exc:
            raise UsuarioDuplicado() from exc

        return user

    @staticmethod
    @transaction.atomic
    def actualizar_usuario(*, user, username, empleado, groups, is_active=True):
        UsuarioService._validar_empleado_disponible(empleado, usuario_actual=user)

        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            raise UsuarioDuplicado('Ya existe otro usuario con ese nombre de usuario.')

        user.username = username
        user.first_name = empleado.nombres
        user.last_name = empleado.apellidos
        user.email = empleado.email
        user.is_active = is_active
        user.is_staff = UsuarioService._incluye_rol_admin(groups)

        try:
            user.save(update_fields=['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff'])
            user.groups.set(groups)
            UsuarioEmpleado.todos.update_or_create(
                usuario=user,
                defaults={'empleado': empleado, 'activo': True},
            )
        except IntegrityError as exc:
            raise UsuarioDuplicado() from exc

        return user

    @staticmethod
    @transaction.atomic
    def desactivar_usuario(*, user, usuario_actor):
        if user == usuario_actor:
            raise UsuarioNoDesactivable('No puedes desactivar tu propio usuario.')

        user.is_active = False
        user.save(update_fields=['is_active'])

        perfil = UsuarioEmpleado.todos.filter(usuario=user).first()
        if perfil:
            perfil.eliminar(usuario=usuario_actor)

        return user

    @staticmethod
    def _validar_username_disponible(username):
        if User.objects.filter(username=username).exists():
            raise UsuarioDuplicado('Ya existe un usuario con ese nombre de usuario.')

    @staticmethod
    def _validar_empleado_disponible(empleado, *, usuario_actual=None):
        if empleado.estado != EstadoGeneral.ACTIVO:
            raise EmpleadoNoDisponible('Solo se puede vincular un empleado activo.')

        perfil_existente = UsuarioEmpleado.todos.filter(empleado=empleado).first()
        if not perfil_existente:
            return

        if usuario_actual and perfil_existente.usuario_id == usuario_actual.pk:
            return

        raise EmpleadoNoDisponible()

    @staticmethod
    def _incluye_rol_admin(groups):
        if hasattr(groups, 'filter'):
            return groups.filter(name=ROLE_ADMIN).exists()
        return any(group.name == ROLE_ADMIN for group in groups)

    @staticmethod
    def _usuario_persistido(user):
        return bool(user and getattr(user, 'is_authenticated', False) and user.pk)
