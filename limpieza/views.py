from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from config.choices import EstadoHabitacion
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING
from habitaciones.models import Habitacion

from .services import marcar_disponible, marcar_mantenimiento


@any_role_required(ROLE_ADMIN, ROLE_HOUSEKEEPING)
def panel_limpieza(request):
    """Muestra habitaciones pendientes de limpieza o mantenimiento."""
    habitaciones = Habitacion.objects.select_related('hotel', 'tipo').filter(
        estado__in=[EstadoHabitacion.LIMPIEZA, EstadoHabitacion.MANTENIMIENTO],
    ).order_by('piso', 'numero')

    piso = request.GET.get('piso')
    if piso:
        habitaciones = habitaciones.filter(piso=piso)

    contexto = {
        'habitaciones': habitaciones,
        'pisos': Habitacion.objects.order_by('piso').values_list('piso', flat=True).distinct(),
        'total_limpieza': habitaciones.filter(estado=EstadoHabitacion.LIMPIEZA).count(),
        'total_mantenimiento': habitaciones.filter(estado=EstadoHabitacion.MANTENIMIENTO).count(),
    }
    return render(request, 'limpieza/panel_limpieza.html', contexto)


@any_role_required(ROLE_ADMIN, ROLE_HOUSEKEEPING)
def marcar_habitacion_disponible(request, habitacion_id):
    """Marca como disponible una habitacion luego de limpieza o mantenimiento."""
    habitacion = get_object_or_404(Habitacion, pk=habitacion_id)

    if request.method == 'POST':
        try:
            marcar_disponible(habitacion)
            messages.success(request, 'Habitacion marcada como disponible.')
        except ValidationError as error:
            messages.error(request, error.messages[0])

    return redirect('limpieza:panel_limpieza')


@any_role_required(ROLE_ADMIN, ROLE_HOUSEKEEPING)
def marcar_habitacion_mantenimiento(request, habitacion_id):
    """Envia una habitacion a mantenimiento si no esta ocupada."""
    habitacion = get_object_or_404(Habitacion, pk=habitacion_id)

    if request.method == 'POST':
        try:
            marcar_mantenimiento(habitacion)
            messages.success(request, 'Habitacion enviada a mantenimiento.')
        except ValidationError as error:
            messages.error(request, error.messages[0])

    return redirect('limpieza:panel_limpieza')
