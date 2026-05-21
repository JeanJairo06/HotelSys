from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from config.choices import EstadoReserva
from habitaciones.models import Habitacion, TipoHabitacion
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
        huespedes = Huesped.objects.none()
        huesped_id = self.data.get(self.add_prefix('huesped')) if self.is_bound else None
        if huesped_id:
            huespedes = Huesped.objects.filter(pk=huesped_id)
        elif self.instance and self.instance.pk and self.instance.huesped_id:
            huespedes = Huesped.objects.filter(pk=self.instance.huesped_id)
        self.fields['huesped'].queryset = huespedes.order_by('apellidos', 'nombres')
        self.fields['tipo_habitacion'].queryset = TipoHabitacion.objects.order_by('nombre')
        habitaciones = Habitacion.objects.none()
        habitacion_id = self.data.get(self.add_prefix('habitacion')) if self.is_bound else None

        tipo_id = self.data.get('tipo_habitacion') if self.is_bound else self.initial.get('tipo_habitacion')
        fecha_entrada = self.data.get('fecha_entrada') if self.is_bound else self.initial.get('fecha_entrada')
        fecha_salida = self.data.get('fecha_salida') if self.is_bound else self.initial.get('fecha_salida')

        if self.instance and self.instance.pk:
            habitacion_id = habitacion_id or self.instance.habitacion_id
            tipo_id = tipo_id or self.instance.habitacion.tipo_id
            fecha_entrada = fecha_entrada or self.instance.fecha_entrada
            fecha_salida = fecha_salida or self.instance.fecha_salida

        if habitacion_id:
            habitaciones = Habitacion.objects.select_related('hotel', 'tipo').filter(pk=habitacion_id)

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
        self.fields['huesped'].widget.attrs.update({'class': 'form-select js-huesped-select'})
        self.fields['habitacion'].widget.attrs.update({'class': 'form-select js-habitacion-select'})

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
        tipo_habitacion = cleaned_data.get('tipo_habitacion')
        habitacion = cleaned_data.get('habitacion')
        fecha_entrada = cleaned_data.get('fecha_entrada')
        fecha_salida = cleaned_data.get('fecha_salida')
        num_adultos = cleaned_data.get('num_adultos')

        if tipo_habitacion and habitacion and habitacion.tipo_id != tipo_habitacion.id:
            self.add_error('habitacion', 'La habitacion no corresponde al tipo seleccionado.')

        if num_adultos is not None and num_adultos < 1:
            self.add_error('num_adultos', 'Debe registrar al menos un adulto.')

        if habitacion and num_adultos and num_adultos > habitacion.tipo.capacidad:
            self.add_error('num_adultos', 'La cantidad de adultos supera la capacidad de la habitacion.')

        if fecha_entrada and fecha_salida and fecha_salida > fecha_entrada and habitacion:
            noches = (fecha_salida - fecha_entrada).days
            cleaned_data['precio_total'] = habitacion.tipo.precio_base * noches
        elif fecha_entrada and fecha_salida and fecha_salida <= fecha_entrada:
            raise ValidationError('La fecha de salida debe ser mayor a la fecha de entrada.')

        return cleaned_data

    def save(self, commit=True):
        reserva = super().save(commit=False)
        if reserva.habitacion_id:
            reserva.hotel = reserva.habitacion.hotel
        if commit:
            reserva.save()
            self.save_m2m()
        return reserva
