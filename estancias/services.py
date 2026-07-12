from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from config.choices import EstadoEstancia, EstadoFolio, EstadoHabitacion, EstadoReserva
from habitaciones.services import publicar_evento_estado_habitacion, tiene_estancia_activa

from .models import Estancia


@transaction.atomic
def registrar_checkin(reserva):
    """
    Realiza el check-in de una reserva confirmada.

    Crea la estancia y actualiza reserva/habitacion dentro de una transaccion para
    evitar estados parciales si alguna validacion falla.
    """
    _validar_checkin(reserva)

    estancia = Estancia.objects.create(
        reserva=reserva,
        habitacion=reserva.habitacion,
        fecha_checkin=timezone.now(),
        precio_final=reserva.precio_total,
        estado=EstadoEstancia.ACTIVA,
    )

    from facturacion.models import Folio

    folio = Folio.objects.create(estancia=estancia)
    folio.calcular_totales()

    reserva.estado = EstadoReserva.CHECKIN
    reserva.save(update_fields=['estado'])

    _cambiar_estado_habitacion(reserva.habitacion, EstadoHabitacion.OCUPADA)

    return estancia


@transaction.atomic
def registrar_checkout(estancia):
    """
    Finaliza una estancia activa.

    Deja la reserva finalizada y mueve la habitacion a LIMPIEZA para continuar el
    flujo operativo de housekeeping.
    """
    _validar_checkout(estancia)

    estancia.estado = EstadoEstancia.FINALIZADA
    estancia.fecha_checkout = timezone.now()
    estancia.save(update_fields=['estado', 'fecha_checkout'])

    estancia.reserva.estado = EstadoReserva.FINALIZADA
    estancia.reserva.save(update_fields=['estado'])

    _cambiar_estado_habitacion(estancia.habitacion, EstadoHabitacion.LIMPIEZA)

    return estancia


def _validar_checkin(reserva):
    if hasattr(reserva, 'estancia'):
        raise ValidationError('La reserva ya tiene una estancia registrada.')

    if reserva.estado != EstadoReserva.CONFIRMADA:
        raise ValidationError('Solo se puede realizar check-in de reservas confirmadas.')

    hoy = timezone.localdate()
    if not (reserva.fecha_entrada <= hoy < reserva.fecha_salida):
        raise ValidationError('El check-in solo se puede realizar dentro del rango de fechas de la reserva.')

    if reserva.habitacion.estado != EstadoHabitacion.DISPONIBLE:
        raise ValidationError('La habitacion no esta disponible para check-in.')

    if tiene_estancia_activa(reserva.habitacion):
        raise ValidationError('La habitacion ya tiene una estancia activa.')


def _validar_checkout(estancia):
    if estancia.estado != EstadoEstancia.ACTIVA:
        raise ValidationError('Solo se puede finalizar una estancia activa.')

    folio = getattr(estancia, 'folio', None)
    if folio and folio.estado not in [EstadoFolio.PAGADO, EstadoFolio.CERRADO]:
        raise ValidationError('No se puede hacer checkout con folio pendiente de pago.')


def _cambiar_estado_habitacion(habitacion, nuevo_estado):
    estado_anterior = habitacion.estado
    habitacion.estado = nuevo_estado
    habitacion.save(update_fields=['estado'])
    publicar_evento_estado_habitacion(habitacion, estado_anterior)
