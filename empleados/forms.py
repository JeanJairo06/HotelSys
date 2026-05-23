from datetime import date

from django import forms

from empleados.models import Empleado


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'codigo',
            'nombres',
            'apellidos',
            'cargo',
            'email',
            'telefono',
            'estado',
            'fecha_ingreso',
        ]
        labels = {
            'codigo': 'Código',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'cargo': 'Cargo',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'estado': 'Estado',
            'fecha_ingreso': 'Fecha de ingreso',
        }
        widgets = {
            'fecha_ingreso': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False

        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({'class': css_class})

        self.fields['codigo'].widget.attrs.update({
            'maxlength': '10',
            'readonly': 'readonly',
            'placeholder': 'Se generara automaticamente',
            'style': 'text-transform: uppercase;',
        })
        self.fields['telefono'].widget.attrs.update({
            'maxlength': '15',
            'inputmode': 'tel',
        })
        self.fields['fecha_ingreso'].widget.attrs.update({
            'max': date.today().isoformat(),
        })
        self.fields['fecha_ingreso'].input_formats = ['%Y-%m-%d']

    def clean_codigo(self):
        if self.instance and self.instance.pk:
            return self.instance.codigo

        return ''
