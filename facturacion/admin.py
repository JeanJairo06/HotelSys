from django.contrib import admin
from .models import Folio


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
    list_display = ('id', 'estancia', 'subtotal', 'igv', 'total', 'estado')
    search_fields = (
        'estancia__reserva__huesped__num_doc',
        'estancia__reserva__huesped__nombres',
        'estancia__reserva__huesped__apellidos',
    )
    list_filter = ('estado',)