from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from cuentas.decorators import role_required
from cuentas.forms import UsuarioCreateForm, UsuarioUpdateForm
from cuentas.roles import ROLE_ADMIN


class CuentaLoginView(LoginView):
    template_name = 'cuentas/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Inicio de sesión correcto.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña inválidos.')
        return super().form_invalid(form)


class CuentaLogoutView(LogoutView):
    http_method_names = ['post', 'options']
    next_page = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, 'Sesión cerrada correctamente.')
        return response


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioListView(ListView):
    model = User
    template_name = 'cuentas/usuarios/list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        return User.objects.select_related('perfil_empleado__empleado').prefetch_related('groups').order_by('username')


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioDetailView(DetailView):
    model = User
    template_name = 'cuentas/usuarios/detail.html'
    context_object_name = 'usuario'

    def get_queryset(self):
        return User.objects.select_related('perfil_empleado__empleado').prefetch_related('groups')


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioCreateView(CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = 'cuentas/usuarios/form.html'
    success_url = reverse_lazy('usuarios:list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario creado correctamente.')
        return super().form_valid(form)


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioUpdateView(UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = 'cuentas/usuarios/form.html'
    success_url = reverse_lazy('usuarios:list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado correctamente.')
        return super().form_valid(form)


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioDeleteView(DeleteView):
    model = User
    template_name = 'cuentas/usuarios/confirm_delete.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('usuarios:list')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object == request.user:
            messages.error(request, 'No puedes eliminar tu propio usuario.')
            return self.get(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Usuario eliminado correctamente.')
        return super().form_valid(form)
