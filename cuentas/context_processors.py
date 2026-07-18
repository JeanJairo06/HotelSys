from django.conf import settings

from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA, user_has_role
from cuentas.session_policy import get_session_policy
from cuentas.session_state import get_expiration_reason, get_session_expires_at


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


def session_timeout(request):
    if not request.user.is_authenticated:
        return {}

    policy = get_session_policy(request.user)
    if get_expiration_reason(request, policy):
        return {}

    return {
        'session_expires_at': get_session_expires_at(request, policy),
        'session_warning_seconds': settings.SESSION_WARNING_SECONDS,
        'session_activity_debounce_seconds': settings.SESSION_ACTIVITY_DEBOUNCE_SECONDS,
    }
