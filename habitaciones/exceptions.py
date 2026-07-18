from core.exceptions import ReglaNegocioViolada


class HabitacionNoDisponible(ReglaNegocioViolada):
    code = 'HABITACION_NO_DISPONIBLE'
    default_message = 'La habitacion no esta disponible para la operacion solicitada.'


class TransicionHabitacionInvalida(ReglaNegocioViolada):
    code = 'TRANSICION_HABITACION_INVALIDA'
    default_message = 'La transicion de estado de habitacion no esta permitida.'
