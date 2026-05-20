# Create your views here.
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from config.choices import EstadoFolio
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA

from .forms import FacturaEmisionForm 
from .models import Factura, Folio


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
        folio = super().get_object(queryset)
        if folio:
            folio.calcular_totales()
        return folio

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = FacturaEmisionForm()
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
        folio = Folio.objects.get(pk=self.kwargs['folio_id'])
        folio.calcular_totales()
        factura = form.save(commit=False)
        factura.folio = folio
        factura.monto_subtotal = folio.subtotal
        factura.monto_igv = folio.igv
        factura.monto_total = folio.total
        factura.save()
        folio.estado = EstadoFolio.PAGADO
        folio.save()

        messages.success(self.request, f'Factura #{factura.id} emitida correctamente por S/ {factura.monto_total}')
        return super().form_valid(form)