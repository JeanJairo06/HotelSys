from django.contrib import admin
from .models import Huesped


@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ('num_doc', 'tipo_doc', 'apellidos', 'nombres', 'email', 'telefono', 'nacionalidad')
    search_fields = ('num_doc', 'nombres', 'apellidos', 'email')
    list_filter = ('tipo_doc', 'nacionalidad')