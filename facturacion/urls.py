from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('folios/', views.FolioListView.as_view(), name='folio_list'),
    path('folios/<int:pk>/', views.FolioDetailView.as_view(), name='folio_detail'),
    path('folios/<int:folio_id>/facturar/', views.FacturaCreateView.as_view(), name='factura_create'),

    path('folios/<int:folio_id>/agregar-cargo/', views.CargoEstanciaCreateView.as_view(), name='cargo_create'),
    path('tarifas/', views.TarifaListView.as_view(), name='tarifa_list'),
    path('tarifas/crear/', views.TarifaCreateView.as_view(), name='tarifa_create'),
    path('tarifas/<int:pk>/editar/', views.TarifaUpdateView.as_view(), name='tarifa_update'),
    path('tarifas/<int:pk>/eliminar/', views.TarifaDeleteView.as_view(), name='tarifa_delete'),
]