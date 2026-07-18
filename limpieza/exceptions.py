from habitaciones.exceptions import TransicionHabitacionInvalida


class HousekeepingTransicionInvalida(TransicionHabitacionInvalida):
    code = 'HOUSEKEEPING_TRANSICION_INVALIDA'
    default_message = 'Housekeeping no puede realizar esta transicion de habitacion.'
