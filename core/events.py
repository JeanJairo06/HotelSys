from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone


EVENTO_HABITACION_OCUPADA = 'HABITACION_OCUPADA'
EVENTO_HABITACION_EN_LIMPIEZA = 'HABITACION_EN_LIMPIEZA'
EVENTO_HABITACION_DISPONIBLE = 'HABITACION_DISPONIBLE'
EVENTO_HABITACION_EN_MANTENIMIENTO = 'HABITACION_EN_MANTENIMIENTO'


def publicar_evento_habitacion(habitacion, *, estado_anterior, evento):
    payload = {
        'tipo': evento,
        'hotel_id': habitacion.hotel_id,
        'habitacion_id': habitacion.id,
        'numero': habitacion.numero,
        'piso': habitacion.piso,
        'tipo_habitacion': habitacion.tipo.nombre,
        'estado_anterior': estado_anterior,
        'estado_nuevo': habitacion.estado,
        'actualizado_en': timezone.now().isoformat(),
    }

    def enviar():
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        async_to_sync(channel_layer.group_send)(
            f'hotel_{habitacion.hotel_id}_habitaciones',
            {
                'type': 'habitacion.estado',
                'payload': payload,
            },
        )

    transaction.on_commit(enviar)
    return payload
