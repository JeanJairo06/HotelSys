from core.exceptions import OperacionNoPermitida, ReglaNegocioViolada


class UsuarioDuplicado(ReglaNegocioViolada):
    code = 'USUARIO_DUPLICADO'
    default_message = 'Ya existe un usuario con esos datos.'


class EmpleadoNoDisponible(ReglaNegocioViolada):
    code = 'EMPLEADO_NO_DISPONIBLE'
    default_message = 'El empleado seleccionado no esta disponible para crear una cuenta.'


class UsuarioNoDesactivable(OperacionNoPermitida):
    code = 'USUARIO_NO_DESACTIVABLE'
    default_message = 'El usuario no puede desactivarse.'


class RolUsuarioInvalido(ReglaNegocioViolada):
    code = 'ROL_USUARIO_INVALIDO'
    default_message = 'Los roles seleccionados no son validos para el usuario.'
