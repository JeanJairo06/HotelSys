from django.contrib import admin

from cuentas.models import UsuarioEmpleado


@admin.register(UsuarioEmpleado)
class UsuarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empleado')
    search_fields = ('usuario__username', 'empleado__codigo', 'empleado__nombres', 'empleado__apellidos')
