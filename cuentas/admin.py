from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from cuentas.models import UsuarioEmpleado


class UsuarioEmpleadoInline(admin.StackedInline):
    model = UsuarioEmpleado
    fk_name = 'usuario'
    can_delete = False
    extra = 0
    fields = ('empleado', 'activo', 'creado_por', 'creado_en', 'actualizado_en')
    readonly_fields = ('creado_en', 'actualizado_en')


@admin.register(UsuarioEmpleado)
class UsuarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empleado', 'activo', 'creado_en', 'actualizado_en')
    list_filter = ('activo', 'creado_en')
    search_fields = ('usuario__username', 'empleado__codigo', 'empleado__nombres', 'empleado__apellidos')
    readonly_fields = ('creado_en', 'actualizado_en')


admin.site.unregister(User)


@admin.register(User)
class HotelSysUserAdmin(UserAdmin):
    inlines = (UsuarioEmpleadoInline,)
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'empleado_vinculado',
        'perfil_activo',
        'perfil_creado_en',
        'perfil_actualizado_en',
    )
    list_select_related = ('perfil_empleado__empleado',)

    @admin.display(description='Empleado', ordering='perfil_empleado__empleado__apellidos')
    def empleado_vinculado(self, obj):
        perfil = self._perfil(obj)
        if not perfil:
            return '-'
        return perfil.empleado.nombre_completo

    @admin.display(description='Perfil activo', boolean=True, ordering='perfil_empleado__activo')
    def perfil_activo(self, obj):
        perfil = self._perfil(obj)
        return perfil.activo if perfil else None

    @admin.display(description='Perfil creado', ordering='perfil_empleado__creado_en')
    def perfil_creado_en(self, obj):
        perfil = self._perfil(obj)
        return perfil.creado_en if perfil else None

    @admin.display(description='Perfil actualizado', ordering='perfil_empleado__actualizado_en')
    def perfil_actualizado_en(self, obj):
        perfil = self._perfil(obj)
        return perfil.actualizado_en if perfil else None

    def _perfil(self, obj):
        return UsuarioEmpleado.todos.select_related('empleado').filter(usuario=obj).first()
