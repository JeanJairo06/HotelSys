from rest_framework import status


class AppError(Exception):
    code = 'APP_ERROR'
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = 'No se pudo completar la operacion.'

    def __init__(self, message=None, *, code=None, detail=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.code
        self.detail = detail or {}
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class ReglaNegocioViolada(AppError):
    code = 'REGLA_NEGOCIO_VIOLADA'
    default_message = 'La operacion viola una regla de negocio.'


class RecursoNoEncontrado(AppError):
    code = 'RECURSO_NO_ENCONTRADO'
    status_code = status.HTTP_404_NOT_FOUND
    default_message = 'El recurso solicitado no existe.'


class AccesoNoAutorizado(AppError):
    code = 'ACCESO_NO_AUTORIZADO'
    status_code = status.HTTP_403_FORBIDDEN
    default_message = 'No tiene permisos para realizar esta accion.'


class OperacionNoPermitida(AppError):
    code = 'OPERACION_NO_PERMITIDA'
    status_code = status.HTTP_409_CONFLICT
    default_message = 'La operacion no esta permitida en el estado actual.'


class ValidacionDominioError(AppError):
    code = 'VALIDACION_DOMINIO_ERROR'
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = 'Los datos enviados no son validos para esta operacion.'
