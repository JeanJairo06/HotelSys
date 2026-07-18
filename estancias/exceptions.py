from core.exceptions import ReglaNegocioViolada


class CheckinYaRealizado(ReglaNegocioViolada):
    code = 'CHECKIN_YA_REALIZADO'
    default_message = 'La reserva ya tiene check-in realizado.'


class CheckinNoPermitido(ReglaNegocioViolada):
    code = 'CHECKIN_NO_PERMITIDO'
    default_message = 'No se puede realizar el check-in para esta reserva.'


class EstanciaActivaExistente(ReglaNegocioViolada):
    code = 'ESTANCIA_ACTIVA_EXISTENTE'
    default_message = 'La habitacion ya tiene una estancia activa.'


class CheckoutYaRealizado(ReglaNegocioViolada):
    code = 'CHECKOUT_YA_REALIZADO'
    default_message = 'La estancia ya tiene checkout realizado.'


class CheckoutNoPermitido(ReglaNegocioViolada):
    code = 'CHECKOUT_NO_PERMITIDO'
    default_message = 'No se puede realizar checkout para esta estancia.'
