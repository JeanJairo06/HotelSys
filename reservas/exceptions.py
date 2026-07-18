from django.core.exceptions import ValidationError


class ReservaError(ValidationError):
    """Error de negocio del modulo de reservas."""


class HuespedDuplicado(ReservaError):
    pass


class ReservaSolapada(ReservaError):
    pass


class ReservaNoDisponible(ReservaError):
    pass


class ReservaNoModificable(ReservaError):
    pass


class TransicionReservaInvalida(ReservaError):
    pass
