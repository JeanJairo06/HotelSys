from datetime import timedelta
from decimal import Decimal

from habitaciones.models import Tarifa


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
