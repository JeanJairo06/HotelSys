from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse

from cuentas.session_audit import registrar_expiracion_sesion
from cuentas.session_policy import get_session_policy
from cuentas.session_state import get_expiration_reason, refresh_session_activity


class SessionExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated or self._is_expiration_excluded(request):
            return self.get_response(request)

        policy = get_session_policy(request.user)
        reason = get_expiration_reason(request, policy)
        if reason:
            return self._expire_session(request, policy, reason)

        response = self.get_response(request)
        if not self._is_activity_excluded(request):
            refresh_session_activity(request)
        return response

    @staticmethod
    def _is_expiration_excluded(request):
        return any(
            request.path.startswith(prefix)
            for prefix in settings.SESSION_EXPIRATION_EXCLUDED_PREFIXES
        )

    @staticmethod
    def _is_activity_excluded(request):
        if SessionExpirationMiddleware._expects_json(request):
            return True

        return any(
            request.path.startswith(prefix)
            for prefix in settings.SESSION_ACTIVITY_EXCLUDED_PREFIXES
        )

    @staticmethod
    def _expects_json(request):
        return 'application/json' in request.headers.get('Accept', '')

    @staticmethod
    def _expire_session(request, policy, reason):
        registrar_expiracion_sesion(
            user=request.user,
            policy=policy,
            motivo=reason,
            ruta=request.get_full_path(),
        )
        logout(request)

        if SessionExpirationMiddleware._expects_json(request):
            return JsonResponse(
                {
                    'detail': 'La sesión ha expirado.',
                    'code': 'session_expired',
                },
                status=401,
            )

        messages.warning(request, 'Tu sesión ha expirado. Inicia sesión nuevamente.')
        return redirect_to_login(request.get_full_path(), login_url=settings.LOGIN_URL)
