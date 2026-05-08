from django.contrib import admin
from .models import TipoHabitacion, Habitacion, Tarifa


@admin.register(TipoHabitacion)
class TipoHabitacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'precio_base')
    search_fields = ('nombre',)
    list_filter = ('capacidad',)


@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'hotel', 'tipo', 'piso', 'estado')
    search_fields = ('numero', 'hotel__nombre', 'tipo__nombre')
    list_filter = ('estado', 'hotel', 'tipo', 'piso')


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_habitacion', 'precio_noche', 'fecha_inicio', 'fecha_fin')
    search_fields = ('nombre', 'tipo_habitacion__nombre')
    list_filter = ('tipo_habitacion', 'fecha_inicio', 'fecha_fin')