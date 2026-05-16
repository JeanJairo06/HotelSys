from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.db.models import Q

from cuentas.models import UsuarioEmpleado
from cuentas.roles import ROLE_ADMIN
from empleados.models import Empleado


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs.update({'class': 'form-check-input'})
            else:
                widget.attrs.update({'class': 'form-control'})


class UsuarioCreateForm(BootstrapFormMixin, UserCreationForm):
    empleado = forms.ModelChoiceField(
        label='Empleado',
        queryset=Empleado.objects.none(),
        empty_label='Selecciona un empleado',
    )
    groups = forms.ModelMultipleChoiceField(
        label='Roles / grupos',
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    is_active = forms.BooleanField(label='Usuario activo', required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            'empleado',
            'username',
            'groups',
            'is_active',
        ]
        labels = {
            'username': 'Usuario',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empleado'].queryset = Empleado.objects.filter(cuenta_usuario__isnull=True).order_by('apellidos', 'nombres')
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self._apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        empleado = self.cleaned_data['empleado']
        user.first_name = empleado.nombres
        user.last_name = empleado.apellidos
        user.email = empleado.email
        user.is_staff = self.cleaned_data['groups'].filter(name=ROLE_ADMIN).exists()
        if commit:
            user.save()
            self.save_m2m()
            UsuarioEmpleado.objects.create(usuario=user, empleado=empleado)
        return user


class UsuarioUpdateForm(BootstrapFormMixin, forms.ModelForm):
    empleado = forms.ModelChoiceField(
        label='Empleado',
        queryset=Empleado.objects.none(),
        empty_label='Selecciona un empleado',
    )
    groups = forms.ModelMultipleChoiceField(
        label='Roles / grupos',
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = [
            'empleado',
            'username',
            'groups',
            'is_active',
        ]
        labels = {
            'username': 'Usuario',
            'is_active': 'Usuario activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        empleado_actual = None
        if self.instance and self.instance.pk:
            perfil = getattr(self.instance, 'perfil_empleado', None)
            if perfil:
                empleado_actual = perfil.empleado

        queryset = Empleado.objects.filter(cuenta_usuario__isnull=True)
        if empleado_actual:
            queryset = Empleado.objects.filter(Q(cuenta_usuario__isnull=True) | Q(pk=empleado_actual.pk))
            self.fields['empleado'].initial = empleado_actual

        self.fields['empleado'].queryset = queryset.order_by('apellidos', 'nombres')
        self._apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        empleado = self.cleaned_data['empleado']
        user.first_name = empleado.nombres
        user.last_name = empleado.apellidos
        user.email = empleado.email
        user.is_staff = self.cleaned_data['groups'].filter(name=ROLE_ADMIN).exists()
        if commit:
            user.save()
            self.save_m2m()
            UsuarioEmpleado.objects.update_or_create(
                usuario=user,
                defaults={'empleado': empleado},
            )
        return user
