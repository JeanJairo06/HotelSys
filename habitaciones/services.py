from django.core.exceptions import ValidationError
from django.db import transaction

from config.choices import EstadoEstancia, EstadoHabitacion
from core.events import (
    EVENTO_HABITACION_DISPONIBLE,
    EVENTO_HABITACION_EN_LIMPIEZA,
    EVENTO_HABITACION_EN_MANTENIMIENTO,
    EVENTO_HABITACION_OCUPADA,
    publicar_evento_habitacion,
)


EVENTOS_POR_ESTADO = {
    EstadoHabitacion.DISPONIBLE: EVENTO_HABITACION_DISPONIBLE,
    EstadoHabitacion.OCUPADA: EVENTO_HABITACION_OCUPADA,
    EstadoHabitacion.LIMPIEZA: EVENTO_HABITACION_EN_LIMPIEZA,
    EstadoHabitacion.MANTENIMIENTO: EVENTO_HABITACION_EN_MANTENIMIENTO,
}


@transaction.atomic
def cambiar_estado_manual(habitacion, nuevo_estado):
    """
    Cambia el estado de una habitacion desde el panel manual.

    La funcion protege la consistencia del flujo operativo: una habitacion ocupada
    debe liberarse mediante checkout, no por edicion manual del estado.
    """
    _validar_cambio_estado_manual(habitacion, nuevo_estado)
    estado_anterior = habitacion.estado
    habitacion.estado = nuevo_estado
    habitacion.save(update_fields=['estado'])
    publicar_evento_estado_habitacion(habitacion, estado_anterior)
    return habitacion


def tiene_estancia_activa(habitacion):
    return habitacion.estancias.filter(
        estado=EstadoEstancia.ACTIVA,
        fecha_checkout__isnull=True,
    ).exists()


def _validar_cambio_estado_manual(habitacion, nuevo_estado):
    if tiene_estancia_activa(habitacion) and nuevo_estado != EstadoHabitacion.OCUPADA:
        raise ValidationError(
            'No se puede cambiar una habitacion con estancia activa a un estado distinto de ocupada.'
        )

    if habitacion.estado == EstadoHabitacion.OCUPADA and nuevo_estado in [
        EstadoHabitacion.DISPONIBLE,
        EstadoHabitacion.LIMPIEZA,
        EstadoHabitacion.MANTENIMIENTO,
    ]:
        raise ValidationError(
            'Una habitacion ocupada debe liberarse mediante checkout, no por cambio manual.'
        )


def publicar_evento_estado_habitacion(habitacion, estado_anterior):
    if estado_anterior == habitacion.estado:
        return

    evento = EVENTOS_POR_ESTADO.get(habitacion.estado)
    if evento:
        publicar_evento_habitacion(
            habitacion,
            estado_anterior=estado_anterior,
            evento=evento,
        )
