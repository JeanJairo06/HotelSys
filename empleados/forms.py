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
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({'class': css_class})
        self.fields['fecha_ingreso'].input_formats = ['%Y-%m-%d']
