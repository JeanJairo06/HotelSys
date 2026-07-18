from datetime import timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from config.choices import EstadoReserva
from habitaciones.models import Habitacion, Tarifa
from reservas.exceptions import (
    ReservaNoDisponible,
    ReservaNoModificable,
    ReservaSolapada,
    TransicionReservaInvalida,
)
from reservas.models import Reserva


ESTADOS_NO_BLOQUEAN_DISPONIBILIDAD = [
    EstadoReserva.CANCELADA,
    EstadoReserva.FINALIZADA,
]


def calcular_precio_total_reserva(tipo_habitacion, fecha_entrada, fecha_salida):
    if not tipo_habitacion or not fecha_entrada or not fecha_salida or fecha_salida <= fecha_entrada:
        return Decimal('0.00')

    tarifas = list(
        Tarifa.objects.filter(
            tipo_habitacion=tipo_habitacion,
            fecha_inicio__lt=fecha_salida,
            fecha_fin__gte=fecha_entrada,
        ).order_by('fecha_inicio')
    )
    total = Decimal('0.00')
    noche = fecha_entrada

    while noche < fecha_salida:
        tarifa = next(
            (
                tarifa
                for tarifa in tarifas
                if tarifa.fecha_inicio <= noche <= tarifa.fecha_fin
            ),
            None,
        )
        total += tarifa.precio_noche if tarifa else tipo_habitacion.precio_base
        noche += timedelta(days=1)

    return total


def habitaciones_disponibles(
    *,
    tipo=None,
    fecha_entrada=None,
    fecha_salida=None,
    num_huespedes=None,
    reserva_id=None,
):
    queryset = Habitacion.objects.select_related('hotel', 'tipo')

    if tipo:
        queryset = queryset.filter(tipo_id=tipo)

    if num_huespedes:
        queryset = queryset.filter(tipo__capacidad__gte=num_huespedes)

    if fecha_entrada and fecha_salida and fecha_salida > fecha_entrada:
        reservas_ocupadas = Reserva.objects.filter(
            fecha_entrada__lt=fecha_salida,
            fecha_salida__gt=fecha_entrada,
        ).exclude(estado__in=ESTADOS_NO_BLOQUEAN_DISPONIBILIDAD)
        if reserva_id:
            reservas_ocupadas = reservas_ocupadas.exclude(pk=reserva_id)
        queryset = queryset.exclude(pk__in=reservas_ocupadas.values('habitacion_id'))

    return queryset


def validar_reserva(
    *,
    habitacion,
    fecha_entrada,
    fecha_salida,
    num_adultos,
    reserva_id=None,
    permitir_pasado=False,
):
    errors = {}

    if fecha_entrada and fecha_salida and fecha_salida <= fecha_entrada:
        errors['fecha_salida'] = 'La fecha de salida debe ser mayor a la fecha de entrada.'

    if not permitir_pasado and fecha_entrada and fecha_entrada < timezone.localdate():
        errors['fecha_entrada'] = 'La fecha de entrada no puede ser anterior a hoy.'

    if num_adultos is not None and num_adultos < 1:
        errors['num_adultos'] = 'Debe registrar al menos un adulto.'

    if habitacion and num_adultos and num_adultos > habitacion.tipo.capacidad:
        raise ReservaNoDisponible({
            'num_adultos': 'La cantidad de huespedes supera la capacidad de la habitacion.',
        })

    if errors:
        raise ValidationError(errors)

    if habitacion and fecha_entrada and fecha_salida:
        validar_disponibilidad(
            habitacion=habitacion,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            reserva_id=reserva_id,
        )


def validar_disponibilidad(*, habitacion, fecha_entrada, fecha_salida, reserva_id=None):
    reserva_solapada = Reserva.objects.filter(
        habitacion=habitacion,
        fecha_entrada__lt=fecha_salida,
        fecha_salida__gt=fecha_entrada,
    ).exclude(estado__in=ESTADOS_NO_BLOQUEAN_DISPONIBILIDAD)
    if reserva_id:
        reserva_solapada = reserva_solapada.exclude(pk=reserva_id)

    if reserva_solapada.exists():
        raise ReservaSolapada({
            'habitacion': 'La habitacion ya tiene una reserva activa en ese rango de fechas.',
        })


def asegurar_modificable(reserva):
    if not reserva.es_modificable:
        raise ReservaNoModificable(
            f'No se puede editar una reserva en estado {reserva.get_estado_display()}.'
        )


@transaction.atomic
def crear_reserva(
    *,
    huesped,
    habitacion,
    fecha_entrada,
    fecha_salida,
    num_adultos=1,
    origen=None,
    usuario=None,
):
    habitacion = Habitacion.objects.select_for_update().select_related('hotel', 'tipo').get(pk=habitacion.pk)
    validar_reserva(
        habitacion=habitacion,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        num_adultos=num_adultos,
    )
    precio_total = calcular_precio_total_reserva(habitacion.tipo, fecha_entrada, fecha_salida)

    reserva = Reserva(
        hotel=habitacion.hotel,
        huesped=huesped,
        habitacion=habitacion,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        num_adultos=num_adultos,
        origen=origen or Reserva._meta.get_field('origen').default,
        estado=EstadoReserva.CONFIRMADA,
        precio_total=precio_total,
        creado_por=usuario if getattr(usuario, 'is_authenticated', False) else None,
    )
    try:
        reserva.save()
    except IntegrityError as error:
        raise ReservaNoDisponible('No se pudo generar un codigo unico para la reserva.') from error
    publicar_actualizacion_reserva(reserva, accion='creada')
    return reserva


@transaction.atomic
def editar_reserva(reserva, *, usuario=None, **datos):
    reserva = Reserva.objects.select_for_update().select_related('habitacion__tipo', 'habitacion__hotel').get(
        pk=reserva.pk,
    )
    asegurar_modificable(reserva)

    habitacion = datos.get('habitacion', reserva.habitacion)
    habitacion = Habitacion.objects.select_for_update().select_related('hotel', 'tipo').get(pk=habitacion.pk)
    fecha_entrada = datos.get('fecha_entrada', reserva.fecha_entrada)
    fecha_salida = datos.get('fecha_salida', reserva.fecha_salida)
    num_adultos = datos.get('num_adultos', reserva.num_adultos)

    validar_reserva(
        habitacion=habitacion,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        num_adultos=num_adultos,
        reserva_id=reserva.pk,
    )

    reserva.huesped = datos.get('huesped', reserva.huesped)
    reserva.habitacion = habitacion
    reserva.hotel = habitacion.hotel
    reserva.fecha_entrada = fecha_entrada
    reserva.fecha_salida = fecha_salida
    reserva.num_adultos = num_adultos
    reserva.origen = datos.get('origen', reserva.origen)
    reserva.precio_total = calcular_precio_total_reserva(habitacion.tipo, fecha_entrada, fecha_salida)
    reserva.save()
    publicar_actualizacion_reserva(reserva, accion='actualizada')
    return reserva


@transaction.atomic
def cancelar_reserva(reserva, *, usuario=None):
    reserva = Reserva.todos.select_for_update().get(pk=reserva.pk)

    if reserva.estado == EstadoReserva.CANCELADA:
        return reserva

    if reserva.estado in [EstadoReserva.CHECKIN, EstadoReserva.FINALIZADA]:
        raise TransicionReservaInvalida(
            'No se puede cancelar una reserva con check-in o finalizada.'
        )

    reserva.estado = EstadoReserva.CANCELADA
    reserva.save(update_fields=['estado', 'actualizado_en'])

    publicar_actualizacion_reserva(reserva, accion='cancelada')
    return reserva


def publicar_actualizacion_reserva(reserva, *, accion):
    payload = {
        'tipo': 'RESERVA_ACTUALIZADA',
        'accion': accion,
        'reserva_id': reserva.id,
        'codigo': reserva.codigo,
        'estado': reserva.estado,
        'hotel_id': reserva.hotel_id,
        'habitacion_id': reserva.habitacion_id,
        'fecha_entrada': reserva.fecha_entrada.isoformat(),
        'fecha_salida': reserva.fecha_salida.isoformat(),
        'actualizado_en': timezone.now().isoformat(),
    }

    def enviar():
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        async_to_sync(channel_layer.group_send)(
            f'hotel_{reserva.hotel_id}_reservas',
            {
                'type': 'reserva.actualizada',
                'payload': payload,
            },
        )

    transaction.on_commit(enviar)
    return payload
