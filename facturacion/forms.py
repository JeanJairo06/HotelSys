from django import forms
from .models import Factura
from habitaciones.models import Tarifa
from estancias.models import CargoEstancia
from config.choices import TipoCargo

class FacturaEmisionForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = []
        
    
class TarifaForm(forms.ModelForm):
    class Meta:
        model = Tarifa
        fields = ['tipo_habitacion', 'nombre','precio_noche', 'fecha_inicio', 'fecha_fin']
        labels = {
            'nombre': 'Nombre de la Temporada / Tarifa',
            'precio_noche': 'Precio (S/)',
        }
        widgets = {
            'tipo_habitacion': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Fin de semana / Temporada Alta'}),
            'precio_noche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_inicio': forms.DateInput(format='%Y-%m-%d',attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(format='%Y-%m-%d',attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise forms.ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        return cleaned_data
    
class CargoEstanciaForm(forms.ModelForm):
    tipo = forms.ChoiceField(
        choices=TipoCargo.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tipo de Gasto / Cargo"
    )
    class Meta:
        model = CargoEstancia
        fields = ['tipo','concepto','monto']
        labels ={
            'concepto': 'Descripción del Consumo',
            'monto': 'Monto Comercial (S/)',
        }
        widgets = {
            'concepto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Desayuno Buffet / Lavandería '}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
    def __init__(self, *args, **kwargs):
        self.folio = kwargs.pop('folio', None)
        super().__init__(*args, **kwargs)
        
        nuevas_opciones = [choice for choice in TipoCargo.choices if choice[0] != 'HABITACION']
        self.fields['tipo'].choices = nuevas_opciones
        
    def clean(self):
        cleaned_data = super().clean()
        if self.folio and self.folio.estado == 'PAGADO':
            raise forms.ValidationError("Acción inválida: No se pueden agregar consumos a una cuenta ya liquidada.")
        return cleaned_data