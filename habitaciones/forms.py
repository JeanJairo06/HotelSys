from django import forms

from hoteles.models import Hotel

from .models import Habitacion, TipoHabitacion


AMENIDADES_ORDEN = [
    'Wifi',
    'TV',
    'Aire acondicionado',
    'Minibar',
    'Jacuzzi',
    'Caja fuerte',
    'Escritorio',
    'Balcon',
    'Vista exterior',
]


class TipoHabitacionForm(forms.ModelForm):
    """Formulario para registrar categorias de habitacion."""

    amenidades = forms.MultipleChoiceField(
        label='Amenidades',
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        amenidades_registradas = self._amenidades_registradas()
        if self.instance and self.instance.amenidades:
            amenidades = self.instance.amenidades_lista
            amenidades_registradas.update(amenidades)
            self.fields['amenidades'].initial = amenidades
            self.initial['amenidades'] = amenidades
        self.fields['amenidades'].choices = [
            (amenidad, amenidad)
            for amenidad in sorted(
                amenidades_registradas,
                key=lambda amenidad: AMENIDADES_ORDEN.index(amenidad) if amenidad in AMENIDADES_ORDEN else len(AMENIDADES_ORDEN),
            )
        ]
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                css_class = 'amenities-options'
            else:
                css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)

    def clean_amenidades(self):
        return self.cleaned_data.get('amenidades', [])

    @staticmethod
    def _amenidades_registradas():
        amenidades = set()
        for tipo in TipoHabitacion.objects.all():
            amenidades.update(tipo.amenidades_lista)
        return amenidades

    class Meta:
        model = TipoHabitacion
        fields = ['nombre', 'capacidad', 'precio_base', 'amenidades']
        labels = {
            'nombre': 'Nombre',
            'capacidad': 'Capacidad',
            'precio_base': 'Precio base',
            'amenidades': 'Amenidades',
        }


class HabitacionForm(forms.ModelForm):
    """Formulario para crear o editar habitaciones fisicas."""

    def __init__(self, *args, **kwargs):
        hotel = kwargs.pop('hotel', None)
        instance = kwargs.get('instance')
        self.hotel = hotel or getattr(instance, 'hotel', None) or Hotel.objects.order_by('id').first()
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)

    def clean(self):
        cleaned_data = super().clean()
        if not self.hotel:
            raise forms.ValidationError('Debe existir un hotel registrado antes de crear habitaciones.')
        return cleaned_data

    def save(self, commit=True):
        habitacion = super().save(commit=False)
        if self.hotel:
            habitacion.hotel = self.hotel
        if commit:
            habitacion.save()
            self.save_m2m()
        return habitacion

    class Meta:
        model = Habitacion
        fields = ['tipo', 'numero', 'piso']
        labels = {
            'tipo': 'Tipo de habitacion',
            'numero': 'Numero',
            'piso': 'Piso',
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
