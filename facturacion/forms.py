from django import forms
from .models import Factura
from habitaciones.models import Tarifa
class FacturaEmisionForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['ruc_dni', 'razon_social']
        labels = {
            'ruc_dni': 'RUC o DNI del Cliente',
            'razon_social': 'Razón Social / Nombre Completo',
        }
        widgets = {
            'ruc_dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 10165519901 o 74826622',
                'maxlength': '11'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Sodexo Perú S.A.C.'
            }),
        }

    def clean_ruc_dni(self):
        ruc_dni = self.cleaned_data.get('ruc_dni')
        if len(ruc_dni) not in [8, 11]:
            raise forms.ValidationError("El documento debe tener exactamente 8 dígitos (DNI) o 11 dígitos (RUC).")
        return ruc_dni
    
class TarifaForm(forms.ModelForm):
    class Meta:
        model = Tarifa
        fields = ['tipo_habitacion', 'nombre','precio_noche', 'fecha_inicio', 'fecha_fin']
        labels = {
            'nombre': 'Nombre de la Temporada / Tarifa',
        }
        widgets = {
            'tipo_habitacion': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Fin de semana / Temporada Alta'}),
            'precio_noche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise forms.ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        return cleaned_data