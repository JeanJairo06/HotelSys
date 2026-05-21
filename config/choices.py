from django.db import models


class EstadoHabitacion(models.TextChoices):
    DISPONIBLE = 'DISPONIBLE', 'Disponible'
    OCUPADA = 'OCUPADA', 'Ocupada'
    LIMPIEZA = 'LIMPIEZA', 'Limpieza'
    MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'


class TipoDocumento(models.TextChoices):
    DNI = 'DNI', 'DNI'
    RUC = 'RUC', 'RUC'


class EstadoGeneral(models.IntegerChoices):
    INACTIVO = 0, 'Inactivo'
    ACTIVO = 1, 'Activo'


class CargoEmpleado(models.TextChoices):
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
    RECEPCIONISTA = 'RECEPCIONISTA', 'Recepcionista'
    HOUSEKEEPING = 'HOUSEKEEPING', 'Housekeeping'
    #SUPERVISOR = 'SUPERVISOR', 'Supervisor'
    #MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'
    #CONTABILIDAD = 'CONTABILIDAD', 'Contabilidad'
    #OTRO = 'OTRO', 'Otro'


class EstadoReserva(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    CONFIRMADA = 'CONFIRMADA', 'Confirmada'
    CANCELADA = 'CANCELADA', 'Cancelada'
    CHECKIN = 'CHECKIN', 'Check-in realizado'
    FINALIZADA = 'FINALIZADA', 'Finalizada'


class OrigenReserva(models.TextChoices):
    WEB = 'WEB', 'Web'
    TELEFONO = 'TELEFONO', 'Teléfono'
    RECEPCION = 'RECEPCION', 'Recepción'
    AGENCIA = 'AGENCIA', 'Agencia'
    OTRO = 'OTRO', 'Otro'


class EstadoEstancia(models.TextChoices):
    ACTIVA = 'ACTIVA', 'Activa'
    FINALIZADA = 'FINALIZADA', 'Finalizada'
    CANCELADA = 'CANCELADA', 'Cancelada'


class TipoCargo(models.TextChoices):
    HABITACION = 'HABITACION', 'Habitación'
    RESTAURANTE = 'RESTAURANTE', 'Restaurante'
    LAVANDERIA = 'LAVANDERIA', 'Lavandería'
    MINIBAR = 'MINIBAR', 'Minibar'
    PENALIDAD = 'PENALIDAD', 'Penalidad'
    OTRO = 'OTRO', 'Otro'


class EstadoFolio(models.TextChoices):
    ABIERTO = 'ABIERTO', 'Abierto'
    PENDIENTE = 'PENDIENTE', 'Pendiente de pago'
    PAGADO = 'PAGADO', 'Pagado'
    CERRADO = 'CERRADO', 'Cerrado'
    ANULADO = 'ANULADO', 'Anulado'


class RolUsuario(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'
    RECEPCIONISTA = 'RECEPCIONISTA', 'Recepcionista'
    HOUSEKEEPING = 'HOUSEKEEPING', 'Housekeeping'
