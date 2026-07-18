from django.urls import path
#from . import views
from facturacion.views import (
    TarifaListView, TarifaCreateView, TarifaUpdateView, TarifaDeleteView,
    FolioListView, FolioDetailView, CargoEstanciaCreateView, FacturaCreateView,RegistrarPagoView
)
app_name = 'facturacion'

urlpatterns = [
    path('folios/', FolioListView.as_view(), name='folio_list'),
    path('folios/<int:pk>/', FolioDetailView.as_view(), name='folio_detail'),
    path('folios/<int:folio_id>/facturar/', FacturaCreateView.as_view(), name='factura_create'),
    path('folios/<int:folio_id>/agregar-cargo/', CargoEstanciaCreateView.as_view(), name='cargo_create'),
    path('folios/<int:folio_id>/registrar-pago/', RegistrarPagoView.as_view(), name='registrar_pago'),
    
    path('tarifas/', TarifaListView.as_view(), name='tarifa_list'),
    path('tarifas/crear/', TarifaCreateView.as_view(), name='tarifa_create'),
    path('tarifas/<int:pk>/editar/', TarifaUpdateView.as_view(), name='tarifa_update'),
    path('tarifas/<int:pk>/eliminar/', TarifaDeleteView.as_view(), name='tarifa_delete'),
]