from django.contrib import admin
from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'hotel',
        'huesped',
        'habitacion',
        'fecha_entrada',
        'fecha_salida',
        'num_adultos',
        'estado',
        'precio_total',
        'origen',
    )
    search_fields = (
        'huesped__num_doc',
        'huesped__nombres',
        'huesped__apellidos',
        'habitacion__numero',
        'hotel__nombre',
    )
    list_filter = ('estado', 'origen', 'hotel', 'fecha_entrada', 'fecha_salida')
    date_hierarchy = 'fecha_entrada'