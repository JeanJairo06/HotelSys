from django.contrib import admin

from cuentas.models import UsuarioEmpleado


@admin.register(UsuarioEmpleado)
class UsuarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empleado', 'activo', 'creado_en', 'actualizado_en')
    list_filter = ('activo', 'creado_en')
    search_fields = ('usuario__username', 'empleado__codigo', 'empleado__nombres', 'empleado__apellidos')
    readonly_fields = ('creado_en', 'actualizado_en')
