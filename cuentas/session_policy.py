from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cuentas.roles import ROLE_ADMIN, SYSTEM_ROLES


DEFAULT_POLICY_ROLE = 'default'


@dataclass(frozen=True)
class SessionPolicy:
    idle_timeout: int
    absolute_timeout: int
    roles: tuple[str, ...]


def get_session_policy(user):
    roles = set()
    if user.is_authenticated:
        roles = set(user.groups.filter(name__in=SYSTEM_ROLES).values_list('name', flat=True))
        if user.is_superuser:
            roles.add(ROLE_ADMIN)

    policies = [_get_policy(role) for role in roles] or [_get_policy(DEFAULT_POLICY_ROLE)]
    return SessionPolicy(
        idle_timeout=min(policy['idle_timeout'] for policy in policies),
        absolute_timeout=min(policy['absolute_timeout'] for policy in policies),
        roles=tuple(sorted(roles)),
    )


def _get_policy(role):
    try:
        policy = settings.SESSION_ROLE_POLICIES[role]
        idle_timeout = policy['idle_timeout']
        absolute_timeout = policy['absolute_timeout']
    except (KeyError, TypeError) as error:
        raise ImproperlyConfigured(f'La política de sesión para "{role}" no está configurada.') from error

    if not isinstance(idle_timeout, int) or idle_timeout <= 0:
        raise ImproperlyConfigured(f'El tiempo inactivo para "{role}" debe ser un entero positivo.')
    if not isinstance(absolute_timeout, int) or absolute_timeout <= 0:
        raise ImproperlyConfigured(f'El límite absoluto para "{role}" debe ser un entero positivo.')

    return policy
