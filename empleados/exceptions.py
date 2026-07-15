from core.exceptions import OperacionNoPermitida, ReglaNegocioViolada, RecursoNoEncontrado


class EmpleadoDuplicado(ReglaNegocioViolada):
    code = 'EMPLEADO_DUPLICADO'
    default_message = 'Ya existe un empleado con esos datos.'


class EmpleadoNoEncontrado(RecursoNoEncontrado):
    code = 'EMPLEADO_NO_ENCONTRADO'
    default_message = 'El empleado solicitado no existe.'


class EmpleadoNoDesactivable(OperacionNoPermitida):
    code = 'EMPLEADO_NO_DESACTIVABLE'
    default_message = 'El empleado no puede desactivarse.'


class EmpleadoInactivo(OperacionNoPermitida):
    code = 'EMPLEADO_INACTIVO'
    default_message = 'El empleado se encuentra inactivo.'


class CargoEmpleadoInvalido(ReglaNegocioViolada):
    code = 'CARGO_EMPLEADO_INVALIDO'
    default_message = 'El cargo seleccionado no es valido.'


class DatosEmpleadoInvalidos(ReglaNegocioViolada):
    code = 'DATOS_EMPLEADO_INVALIDOS'
    default_message = 'Los datos del empleado no son validos.'
