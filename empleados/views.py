from django.contrib import messages
from django.db import models
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from cuentas.decorators import role_required
from cuentas.roles import ROLE_ADMIN
from empleados.forms import EmpleadoForm
from empleados.models import Empleado


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoListView(ListView):
    model = Empleado
    template_name = 'empleados/list.html'
    context_object_name = 'empleados'
    paginate_by = 10

    def get_queryset(self):
        queryset = Empleado.objects.order_by('apellidos', 'nombres')
        query = self.request.GET.get('q')

        if query:
            queryset = queryset.filter(
                models.Q(codigo__icontains=query)
                | models.Q(nombres__icontains=query)
                | models.Q(apellidos__icontains=query)
                | models.Q(cargo__icontains=query)
                | models.Q(email__icontains=query)
            )

        return queryset


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoDetailView(DetailView):
    model = Empleado
    template_name = 'empleados/detail.html'
    context_object_name = 'empleado'


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoCreateView(CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/form.html'
    success_url = reverse_lazy('empleados:list')

    def form_valid(self, form):
        messages.success(self.request, 'Empleado creado correctamente.')
        return super().form_valid(form)


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoUpdateView(UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/form.html'
    success_url = reverse_lazy('empleados:list')

    def form_valid(self, form):
        messages.success(self.request, 'Empleado actualizado correctamente.')
        return super().form_valid(form)


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoDeleteView(DeleteView):
    model = Empleado
    template_name = 'empleados/confirm_delete.html'
    context_object_name = 'empleado'
    success_url = reverse_lazy('empleados:list')

    def form_valid(self, form):
        messages.success(self.request, 'Empleado eliminado correctamente.')
        return super().form_valid(form)
