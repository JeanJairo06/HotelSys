from django import forms
from .models import Factura

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