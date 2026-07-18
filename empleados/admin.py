from django.contrib import admin

from empleados.models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codigo',
        'nombres',
        'apellidos',
        'cargo',
        'email',
        'estado',
        'activo',
        'fecha_ingreso',
        'creado_en',
        'actualizado_en',
    )
    list_filter = ('activo', 'estado', 'cargo', 'creado_en')
    search_fields = ('codigo', 'nombres', 'apellidos', 'email', 'cargo')
    ordering = ('apellidos', 'nombres')
    readonly_fields = ('creado_en', 'actualizado_en')
