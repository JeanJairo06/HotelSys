from django import forms
from django.core.exceptions import ValidationError

from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.models import Reserva


class ReservaForm(forms.ModelForm):
    tipo_habitacion = forms.ModelChoiceField(
        queryset=TipoHabitacion.objects.none(),
        label='Tipo de habitacion',
        required=True,
    )

    class Meta:
        model = Reserva
        fields = [
            'hotel',
            'huesped',
            'tipo_habitacion',
            'habitacion',
            'fecha_entrada',
            'fecha_salida',
            'num_adultos',
            'origen',
            'estado',
            'precio_total',
        ]
        labels = {
            'hotel': 'Hotel',
            'huesped': 'Huesped',
            'habitacion': 'Habitacion',
            'fecha_entrada': 'Fecha de entrada',
            'fecha_salida': 'Fecha de salida',
            'num_adultos': 'Adultos',
            'origen': 'Origen',
            'estado': 'Estado',
            'precio_total': 'Total preliminar',
        }
        widgets = {
            'fecha_entrada': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'fecha_salida': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hotel'].queryset = Hotel.objects.order_by('nombre')
        self.fields['huesped'].queryset = Huesped.objects.order_by('apellidos', 'nombres')
        self.fields['tipo_habitacion'].queryset = TipoHabitacion.objects.order_by('nombre')
        habitaciones = Habitacion.objects.select_related('hotel', 'tipo').order_by(
            'hotel__nombre',
            'piso',
            'numero',
        )

        hotel_id = self.data.get('hotel') if self.is_bound else None
        tipo_id = self.data.get('tipo_habitacion') if self.is_bound else None

        if hotel_id:
            habitaciones = habitaciones.filter(hotel_id=hotel_id)

        if tipo_id:
            habitaciones = habitaciones.filter(tipo_id=tipo_id)

        self.fields['habitacion'].queryset = habitaciones
        self.fields['fecha_entrada'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_salida'].input_formats = ['%Y-%m-%d']
        self.fields['precio_total'].required = False
        self.fields['precio_total'].widget.attrs.update({'readonly': 'readonly'})

        if self.instance and self.instance.pk and self.instance.habitacion_id:
            self.fields['tipo_habitacion'].initial = self.instance.habitacion.tipo_id

        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({'class': css_class})

    def clean(self):
        cleaned_data = super().clean()
        hotel = cleaned_data.get('hotel')
        tipo_habitacion = cleaned_data.get('tipo_habitacion')
        habitacion = cleaned_data.get('habitacion')
        fecha_entrada = cleaned_data.get('fecha_entrada')
        fecha_salida = cleaned_data.get('fecha_salida')

        if hotel and habitacion and habitacion.hotel_id != hotel.id:
            self.add_error('habitacion', 'La habitacion seleccionada no pertenece al hotel.')

        if tipo_habitacion and habitacion and habitacion.tipo_id != tipo_habitacion.id:
            self.add_error('habitacion', 'La habitacion no corresponde al tipo seleccionado.')

        if fecha_entrada and fecha_salida and fecha_salida > fecha_entrada and habitacion:
            noches = (fecha_salida - fecha_entrada).days
            cleaned_data['precio_total'] = habitacion.tipo.precio_base * noches
        elif fecha_entrada and fecha_salida and fecha_salida <= fecha_entrada:
            raise ValidationError('La fecha de salida debe ser mayor a la fecha de entrada.')

        return cleaned_data
