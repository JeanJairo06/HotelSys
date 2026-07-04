from datetime import date

from django import forms

from config.choices import TipoDocumento
from huespedes.models import Huesped
from huespedes.services import crear_huesped, editar_huesped


class HuespedForm(forms.ModelForm):
    class Meta:
        model = Huesped
        fields = [
            'tipo_doc',
            'num_doc',
            'nombres',
            'apellidos',
            'razon_social',
            'fecha_nacimiento',
            'email',
            'telefono',
            'nacionalidad',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'tipo_doc': 'Tipo de documento',
            'num_doc': 'Numero de documento',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'razon_social': 'Razon social',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'email': 'Correo electronico',
            'telefono': 'Telefono',
            'nacionalidad': 'Nacionalidad',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('nombres', 'apellidos', 'razon_social', 'fecha_nacimiento'):
            self.fields[field_name].required = False

        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({'class': css_class})

        self.fields['num_doc'].widget.attrs.update({
            'maxlength': '11',
            'inputmode': 'numeric',
        })
        self.fields['telefono'].widget.attrs.update({
            'maxlength': '20',
            'inputmode': 'tel',
        })
        hoy = date.today()
        try:
            fecha_maxima = hoy.replace(year=hoy.year - 18)
        except ValueError:
            fecha_maxima = hoy.replace(year=hoy.year - 18, day=28)

        self.fields['fecha_nacimiento'].widget.attrs.update({
            'max': fecha_maxima.isoformat(),
        })

    def clean_razon_social(self):
        tipo_doc = self.cleaned_data.get('tipo_doc')
        razon_social = self.cleaned_data.get('razon_social')

        if tipo_doc == TipoDocumento.DNI:
            return ''

        return razon_social

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        datos = {
            campo: self.cleaned_data[campo]
            for campo in self.Meta.fields
        }

        if self.instance and self.instance.pk:
            return editar_huesped(self.instance, usuario=getattr(self, 'usuario', None), **datos)

        return crear_huesped(usuario=getattr(self, 'usuario', None), **datos)
