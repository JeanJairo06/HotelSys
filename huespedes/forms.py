from django import forms

from huespedes.models import Huesped


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
