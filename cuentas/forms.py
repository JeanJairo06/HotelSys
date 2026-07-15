from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from cuentas.services import UsuarioService
from cuentas.roles import SYSTEM_ROLES
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
        queryset=Group.objects.filter(name__in=SYSTEM_ROLES),
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
        empleado_id = self.data.get(self.add_prefix('empleado')) if self.is_bound else None
        self.fields['empleado'].queryset = UsuarioService.empleados_disponibles_queryset(
            empleado_id=empleado_id,
        )
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self._apply_bootstrap()
        self.fields['empleado'].widget.attrs.update({'class': 'form-select js-empleado-select'})

    def save(self, commit=True, usuario_actor=None):
        if not commit:
            return super().save(commit=False)

        return UsuarioService.crear_usuario(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            empleado=self.cleaned_data['empleado'],
            groups=self.cleaned_data['groups'],
            is_active=self.cleaned_data['is_active'],
            usuario_actor=usuario_actor,
        )


class UsuarioUpdateForm(BootstrapFormMixin, forms.ModelForm):
    empleado = forms.ModelChoiceField(
        label='Empleado',
        queryset=Empleado.objects.none(),
        empty_label='Selecciona un empleado',
    )
    groups = forms.ModelMultipleChoiceField(
        label='Roles / grupos',
        queryset=Group.objects.filter(name__in=SYSTEM_ROLES),
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

        empleado_id = self.data.get(self.add_prefix('empleado')) if self.is_bound else None
        if empleado_actual:
            self.fields['empleado'].initial = empleado_actual

        self.fields['empleado'].queryset = UsuarioService.empleados_disponibles_queryset(
            empleado_actual=empleado_actual,
            empleado_id=empleado_id,
        )
        self._apply_bootstrap()
        self.fields['empleado'].widget.attrs.update({'class': 'form-select js-empleado-select'})

    def save(self, commit=True, usuario_actor=None):
        if not commit:
            return super().save(commit=False)

        return UsuarioService.actualizar_usuario(
            user=self.instance,
            username=self.cleaned_data['username'],
            empleado=self.cleaned_data['empleado'],
            groups=self.cleaned_data['groups'],
            is_active=self.cleaned_data['is_active'],
            usuario_actor=usuario_actor,
        )
