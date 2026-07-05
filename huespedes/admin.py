from django.contrib import admin
from .models import Huesped


@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'num_doc',
        'tipo_doc',
        'apellidos',
        'nombres',
        'razon_social',
        'fecha_nacimiento',
        'email',
        'telefono',
        'nacionalidad',
    )
    search_fields = ('num_doc', 'nombres', 'apellidos', 'razon_social', 'email')
    list_filter = ('tipo_doc', 'nacionalidad')
