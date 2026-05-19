from django import forms

from .models import Hotel


class HotelForm(forms.ModelForm):
    """Formulario para crear y editar sedes hoteleras."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)

    class Meta:
        model = Hotel
        fields = ['nombre', 'ruc', 'direccion', 'estrellas', 'telefono']
        labels = {
            'nombre': 'Nombre',
            'ruc': 'RUC',
            'direccion': 'Direccion',
            'estrellas': 'Estrellas',
            'telefono': 'Telefono',
        }
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
