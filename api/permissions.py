from rest_framework.permissions import BasePermission

from config.choices import EstadoGeneral
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA, user_has_role


class IsEmpleadoActivo(BasePermission):
    message = 'El usuario no tiene un empleado activo vinculado.'

    def has_permission(self, request, view):
        perfil = getattr(request.user, 'perfil_empleado', None)
        return bool(
            request.user
            and request.user.is_authenticated
            and perfil
            and perfil.empleado.estado == EstadoGeneral.ACTIVO
        )


class RolePermission(BasePermission):
    roles = []
    message = 'No tiene permisos para acceder a este recurso.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return any(user_has_role(request.user, role) for role in self.roles)


class IsAdminRole(RolePermission):
    roles = [ROLE_ADMIN]


class IsRecepcionistaRole(RolePermission):
    roles = [ROLE_RECEPCIONISTA]


class IsHousekeepingRole(RolePermission):
    roles = [ROLE_HOUSEKEEPING]


class HasAnyRole(RolePermission):
    def has_permission(self, request, view):
        self.roles = getattr(view, 'allowed_roles', [])
        return super().has_permission(request, view)
