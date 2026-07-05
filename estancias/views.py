from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from config.choices import EstadoEstancia, EstadoReserva
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from reservas.models import Reserva

from .models import Estancia
from .services import registrar_checkin, registrar_checkout


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def listar_estancias(request):
    """Muestra las estancias reales del hotel con filtro por estado operativo."""
    estancias = Estancia.objects.select_related(
        'reserva',
        'reserva__huesped',
        'habitacion',
        'habitacion__hotel',
        'folio',
    ).order_by('-fecha_checkin')

    estado = request.GET.get('estado')
    if estado:
        estancias = estancias.filter(estado=estado)

    contexto = {
        'estancias': estancias,
        'estados': EstadoEstancia.choices,
        'total_activas': estancias.filter(estado=EstadoEstancia.ACTIVA).count(),
        'total_finalizadas': estancias.filter(estado=EstadoEstancia.FINALIZADA).count(),
        'total_canceladas': estancias.filter(estado=EstadoEstancia.CANCELADA).count(),
    }
    return render(request, 'estancias/listar_estancias.html', contexto)


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def listar_reservas_checkin(request):
    """Lista reservas confirmadas que pueden iniciar el flujo de check-in."""
    reservas = Reserva.objects.select_related('hotel', 'huesped', 'habitacion').filter(
        estado=EstadoReserva.CONFIRMADA,
    ).order_by('fecha_entrada', 'habitacion__numero')
    return render(request, 'estancias/listar_reservas_checkin.html', {'reservas': reservas})


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def realizar_checkin(request, reserva_id):
    """Confirma el ingreso de un huesped y crea la estancia asociada."""
    reserva = get_object_or_404(
        Reserva.objects.select_related('hotel', 'huesped', 'habitacion'),
        pk=reserva_id,
    )

    if request.method == 'POST':
        try:
            registrar_checkin(reserva)
            messages.success(request, 'Check-in realizado correctamente.')
            return redirect('estancias:listar_estancias')
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect('estancias:listar_reservas_checkin')

    return render(request, 'estancias/confirmar_checkin.html', {'reserva': reserva})


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def realizar_checkout(request, estancia_id):
    """Finaliza una estancia activa y envia la habitacion a limpieza."""
    estancia = get_object_or_404(
        Estancia.objects.select_related('reserva', 'reserva__huesped', 'habitacion'),
        pk=estancia_id,
    )

    if request.method == 'POST':
        try:
            registrar_checkout(estancia)
            messages.success(request, 'Checkout realizado correctamente. Habitacion enviada a limpieza.')
            return redirect('estancias:listar_estancias')
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect('estancias:listar_estancias')

    return render(request, 'estancias/confirmar_checkout.html', {'estancia': estancia})
