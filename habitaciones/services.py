from django.core.exceptions import ValidationError
from django.db import transaction

from config.choices import EstadoEstancia, EstadoHabitacion


@transaction.atomic
def cambiar_estado_manual(habitacion, nuevo_estado):
    """
    Cambia el estado de una habitacion desde el panel manual.

    La funcion protege la consistencia del flujo operativo: una habitacion ocupada
    debe liberarse mediante checkout, no por edicion manual del estado.
    """
    estancia_activa = habitacion.estancias.filter(
        estado=EstadoEstancia.ACTIVA,
        fecha_checkout__isnull=True,
    ).exists()

    if estancia_activa and nuevo_estado != EstadoHabitacion.OCUPADA:
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

    habitacion.estado = nuevo_estado
    habitacion.save(update_fields=['estado'])
    return habitacion
