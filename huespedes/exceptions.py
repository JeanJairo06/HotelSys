from django.core.exceptions import ValidationError


class HuespedError(ValidationError):
    """Error de negocio del modulo de huespedes."""


class HuespedDuplicado(HuespedError):
    pass
