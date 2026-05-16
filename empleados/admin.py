from django.contrib import admin

from empleados.models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombres', 'apellidos', 'cargo', 'email', 'estado', 'fecha_ingreso')
    list_filter = ('estado', 'cargo')
    search_fields = ('codigo', 'nombres', 'apellidos', 'email', 'cargo')
    ordering = ('apellidos', 'nombres')
