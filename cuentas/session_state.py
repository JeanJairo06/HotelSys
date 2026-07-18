from django.utils import timezone

from cuentas.models import MotivoExpiracionSesion


SESSION_STARTED_AT = 'session_started_at'
SESSION_LAST_ACTIVITY_AT = 'session_last_activity_at'


def initialize_session(request):
    now = _current_timestamp()
    request.session[SESSION_STARTED_AT] = now
    request.session[SESSION_LAST_ACTIVITY_AT] = now


def get_expiration_reason(request, policy):
    started_at = request.session.get(SESSION_STARTED_AT)
    last_activity_at = request.session.get(SESSION_LAST_ACTIVITY_AT)
    if not _is_timestamp(started_at) or not _is_timestamp(last_activity_at):
        return MotivoExpiracionSesion.SESION_LEGADA

    now = _current_timestamp()
    if now - started_at >= policy.absolute_timeout:
        return MotivoExpiracionSesion.LIMITE_ABSOLUTO
    if now - last_activity_at >= policy.idle_timeout:
        return MotivoExpiracionSesion.INACTIVIDAD
    return None


def refresh_session_activity(request):
    request.session[SESSION_LAST_ACTIVITY_AT] = _current_timestamp()


def get_session_expires_at(request, policy):
    started_at = request.session[SESSION_STARTED_AT]
    last_activity_at = request.session[SESSION_LAST_ACTIVITY_AT]
    return min(
        started_at + policy.absolute_timeout,
        last_activity_at + policy.idle_timeout,
    )


def _current_timestamp():
    return int(timezone.now().timestamp())


def _is_timestamp(value):
    return isinstance(value, int) and not isinstance(value, bool)
