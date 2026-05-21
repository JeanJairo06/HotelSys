from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from config.choices import EstadoReserva
from habitaciones.models import Habitacion, TipoHabitacion
from hoteles.models import Hotel
from huespedes.models import Huesped
from reservas.models import Reserva
from reservas.services import calcular_precio_total_reserva


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

        hotel_id = self.data.get('hotel') if self.is_bound else self.initial.get('hotel')
        tipo_id = self.data.get('tipo_habitacion') if self.is_bound else self.initial.get('tipo_habitacion')
        fecha_entrada = self.data.get('fecha_entrada') if self.is_bound else self.initial.get('fecha_entrada')
        fecha_salida = self.data.get('fecha_salida') if self.is_bound else self.initial.get('fecha_salida')

        if self.instance and self.instance.pk:
            hotel_id = hotel_id or self.instance.hotel_id
            tipo_id = tipo_id or self.instance.habitacion.tipo_id
            fecha_entrada = fecha_entrada or self.instance.fecha_entrada
            fecha_salida = fecha_salida or self.instance.fecha_salida

        if hotel_id:
            habitaciones = habitaciones.filter(hotel_id=hotel_id)

        if tipo_id:
            habitaciones = habitaciones.filter(tipo_id=tipo_id)

        fecha_entrada_filtro = self._parse_filter_date(fecha_entrada)
        fecha_salida_filtro = self._parse_filter_date(fecha_salida)

        if fecha_entrada_filtro and fecha_salida_filtro and fecha_salida_filtro > fecha_entrada_filtro:
            habitaciones_ocupadas = Reserva.objects.filter(
                fecha_entrada__lt=fecha_salida_filtro,
                fecha_salida__gt=fecha_entrada_filtro,
            ).exclude(
                pk=self.instance.pk if self.instance and self.instance.pk else None,
            ).exclude(
                estado__in=[EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA],
            ).values('habitacion_id')
            habitaciones = habitaciones.exclude(pk__in=habitaciones_ocupadas)

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

    @staticmethod
    def _parse_filter_date(value):
        if not value:
            return None
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return value
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

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
            cleaned_data['precio_total'] = calcular_precio_total_reserva(
                habitacion.tipo,
                fecha_entrada,
                fecha_salida,
            )
        elif fecha_entrada and fecha_salida and fecha_salida <= fecha_entrada:
            raise ValidationError('La fecha de salida debe ser mayor a la fecha de entrada.')

        return cleaned_data
