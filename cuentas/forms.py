from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from cuentas.roles import ROLE_ADMIN


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
    email = forms.EmailField(label='Correo electrónico', required=False)
    first_name = forms.CharField(label='Nombres', max_length=150, required=False)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=False)
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
            'username',
            'first_name',
            'last_name',
            'email',
            'groups',
            'is_active',
        ]
        labels = {
            'username': 'Usuario',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self._apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data['groups'].filter(name=ROLE_ADMIN).exists()
        if commit:
            user.save()
            self.save_m2m()
        return user


class UsuarioUpdateForm(BootstrapFormMixin, forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        label='Roles / grupos',
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'groups',
            'is_active',
        ]
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'is_active': 'Usuario activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data['groups'].filter(name=ROLE_ADMIN).exists()
        if commit:
            user.save()
            self.save_m2m()
        return user
