from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('folios/', views.FolioListView.as_view(), name='folio_list'),
    path('folios/<int:pk>/', views.FolioDetailView.as_view(), name='folio_detail'),
    path('folios/<int:folio_id>/facturar/', views.FacturaCreateView.as_view(), name='factura_create'),
]