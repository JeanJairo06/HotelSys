from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView, View
from django.shortcuts import redirect, get_object_or_404
from decimal import Decimal

from config.choices import EstadoFolio
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA

from .forms import FacturaEmisionForm, TarifaForm, CargoEstanciaForm
from .models import Factura, Folio, Pago
from habitaciones.models import Tarifa
from estancias.models import CargoEstancia

from .services import FolioService, PagoService
from core.exceptions import ReglaNegocioViolada

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cargo_form'] = CargoEstanciaForm()
        context['pagos'] = self.object.pagos.filter(activo=True)
        return context


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class CargoEstanciaCreateView(CreateView):
    model = CargoEstancia
    form_class = CargoEstanciaForm
    template_name = 'facturacion/folio_detail.html'

    def get_success_url(self):
        return reverse_lazy('facturacion:folio_detail', kwargs={'pk': self.kwargs['folio_id']})

    def form_valid(self, form):
        try:
            FolioService.registrar_cargo_extra(
                folio_id=self.kwargs['folio_id'],
                concepto=form.cleaned_data['concepto'],
                monto=form.cleaned_data['monto'],
                tipo=form.cleaned_data['tipo'],
                usuario=self.request.user
            )
            messages.success(self.request, 'Cargo adicional registrado y acumulado con éxito.')
        except ReglaNegocioViolada as e:
            messages.error(self.request, str(e))
        except Exception:
            messages.error(self.request, 'Ocurrió un error inesperado al registrar el cargo.')
            
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'Datos inválidos. El monto debe ser estrictamente positivo.')
        return redirect(reverse_lazy('facturacion:folio_detail', kwargs={'pk': self.kwargs['folio_id']}))


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class RegistrarPagoView(View):
    def post(self, request, folio_id):
        folio = get_object_or_404(Folio, pk=folio_id)
        monto_str = request.POST.get('monto')
        metodo_pago = request.POST.get('metodo_pago')

        try:
            monto = Decimal(monto_str)
            PagoService.registrar_pago_parcial(
                folio_id=folio_id,
                monto=monto,
                metodo_pago=metodo_pago,
                usuario=request.user
            )
            messages.success(request, f'¡Pago de S/ {monto} registrado correctamente!')
        except ReglaNegocioViolada as e:
            messages.error(request, str(e))
        except (ValueError, TypeError, KeyError):
            messages.error(request, 'El monto ingresado no posee un formato numérico válido.')
        except Exception:
            messages.error(request, 'Error interno del servidor al procesar el pago.')

        return redirect('facturacion:folio_detail', pk=folio_id)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class FacturaCreateView(CreateView):
    model = Factura
    form_class = FacturaEmisionForm
    template_name = 'facturacion/factura_form.html'

    def get_success_url(self):
        return reverse_lazy('facturacion:folio_detail', kwargs={'pk': self.kwargs['folio_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['folio'] = get_object_or_404(Folio, pk=self.kwargs['folio_id'])
        return context

    def form_valid(self, form):
        try:
            FolioService.emitir_comprobante_y_cerrar(
                folio_id=self.kwargs['folio_id'],
                ruc_dni=form.cleaned_data['ruc_dni'],
                razon_social=form.cleaned_data['razon_social'],
                usuario=self.request.user
            )
            messages.success(self.request, 'Comprobante emitido correctamente y Folio cerrado.')
        except ReglaNegocioViolada as e:
            messages.error(self.request, str(e))
            return redirect(self.get_success_url())
            
        return redirect(self.get_success_url())


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class TarifaListView(ListView):
    model = Tarifa
    template_name = 'facturacion/tarifa_list.html'
    context_object_name = 'tarifas'
    paginate_by = 10


@method_decorator(any_role_required(ROLE_ADMIN), name='dispatch')
class TarifaCreateView(CreateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'facturacion/tarifa_form.html'
    success_url = reverse_lazy('facturacion:tarifa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Nueva regla tarifaria guardada con éxito.')
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