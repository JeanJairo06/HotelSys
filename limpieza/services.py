from django.core.exceptions import ValidationError

from config.choices import EstadoHabitacion
from habitaciones.services import publicar_evento_estado_habitacion, tiene_estancia_activa


def marcar_disponible(habitacion):
    """Libera una habitacion solo si housekeeping puede cerrarla correctamente."""
    _validar_liberacion_limpieza(habitacion)

    estado_anterior = habitacion.estado
    habitacion.estado = EstadoHabitacion.DISPONIBLE
    habitacion.save(update_fields=['estado'])
    publicar_evento_estado_habitacion(habitacion, estado_anterior)
    return habitacion


def marcar_mantenimiento(habitacion):
    """Pasa una habitacion a mantenimiento sin permitir afectar ocupaciones activas."""
    _validar_envio_mantenimiento(habitacion)

    estado_anterior = habitacion.estado
    habitacion.estado = EstadoHabitacion.MANTENIMIENTO
    habitacion.save(update_fields=['estado'])
    publicar_evento_estado_habitacion(habitacion, estado_anterior)
    return habitacion


def _validar_liberacion_limpieza(habitacion):
    if habitacion.estado != EstadoHabitacion.LIMPIEZA:
        raise ValidationError('Solo se pueden liberar habitaciones en limpieza.')

    if tiene_estancia_activa(habitacion):
        raise ValidationError('No se puede liberar una habitacion con estancia activa.')


def _validar_envio_mantenimiento(habitacion):
    if habitacion.estado == EstadoHabitacion.OCUPADA:
        raise ValidationError('No se puede enviar a mantenimiento una habitacion ocupada.')

    if tiene_estancia_activa(habitacion):
        raise ValidationError('No se puede enviar a mantenimiento una habitacion con estancia activa.')
