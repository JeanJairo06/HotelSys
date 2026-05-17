from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@method_decorator(
    any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA, ROLE_HOUSEKEEPING),
    name='dispatch',
)
class DashboardView(TemplateView):
    template_name = 'pages/dashboard.html'


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
