from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.exceptions import AppError
from cuentas.decorators import role_required
from cuentas.forms import UsuarioCreateForm, UsuarioUpdateForm
from cuentas.models import UsuarioEmpleado
from cuentas.roles import ROLE_ADMIN
from cuentas.security import LoginAttemptRateLimiter
from cuentas.session_policy import get_session_policy
from cuentas.session_state import (
    get_session_expires_at,
    refresh_session_activity,
)
from cuentas.services import UsuarioService


class CuentaLoginView(LoginView):
    template_name = 'cuentas/login.html'
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        self.login_rate_limiter = LoginAttemptRateLimiter(request)
        if self.login_rate_limiter.allow_attempt():
            return super().post(request, *args, **kwargs)

        form = self.get_form()
        form.add_error(None, form.error_messages['invalid_login'])
        return self.form_invalid(form)

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('home')

    def form_valid(self, form):
        self.login_rate_limiter.reset()
        response = super().form_valid(form)
        messages.success(self.request, 'Inicio de sesión correcto.')
        return response

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


class SessionActivityView(View):
    http_method_names = ['post', 'options']

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    'detail': 'La sesión ha expirado.',
                    'code': 'session_expired',
                },
                status=401,
            )

        policy = get_session_policy(request.user)
        refresh_session_activity(request)
        return JsonResponse({'expires_at': get_session_expires_at(request, policy)})


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioListView(ListView):
    model = User
    template_name = 'cuentas/usuarios/list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        return UsuarioService.usuarios_queryset()


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioDetailView(DetailView):
    model = User
    template_name = 'cuentas/usuarios/detail.html'
    context_object_name = 'usuario'

    def get_queryset(self):
        return UsuarioService.detalle_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perfil_usuario'] = UsuarioEmpleado.todos.select_related(
            'empleado',
            'creado_por',
        ).filter(usuario=self.object).first()
        return context


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioCreateView(CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = 'cuentas/usuarios/form.html'
    success_url = reverse_lazy('usuarios:list')

    def form_valid(self, form):
        try:
            self.object = form.save(usuario_actor=self.request.user)
        except AppError as error:
            form.add_error(None, error.message)
            return self.form_invalid(form)

        messages.success(self.request, 'Usuario creado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioUpdateView(UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = 'cuentas/usuarios/form.html'
    success_url = reverse_lazy('usuarios:list')

    def form_valid(self, form):
        try:
            self.object = form.save(usuario_actor=self.request.user)
        except AppError as error:
            form.add_error(None, error.message)
            return self.form_invalid(form)

        messages.success(self.request, 'Usuario actualizado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioDeactivateView(DeleteView):
    model = User
    template_name = 'cuentas/usuarios/confirm_deactivate.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('usuarios:list')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object == request.user:
            messages.error(request, 'No puedes desactivar tu propio usuario.')
            return self.get(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            UsuarioService.desactivar_usuario(
                user=self.object,
                usuario_actor=self.request.user,
            )
        except AppError as error:
            messages.error(self.request, error.message)
            return self.get(self.request, *self.args, **self.kwargs)

        messages.success(self.request, 'Usuario desactivado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioActivateView(DetailView):
    model = User
    template_name = 'cuentas/usuarios/confirm_activate.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('usuarios:list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            UsuarioService.reactivar_usuario(
                user=self.object,
                usuario_actor=request.user,
            )
        except AppError as error:
            messages.error(request, error.message)
            return self.get(request, *args, **kwargs)

        messages.success(request, 'Usuario activado correctamente.')
        return HttpResponseRedirect(self.success_url)
