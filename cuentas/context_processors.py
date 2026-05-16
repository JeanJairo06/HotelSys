from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA, user_has_role


def user_roles(request):
    user = request.user
    is_admin = user_has_role(user, ROLE_ADMIN)
    is_recepcionista = user_has_role(user, ROLE_RECEPCIONISTA)
    is_housekeeping = user_has_role(user, ROLE_HOUSEKEEPING)

    return {
        'user_is_admin': is_admin,
        'user_is_recepcionista': is_recepcionista,
        'user_is_housekeeping': is_housekeeping,
        'user_has_system_role': is_admin or is_recepcionista or is_housekeeping,
    }
