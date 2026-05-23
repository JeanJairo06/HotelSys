from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from config.choices import EstadoHabitacion
from cuentas.decorators import any_role_required, role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from hoteles.models import Hotel

from .forms import EstadoHabitacionForm, HabitacionForm, TipoHabitacionForm
from .models import Habitacion, TipoHabitacion
from .services import cambiar_estado_manual


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def listar_habitaciones(request):
    """Muestra el panel operativo de habitaciones con filtros y contadores por estado."""
    habitaciones_base = Habitacion.objects.select_related('hotel', 'tipo').order_by('piso', 'numero')
    habitaciones = habitaciones_base

    hotel_id = request.GET.get('hotel')
    tipo_id = request.GET.get('tipo')
    estado = request.GET.get('estado')
    piso = request.GET.get('piso')

    if hotel_id:
        habitaciones = habitaciones.filter(hotel_id=hotel_id)
    if tipo_id:
        habitaciones = habitaciones.filter(tipo_id=tipo_id)
    if estado:
        habitaciones = habitaciones.filter(estado=estado)
    if piso:
        habitaciones = habitaciones.filter(piso=piso)

    contexto = {
        'habitaciones': habitaciones,
        'hoteles': Hotel.objects.all(),
        'tipos_habitacion': TipoHabitacion.objects.all(),
        'estados': Habitacion._meta.get_field('estado').choices,
        'pisos': Habitacion.objects.order_by('piso').values_list('piso', flat=True).distinct(),
        'total_disponibles': habitaciones_base.filter(estado=EstadoHabitacion.DISPONIBLE).count(),
        'total_ocupadas': habitaciones_base.filter(estado=EstadoHabitacion.OCUPADA).count(),
        'total_limpieza': habitaciones_base.filter(estado=EstadoHabitacion.LIMPIEZA).count(),
        'total_mantenimiento': habitaciones_base.filter(estado=EstadoHabitacion.MANTENIMIENTO).count(),
    }
    return render(request, 'habitaciones/listar_habitaciones.html', contexto)


@role_required(ROLE_ADMIN)
def crear_habitacion(request):
    """Registra una nueva habitacion fisica del hotel."""
    hotel = Hotel.objects.order_by('id').first()

    if request.method == 'POST':
        form = HabitacionForm(request.POST, hotel=hotel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitacion registrada correctamente.')
            return redirect('habitaciones:listar_habitaciones')
    else:
        form = HabitacionForm(hotel=hotel)

    return render(
        request,
        'habitaciones/formulario_habitacion.html',
        {'form': form, 'titulo': 'Registrar habitacion', 'hotel': hotel},
    )


@role_required(ROLE_ADMIN)
def editar_habitacion(request, pk):
    """Actualiza los datos generales de una habitacion existente."""
    habitacion = get_object_or_404(Habitacion, pk=pk)
    hotel = Hotel.objects.order_by('id').first() or habitacion.hotel

    if request.method == 'POST':
        form = HabitacionForm(request.POST, instance=habitacion, hotel=hotel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitacion actualizada correctamente.')
            return redirect('habitaciones:listar_habitaciones')
    else:
        form = HabitacionForm(instance=habitacion, hotel=hotel)

    return render(
        request,
        'habitaciones/formulario_habitacion.html',
        {'form': form, 'titulo': 'Editar habitacion', 'hotel': hotel},
    )


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def cambiar_estado_habitacion(request, pk):
    """Cambia el estado manual de una habitacion respetando reglas de ocupacion."""
    habitacion = get_object_or_404(Habitacion.objects.select_related('hotel', 'tipo'), pk=pk)

    if request.method == 'POST':
        form = EstadoHabitacionForm(request.POST, instance=habitacion)
        if form.is_valid():
            try:
                cambiar_estado_manual(habitacion, form.cleaned_data['estado'])
                messages.success(request, 'Estado de habitacion actualizado correctamente.')
                return redirect('habitaciones:listar_habitaciones')
            except ValidationError as error:
                messages.error(request, error.messages[0])
    else:
        form = EstadoHabitacionForm(instance=habitacion)

    return render(
        request,
        'habitaciones/cambiar_estado_habitacion.html',
        {'form': form, 'habitacion': habitacion},
    )


@any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA)
def listar_tipos_habitacion(request):
    """Lista las categorias de habitacion usadas por el modulo operativo."""
    tipos_habitacion = TipoHabitacion.objects.all()
    return render(
        request,
        'habitaciones/listar_tipos_habitacion.html',
        {'tipos_habitacion': tipos_habitacion},
    )


@role_required(ROLE_ADMIN)
def crear_tipo_habitacion(request):
    """Crea un tipo de habitacion con capacidad, precio base y amenidades."""
    if request.method == 'POST':
        form = TipoHabitacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de habitacion registrado correctamente.')
            return redirect('habitaciones:listar_tipos_habitacion')
    else:
        form = TipoHabitacionForm()

    return render(
        request,
        'habitaciones/formulario_tipo_habitacion.html',
        {'form': form, 'titulo': 'Registrar tipo de habitacion'},
    )


@role_required(ROLE_ADMIN)
def editar_tipo_habitacion(request, pk):
    """Edita un tipo de habitacion existente."""
    tipo_habitacion = get_object_or_404(TipoHabitacion, pk=pk)

    if request.method == 'POST':
        form = TipoHabitacionForm(request.POST, instance=tipo_habitacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de habitacion actualizado correctamente.')
            return redirect('habitaciones:listar_tipos_habitacion')
    else:
        form = TipoHabitacionForm(instance=tipo_habitacion)

    return render(
        request,
        'habitaciones/formulario_tipo_habitacion.html',
        {'form': form, 'titulo': 'Editar tipo de habitacion'},
    )
