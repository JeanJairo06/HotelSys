from django.contrib import admin
from .models import Estancia, CargoEstancia


@admin.register(Estancia)
class EstanciaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reserva',
        'habitacion',
        'fecha_checkin',
        'fecha_checkout',
        'precio_final',
        'estado',
    )
    search_fields = (
        'reserva__huesped__num_doc',
        'reserva__huesped__nombres',
        'reserva__huesped__apellidos',
        'habitacion__numero',
    )
    list_filter = ('estado', 'fecha_checkin', 'fecha_checkout')
    date_hierarchy = 'fecha_checkin'


@admin.register(CargoEstancia)
class CargoEstanciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'estancia', 'concepto', 'monto', 'fecha', 'tipo')
    search_fields = ('concepto', 'estancia__reserva__huesped__num_doc')
    list_filter = ('tipo', 'fecha')
    date_hierarchy = 'fecha'