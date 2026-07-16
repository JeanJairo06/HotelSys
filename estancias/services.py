from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from config.choices import EstadoEstancia, EstadoFolio, EstadoHabitacion, EstadoReserva
from habitaciones.services import publicar_evento_estado_habitacion, tiene_estancia_activa

from .models import Estancia


def registrar_checkin(reserva):
    return EstanciaService.checkin(reserva)


def registrar_checkout(estancia):
    return EstanciaService.checkout(estancia)


class EstanciaService:
    """
    Centraliza el flujo operativo de check-in y checkout.

    Las funciones registrar_checkin y registrar_checkout se mantienen como wrappers
    para no romper vistas, API ni tests existentes.
    """

    @staticmethod
    @transaction.atomic
    def checkin(reserva):
        """
        Realiza el check-in de una reserva confirmada.

        Crea la estancia y actualiza reserva/habitacion dentro de una transaccion
        para evitar estados parciales si alguna validacion falla.
        """
        EstanciaService._validar_checkin(reserva)

        estancia = Estancia.objects.create(
            reserva=reserva,
            habitacion=reserva.habitacion,
            fecha_checkin=timezone.now(),
            precio_final=reserva.precio_total,
            estado=EstadoEstancia.ACTIVA,
        )

        from facturacion.models import Folio
        from facturacion.services import FolioService

        folio = Folio.objects.create(estancia=estancia)
        FolioService.recalcular_totales(folio)

        reserva.estado = EstadoReserva.CHECKIN
        reserva.save(update_fields=['estado'])

        EstanciaService._cambiar_estado_habitacion(reserva.habitacion, EstadoHabitacion.OCUPADA)

        return estancia

    @staticmethod
    @transaction.atomic
    def checkout(estancia):
        """
        Finaliza una estancia activa.

        Deja la reserva finalizada y mueve la habitacion a LIMPIEZA para continuar
        el flujo operativo de housekeeping.
        """
        folio = EstanciaService._validar_checkout(estancia)

        estancia.estado = EstadoEstancia.FINALIZADA
        estancia.fecha_checkout = timezone.now()
        estancia.save(update_fields=['estado', 'fecha_checkout'])

        estancia.reserva.estado = EstadoReserva.FINALIZADA
        estancia.reserva.save(update_fields=['estado'])

        if folio and folio.estado != EstadoFolio.CERRADO:
            folio.estado = EstadoFolio.CERRADO
            folio.save(update_fields=['estado'])

        EstanciaService._cambiar_estado_habitacion(estancia.habitacion, EstadoHabitacion.LIMPIEZA)

        return estancia

    @staticmethod
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

    @staticmethod
    def _validar_checkout(estancia):
        if estancia.estado != EstadoEstancia.ACTIVA:
            raise ValidationError('Solo se puede finalizar una estancia activa.')

        folio = getattr(estancia, 'folio', None)
        if not folio:
            raise ValidationError('No se puede hacer checkout porque la estancia no tiene folio.')

        from facturacion.exceptions import CheckoutBloqueadoError
        from facturacion.services import FolioService

        FolioService.recalcular_totales(folio)
        saldo_pendiente = folio.saldo_pendiente
        if saldo_pendiente > 0:
            raise CheckoutBloqueadoError(f'No se puede hacer checkout. Saldo pendiente: S/ {saldo_pendiente}.')

        return folio

    @staticmethod
    def _cambiar_estado_habitacion(habitacion, nuevo_estado):
        estado_anterior = habitacion.estado
        habitacion.estado = nuevo_estado
        habitacion.save(update_fields=['estado'])
        publicar_evento_estado_habitacion(habitacion, estado_anterior)
