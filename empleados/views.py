from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.exceptions import AppError
from cuentas.decorators import role_required
from cuentas.roles import ROLE_ADMIN
from empleados.forms import EmpleadoForm
from empleados.models import Empleado
from empleados.services import EmpleadoService


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoListView(ListView):
    model = Empleado
    template_name = 'empleados/list.html'
    context_object_name = 'empleados'
    paginate_by = 10

    def get_queryset(self):
        return EmpleadoService.empleados_queryset(q=self.request.GET.get('q'))


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoDetailView(DetailView):
    model = Empleado
    template_name = 'empleados/detail.html'
    context_object_name = 'empleado'

    def get_queryset(self):
        return EmpleadoService.detalle_queryset()


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoCreateView(CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/form.html'
    success_url = reverse_lazy('empleados:list')

    def form_valid(self, form):
        try:
            self.object = EmpleadoService.crear_empleado(
                data=form.cleaned_data,
                usuario_actor=self.request.user,
            )
        except AppError as error:
            form.add_error(None, error.message)
            return self.form_invalid(form)

        messages.success(self.request, 'Empleado creado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoUpdateView(UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/form.html'
    success_url = reverse_lazy('empleados:list')

    def form_valid(self, form):
        try:
            self.object = EmpleadoService.actualizar_empleado(
                empleado=self.object,
                data=form.cleaned_data,
                usuario_actor=self.request.user,
            )
        except AppError as error:
            form.add_error(None, error.message)
            return self.form_invalid(form)

        messages.success(self.request, 'Empleado actualizado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoDeleteView(DeleteView):
    model = Empleado
    template_name = 'empleados/confirm_delete.html'
    context_object_name = 'empleado'
    success_url = reverse_lazy('empleados:list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, 'No se puede eliminar el empleado porque tiene registros asociados.')
            return redirect(self.success_url)

        messages.success(self.request, 'Empleado eliminado correctamente.')
        return response
