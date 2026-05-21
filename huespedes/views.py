from django.contrib import messages
from django.db import models
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from cuentas.decorators import any_role_required
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from huespedes.forms import HuespedForm
from huespedes.models import Huesped


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class HuespedListView(ListView):
    model = Huesped
    template_name = 'huespedes/list.html'
    context_object_name = 'huespedes'
    paginate_by = 10

    def get_queryset(self):
        queryset = Huesped.objects.order_by('apellidos', 'nombres')
        query = self.request.GET.get('q')

        if query:
            queryset = queryset.filter(
                models.Q(num_doc__icontains=query)
                | models.Q(nombres__icontains=query)
                | models.Q(apellidos__icontains=query)
                | models.Q(razon_social__icontains=query)
                | models.Q(email__icontains=query)
                | models.Q(telefono__icontains=query)
                | models.Q(nacionalidad__icontains=query)
            )

        return queryset


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class HuespedDetailView(DetailView):
    model = Huesped
    template_name = 'huespedes/detail.html'
    context_object_name = 'huesped'


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class HuespedCreateView(CreateView):
    model = Huesped
    form_class = HuespedForm
    template_name = 'huespedes/form.html'
    success_url = reverse_lazy('huespedes:list')

    def form_valid(self, form):
        messages.success(self.request, 'Huesped registrado correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class HuespedUpdateView(UpdateView):
    model = Huesped
    form_class = HuespedForm
    template_name = 'huespedes/form.html'
    success_url = reverse_lazy('huespedes:list')

    def form_valid(self, form):
        messages.success(self.request, 'Huesped actualizado correctamente.')
        return super().form_valid(form)


@method_decorator(any_role_required(ROLE_ADMIN, ROLE_RECEPCIONISTA), name='dispatch')
class HuespedDeleteView(DeleteView):
    model = Huesped
    template_name = 'huespedes/confirm_delete.html'
    context_object_name = 'huesped'
    success_url = reverse_lazy('huespedes:list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, 'No se puede eliminar el huesped porque tiene registros asociados.')
            return redirect(self.success_url)

        messages.success(self.request, 'Huesped eliminado correctamente.')
        return response
