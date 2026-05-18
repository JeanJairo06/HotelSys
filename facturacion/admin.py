from django.contrib import admin
from .models import Folio, Factura


class FacturaInline(admin.TabularInline):
    model = Factura
    extra = 0
    readonly_fields = ('monto_subtotal', 'monto_igv', 'monto_total', 'fecha_emision')
    can_delete = False


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
    list_display = ('id', 'estancia', 'subtotal', 'igv', 'total', 'estado')
    search_fields = (
        'estancia__reserva__huesped__num_doc',
        'estancia__reserva__huesped__nombres',
        'estancia__reserva__huesped__apellidos',
    )
    list_filter = ('estado',)
    readonly_fields = ('subtotal', 'igv', 'total')
    inlines = [FacturaInline]


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'folio', 'ruc_dni', 'razon_social', 'monto_total', 'fecha_emision')
    search_fields = ('ruc_dni', 'razon_social', 'folio__id')
    list_filter = ('fecha_emision',)
    readonly_fields = ('folio', 'ruc_dni', 'razon_social', 'monto_subtotal', 'monto_igv', 'monto_total', 'fecha_emision')

    def has_add_permission(self, request):
        
        return False