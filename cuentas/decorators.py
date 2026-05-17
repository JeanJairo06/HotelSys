from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

from cuentas.roles import user_has_any_role, user_has_role


def role_required(role):
    def check_role(user):
        if user_has_role(user, role):
            return True
        raise PermissionDenied

    def decorator(view_func):
        protected_view = user_passes_test(check_role, login_url='login')(view_func)
        return login_required(protected_view, login_url='login')

    return decorator


def any_role_required(*roles):
    def check_roles(user):
        if user_has_any_role(user, roles):
            return True
        raise PermissionDenied

    def decorator(view_func):
        protected_view = user_passes_test(check_roles, login_url='login')(view_func)
        return login_required(protected_view, login_url='login')

    return decorator
