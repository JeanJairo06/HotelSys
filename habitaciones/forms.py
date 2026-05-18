from django import forms

from .models import Habitacion, TipoHabitacion


class TipoHabitacionForm(forms.ModelForm):
    """Formulario para registrar categorias de habitacion."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)

    class Meta:
        model = TipoHabitacion
        fields = ['nombre', 'capacidad', 'precio_base', 'amenidades']
        labels = {
            'nombre': 'Nombre',
            'capacidad': 'Capacidad',
            'precio_base': 'Precio base',
            'amenidades': 'Amenidades',
        }
        widgets = {
            'amenidades': forms.Textarea(attrs={'rows': 3}),
        }


class HabitacionForm(forms.ModelForm):
    """Formulario para crear o editar habitaciones fisicas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)

    class Meta:
        model = Habitacion
        fields = ['hotel', 'tipo', 'numero', 'piso', 'estado']
        labels = {
            'hotel': 'Hotel',
            'tipo': 'Tipo de habitacion',
            'numero': 'Numero',
            'piso': 'Piso',
            'estado': 'Estado',
        }


class EstadoHabitacionForm(forms.ModelForm):
    """Formulario pequeno para cambiar solo el estado operativo de una habitacion."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)

    class Meta:
        model = Habitacion
        fields = ['estado']
        labels = {
            'estado': 'Estado',
        }
