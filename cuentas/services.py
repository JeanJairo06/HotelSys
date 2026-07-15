from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction
from django.db.models import Q

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
    def actualizar_usuario(*, user, username, empleado, groups, is_active=True, usuario_actor=None):
        UsuarioService._validar_empleado_disponible(empleado, usuario_actual=user)
        UsuarioService._validar_cambio_seguridad(
            user=user,
            groups=groups,
            is_active=is_active,
            usuario_actor=usuario_actor,
        )

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
    def reactivar_usuario(*, user, usuario_actor=None):
        perfil = UsuarioEmpleado.todos.select_related('empleado').filter(usuario=user).first()
        if not perfil:
            raise UsuarioNoDesactivable('El usuario no tiene un perfil de empleado asociado para reactivar.')

        if perfil.empleado.estado != EstadoGeneral.ACTIVO:
            raise EmpleadoNoDisponible('No se puede reactivar un usuario con empleado inactivo.')

        user.is_active = True
        user.save(update_fields=['is_active'])

        perfil.activo = True
        perfil.save(update_fields=['activo', 'actualizado_en'])

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
    def _validar_cambio_seguridad(*, user, groups, is_active, usuario_actor=None):
        if UsuarioService._es_mismo_usuario(user, usuario_actor) and not is_active:
            raise UsuarioNoDesactivable('No puedes desactivar tu propio usuario.')

        conserva_admin = UsuarioService._incluye_rol_admin(groups)
        tenia_admin = UsuarioService._usuario_tiene_rol_admin(user)

        if UsuarioService._es_mismo_usuario(user, usuario_actor) and tenia_admin and not conserva_admin:
            raise UsuarioNoDesactivable('No puedes quitarte tu propio rol administrador.')

        if UsuarioService._deja_sistema_sin_admins(user=user, conserva_admin=conserva_admin, is_active=is_active):
            raise UsuarioNoDesactivable('No se puede dejar el sistema sin administradores activos.')

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
    def _usuario_tiene_rol_admin(user):
        return user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists()

    @staticmethod
    def _admins_activos_queryset():
        return User.objects.filter(
            Q(groups__name=ROLE_ADMIN) | Q(is_superuser=True),
            is_active=True,
        ).distinct()

    @staticmethod
    def _deja_sistema_sin_admins(*, user, conserva_admin, is_active):
        admins = UsuarioService._admins_activos_queryset().exclude(pk=user.pk)
        if admins.exists():
            return False

        return not (is_active and (conserva_admin or user.is_superuser))

    @staticmethod
    def _es_mismo_usuario(user, usuario_actor):
        return bool(usuario_actor and getattr(usuario_actor, 'is_authenticated', False) and user.pk == usuario_actor.pk)

    @staticmethod
    def _usuario_persistido(user):
        return bool(user and getattr(user, 'is_authenticated', False) and user.pk)
