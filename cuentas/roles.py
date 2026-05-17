ROLE_ADMIN = 'admin'
ROLE_RECEPCIONISTA = 'recepcionista'
ROLE_HOUSEKEEPING = 'housekeeping'

SYSTEM_ROLES = [
    ROLE_ADMIN,
    ROLE_RECEPCIONISTA,
    ROLE_HOUSEKEEPING,
]


def user_has_role(user, role):
    if not user.is_authenticated:
        return False

    if role == ROLE_ADMIN and user.is_superuser:
        return True

    return user.groups.filter(name=role).exists()


def user_has_any_role(user, roles):
    return any(user_has_role(user, role) for role in roles)
