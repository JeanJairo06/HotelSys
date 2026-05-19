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
            'email',
            'telefono',
            'nacionalidad',
        ]
        labels = {
            'tipo_doc': 'Tipo de documento',
            'num_doc': 'Numero de documento',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'email': 'Correo electronico',
            'telefono': 'Telefono',
            'nacionalidad': 'Nacionalidad',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({'class': css_class})
