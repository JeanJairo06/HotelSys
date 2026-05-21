from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from config.choices import EstadoReserva
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from reservas.forms import ReservaForm
from reservas.models import Reserva


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaListView(ListView):
    model = Reserva
    template_name = 'reservas/list.html'
    context_object_name = 'reservas'
    paginate_by = 10

    def get_queryset(self):
        queryset = Reserva.objects.select_related(
            'hotel',
            'huesped',
            'habitacion',
            'habitacion__tipo',
        ).order_by('-fecha_entrada', '-id')
        query = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        desde = self.request.GET.get('desde')
        hasta = self.request.GET.get('hasta')

        if query:
            filters = (
                Q(huesped__num_doc__icontains=query)
                | Q(huesped__nombres__icontains=query)
                | Q(huesped__apellidos__icontains=query)
                | Q(habitacion__numero__icontains=query)
                | Q(hotel__nombre__icontains=query)
            )
            if query.isdigit():
                filters |= Q(id=int(query))
            queryset = queryset.filter(filters)

        if estado:
            queryset = queryset.filter(estado=estado)

        if desde:
            queryset = queryset.filter(fecha_entrada__gte=desde)

        if hasta:
            queryset = queryset.filter(fecha_entrada__lte=hasta)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados_reserva'] = EstadoReserva.choices
        return context


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaCreateView(CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/form.html'
    success_url = reverse_lazy('reservas:list')

    def form_valid(self, form):
        messages.success(self.request, 'Reserva creada correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaUpdateView(UpdateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/form.html'
    success_url = reverse_lazy('reservas:list')

    def form_valid(self, form):
        messages.success(self.request, 'Reserva actualizada correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaCancelView(View):
    def post(self, request, pk):
        reserva = get_object_or_404(Reserva, pk=pk)

        if reserva.estado in [EstadoReserva.CHECKIN, EstadoReserva.FINALIZADA]:
            messages.error(request, 'No se puede cancelar una reserva con check-in o finalizada.')
            return redirect('reservas:list')

        if reserva.estado == EstadoReserva.CANCELADA:
            messages.info(request, 'La reserva ya estaba cancelada.')
            return redirect('reservas:list')

        reserva.estado = EstadoReserva.CANCELADA
        reserva.save(update_fields=['estado'])
        messages.success(request, 'Reserva cancelada correctamente.')
        return redirect('reservas:list')
