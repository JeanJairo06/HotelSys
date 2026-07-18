from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.choices import EstadoEstancia, EstadoReserva
from core.exceptions import AppError
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from reservas.models import Reserva

from .models import Estancia
from .services import registrar_checkin, registrar_checkout


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def listar_estancias(request):
    """Muestra las estancias reales del hotel con filtro por estado operativo."""
    estancias_base = Estancia.objects.select_related(
        'reserva',
        'reserva__huesped',
        'habitacion',
        'habitacion__hotel',
        'folio',
    ).order_by('-fecha_checkin')

    estado = request.GET.get('estado')
    estancias = estancias_base
    if estado:
        estancias = estancias.filter(estado=estado)
    else:
        estancias = estancias.filter(estado=EstadoEstancia.ACTIVA)

    hoy = timezone.localdate()
    reservas_checkin = Reserva.objects.select_related('hotel', 'huesped', 'habitacion').filter(
        estado=EstadoReserva.CONFIRMADA,
        fecha_entrada__lte=hoy,
        fecha_salida__gt=hoy,
    ).order_by('fecha_entrada', 'habitacion__numero')

    contexto = {
        'estancias': estancias,
        'reservas_checkin': reservas_checkin,
        'estados': EstadoEstancia.choices,
        'total_activas': estancias_base.filter(estado=EstadoEstancia.ACTIVA).count(),
        'total_finalizadas': estancias_base.filter(estado=EstadoEstancia.FINALIZADA).count(),
        'total_canceladas': estancias_base.filter(estado=EstadoEstancia.CANCELADA).count(),
        'estado_actual': estado or EstadoEstancia.ACTIVA,
    }
    return render(request, 'estancias/listar_estancias.html', contexto)


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def listar_reservas_checkin(request):
    """Mantiene la URL antigua apuntando al tablero unico de estancias."""
    return redirect('estancias:listar_estancias')


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def detalle_estancia(request, estancia_id):
    """Muestra la informacion operativa de una estancia y su folio asociado."""
    estancia = get_object_or_404(
        Estancia.objects.select_related(
            'reserva',
            'reserva__hotel',
            'reserva__huesped',
            'habitacion',
            'habitacion__hotel',
            'habitacion__tipo',
            'folio',
        ).prefetch_related('cargos', 'folio__pagos'),
        pk=estancia_id,
    )

    folio = getattr(estancia, 'folio', None)
    return render(request, 'estancias/detalle_estancia.html', {
        'estancia': estancia,
        'folio': folio,
        'cargos': estancia.cargos.all(),
        'pagos': folio.pagos.filter(activo=True) if folio else [],
    })


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
            return redirect('estancias:listar_estancias')
        except AppError as error:
            messages.error(request, error.message)
            return redirect('estancias:listar_estancias')

    return redirect('estancias:listar_estancias')


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def realizar_checkout(request, estancia_id):
    """Finaliza una estancia activa y envia la habitacion a limpieza."""
    estancia = get_object_or_404(
        Estancia.objects.select_related('reserva', 'reserva__huesped', 'habitacion', 'folio'),
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
        except AppError as error:
            messages.error(request, error.message)
            return redirect('estancias:listar_estancias')

    return redirect('estancias:listar_estancias')
