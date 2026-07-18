from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.exceptions import AppError
from cuentas.decorators import role_required
from cuentas.models import UsuarioEmpleado
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perfil_usuario'] = UsuarioEmpleado.todos.select_related(
            'usuario',
            'creado_por',
        ).filter(empleado=self.object).first()
        return context


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

    def get_queryset(self):
        return EmpleadoService.detalle_queryset()

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


class EmpleadoEstadoMixin:
    model = Empleado
    context_object_name = 'empleado'
    success_url = reverse_lazy('empleados:list')

    def get_queryset(self):
        return EmpleadoService.detalle_queryset()


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoDeactivateView(EmpleadoEstadoMixin, DetailView):
    template_name = 'empleados/confirm_deactivate.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            EmpleadoService.desactivar_empleado(
                empleado=self.object,
                usuario_actor=request.user,
            )
        except AppError as error:
            messages.error(request, error.message)
            return self.get(request, *args, **kwargs)

        messages.success(request, 'Empleado desactivado correctamente.')
        return HttpResponseRedirect(self.success_url)


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class EmpleadoActivateView(EmpleadoEstadoMixin, DetailView):
    template_name = 'empleados/confirm_activate.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            EmpleadoService.activar_empleado(
                empleado=self.object,
                usuario_actor=request.user,
            )
        except AppError as error:
            messages.error(request, error.message)
            return self.get(request, *args, **kwargs)

        messages.success(request, 'Empleado activado correctamente.')
        return HttpResponseRedirect(self.success_url)
