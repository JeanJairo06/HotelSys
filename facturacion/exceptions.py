#F:\Ciclo IX\Taller de Programacion\HotelSys\facturacion\exceptions.py
from core.exceptions import ReglaNegocioViolada

class FolioCerradoError(ReglaNegocioViolada):
    code = 'FOLIO_CERRADO'
    default_message = 'No se pueden registrar operaciones (cargos o pagos) en un folio que ya está cerrado o pagado.'

class EstanciaFinalizadaError(ReglaNegocioViolada):
    code = 'ESTANCIA_FINALIZADA'
    default_message = 'No se pueden agregar cargos a una estancia que ya ha sido finalizada.'

class PagoInvalidoError(ReglaNegocioViolada):
    code = 'PAGO_INVALIDO'
    default_message = 'El monto del pago debe ser estrictamente mayor a cero y no puede superar el saldo pendiente actual.'

class CheckoutBloqueadoError(ReglaNegocioViolada):
    code = 'CHECKOUT_BLOQUEADO'
    default_message = 'No se puede realizar el check-out porque el folio presenta un saldo pendiente.'