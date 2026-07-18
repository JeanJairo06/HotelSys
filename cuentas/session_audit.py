from urllib.parse import urlsplit

from cuentas.models import AuditoriaSesion


def registrar_expiracion_sesion(*, user, policy, motivo, ruta):
    return AuditoriaSesion.objects.create(
        usuario=user if user.is_authenticated else None,
        roles_efectivos=','.join(policy.roles),
        motivo=motivo,
        ruta=urlsplit(ruta).path or '/',
    )
