from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from cuentas.decorators import role_required
from cuentas.roles import ROLE_ADMIN

from .forms import HotelForm
from .models import Hotel
from .services import guardar_hotel_desde_formulario


@role_required(ROLE_ADMIN)
def listar_hoteles(request):
    """Lista las sedes hoteleras administradas por el modulo."""
    hoteles = Hotel.objects.all()
    return render(request, 'hoteles/listar_hoteles.html', {'hoteles': hoteles})


@role_required(ROLE_ADMIN)
def crear_hotel(request):
    """Registra una sede hotelera."""
    if request.method == 'POST':
        form = HotelForm(request.POST)
        if form.is_valid():
            guardar_hotel_desde_formulario(form)
            messages.success(request, 'Hotel registrado correctamente.')
            return redirect('hoteles:listar_hoteles')
    else:
        form = HotelForm()

    return render(
        request,
        'hoteles/formulario_hotel.html',
        {'form': form, 'titulo': 'Registrar hotel'},
    )


@role_required(ROLE_ADMIN)
def editar_hotel(request, pk):
    """Actualiza la informacion de una sede hotelera."""
    hotel = get_object_or_404(Hotel, pk=pk)

    if request.method == 'POST':
        form = HotelForm(request.POST, instance=hotel)
        if form.is_valid():
            guardar_hotel_desde_formulario(form)
            messages.success(request, 'Hotel actualizado correctamente.')
            return redirect('hoteles:listar_hoteles')
    else:
        form = HotelForm(instance=hotel)

    return render(
        request,
        'hoteles/formulario_hotel.html',
        {'form': form, 'titulo': 'Editar hotel'},
    )
