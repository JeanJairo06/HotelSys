import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


logger = logging.getLogger(__name__)


def notify_session_expired(user_id):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    try:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}_sessions',
            {'type': 'session.expired'},
        )
    except Exception:
        logger.exception('No se pudo notificar la expiración de sesión al WebSocket.')
