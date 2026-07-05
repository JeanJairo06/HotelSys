# Create your views here.
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView,DeleteView

from config.choices import EstadoFolio
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA

from .forms import FacturaEmisionForm, TarifaForm, CargoEstanciaForm
from .models import Factura, Folio
from django.db import models
from habitaciones.models import Tarifa
from estancias.models import CargoEstancia
@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class FolioListView(ListView):
    model = Folio
    template_name = 'facturacion/folio_list.html'
    context_object_name = 'folios'  
    paginate_by = 15

    def get_queryset(self):
        return Folio.objects.select_related(
            'estancia__reserva__huesped', 
            'estancia__habitacion'
        ).all()


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class FolioDetailView(DetailView):
    model = Folio
    template_name = 'facturacion/folio_detail.html'
    context_object_name = 'folio'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        
        queryset = queryset.select_related(
            'estancia__reserva__huesped',
            'estancia__habitacion'
        )
        folio = super().get_object(queryset)
        if folio:
            folio.calcular_totales()
        return folio

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = FacturaEmisionForm()
        context['cargo_form'] = CargoEstanciaForm()
        context['facturas'] = self.object.facturas.all()
        return context


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class FacturaCreateView(CreateView):
    model = Factura
    form_class = FacturaEmisionForm
    template_name = 'facturacion/folio_detail.html'

    def get_success_url(self):
        return reverse_lazy('facturacion:folio_detail', kwargs={'pk': self.kwargs['folio_id']})

    def form_valid(self, form):
        folio = Folio.objects.select_related('estancia__reserva__huesped').get(pk=self.kwargs['folio_id'])
        folio.calcular_totales()
        
        factura = form.save(commit=False)
        factura.folio = folio
        
        huesped = folio.estancia.reserva.huesped
        factura.ruc_dni = huesped.num_doc  
        
        if huesped.tipo_doc == 'RUC':
            factura.razon_social = huesped.razon_social 
        else:
            factura.razon_social = ""  
            
        factura.monto_subtotal = folio.subtotal
        factura.monto_igv = folio.igv
        factura.monto_total = folio.total
        factura.save()
        
        folio.estado = EstadoFolio.PAGADO
        folio.save()

        messages.success(self.request, f'Comprobante #{factura.id} emitido correctamente.')
        return super().form_valid(form)
    
@method_decorator(any_role_required(ROLE_ADMIN), name='dispatch')
class TarifaListView(ListView):
    model = Tarifa
    template_name = 'facturacion/tarifa_list.html'
    context_object_name = 'tarifas'
    paginate_by = 10

    def get_queryset(self):
        queryset = Tarifa.objects.select_related('tipo_habitacion').order_by('-fecha_inicio')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                models.Q(nombre__icontains=query) |
                models.Q(tipo_habitacion__nombre__icontains=query)
            )
        return queryset


@method_decorator(any_role_required(ROLE_ADMIN), name='dispatch')
class TarifaCreateView(CreateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'facturacion/tarifa_form.html'
    success_url = reverse_lazy('facturacion:tarifa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tarifa por temporada creada correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN), name='dispatch')
class TarifaUpdateView(UpdateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'facturacion/tarifa_form.html'
    success_url = reverse_lazy('facturacion:tarifa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tarifa por temporada actualizada correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN), name='dispatch')
class TarifaDeleteView(DeleteView):
    model = Tarifa
    template_name = 'facturacion/tarifa_confirm_delete.html'
    context_object_name = 'tarifa'
    success_url = reverse_lazy('facturacion:tarifa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tarifa eliminada correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class CargoEstanciaCreateView(CreateView):
    model = CargoEstancia
    form_class = CargoEstanciaForm
    template_name = 'facturacion/folio_detail.html'

    def get_success_url(self):
        return reverse_lazy('facturacion:folio_detail', kwargs={'pk': self.kwargs['folio_id']})

    def form_valid(self, form):
        # Recuperamos el folio directamente de forma nativa
        folio = Folio.objects.get(pk=self.kwargs['folio_id'])

        cargo = form.save(commit=False)
        cargo.estancia = folio.estancia
        cargo.save()

        folio.calcular_totales()

        messages.success(self.request, f"Cargo de '{cargo.concepto}' por S/ {cargo.monto} añadido correctamente.")
        return super().form_valid(form)