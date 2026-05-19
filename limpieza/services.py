from django.core.exceptions import ValidationError

from config.choices import EstadoHabitacion


def marcar_disponible(habitacion):
    """Libera una habitacion solo si housekeeping puede cerrarla correctamente."""
    if habitacion.estado not in [EstadoHabitacion.LIMPIEZA, EstadoHabitacion.MANTENIMIENTO]:
        raise ValidationError('Solo se pueden liberar habitaciones en limpieza o mantenimiento.')

    habitacion.estado = EstadoHabitacion.DISPONIBLE
    habitacion.save(update_fields=['estado'])
    return habitacion


def marcar_mantenimiento(habitacion):
    """Pasa una habitacion a mantenimiento sin permitir afectar ocupaciones activas."""
    if habitacion.estado == EstadoHabitacion.OCUPADA:
        raise ValidationError('No se puede enviar a mantenimiento una habitacion ocupada.')

    habitacion.estado = EstadoHabitacion.MANTENIMIENTO
    habitacion.save(update_fields=['estado'])
    return habitacion
