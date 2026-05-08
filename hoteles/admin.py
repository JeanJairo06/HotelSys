from django.contrib import admin
from .models import Hotel


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ruc', 'direccion', 'estrellas', 'telefono')
    search_fields = ('nombre', 'ruc', 'telefono')
    list_filter = ('estrellas',)