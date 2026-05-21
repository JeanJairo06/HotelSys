from django.contrib import messages
from datetime import date, datetime, timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from config.choices import EstadoReserva
from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from habitaciones.models import Habitacion, TipoHabitacion
from reservas.forms import ReservaForm
from reservas.models import Reserva


def _parse_date(value, default):
    if not value:
        return default
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return default


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


class ReservaFormContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reserva_id'] = self.object.pk if getattr(self, 'object', None) else ''
        return context


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaDetailView(DetailView):
    model = Reserva
    template_name = 'reservas/detail.html'
    context_object_name = 'reserva'
    queryset = Reserva.objects.select_related('hotel', 'huesped', 'habitacion', 'habitacion__tipo')


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaCreateView(ReservaFormContextMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/form.html'
    success_url = reverse_lazy('reservas:list')

    def form_valid(self, form):
        messages.success(self.request, 'Reserva creada correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaUpdateView(ReservaFormContextMixin, UpdateView):
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


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class ReservaCalendarView(TemplateView):
    template_name = 'reservas/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inicio = _parse_date(self.request.GET.get('desde'), date.today())
        fin = _parse_date(self.request.GET.get('hasta'), inicio + timedelta(days=13))

        if fin < inicio:
            fin = inicio + timedelta(days=13)

        dias = [inicio + timedelta(days=offset) for offset in range((fin - inicio).days + 1)]
        habitaciones = Habitacion.objects.select_related('hotel', 'tipo').order_by(
            'piso',
            'numero',
        )
        tipo = self.request.GET.get('tipo')

        if tipo:
            habitaciones = habitaciones.filter(tipo_id=tipo)

        reservas = Reserva.objects.select_related('huesped', 'habitacion').filter(
            habitacion__in=habitaciones,
            fecha_entrada__lte=fin,
            fecha_salida__gt=inicio,
        ).exclude(
            estado__in=[EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA],
        )

        reservas_por_habitacion = {}
        for reserva in reservas:
            reservas_por_habitacion.setdefault(reserva.habitacion_id, []).append(reserva)

        filas = []
        for habitacion in habitaciones:
            celdas = []
            reservas_habitacion = reservas_por_habitacion.get(habitacion.id, [])
            for dia in dias:
                reserva_dia = next(
                    (
                        reserva for reserva in reservas_habitacion
                        if reserva.fecha_entrada <= dia < reserva.fecha_salida
                    ),
                    None,
                )
                celdas.append({'fecha': dia, 'reserva': reserva_dia})
            filas.append({'habitacion': habitacion, 'celdas': celdas})

        context.update({
            'dias': dias,
            'filas': filas,
            'tipos_habitacion': TipoHabitacion.objects.order_by('nombre'),
            'desde': inicio,
            'hasta': fin,
        })
        return context
