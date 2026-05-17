from rest_framework import serializers

from empleados.models import Empleado


class EmpleadoAutocompleteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='nombre_completo', read_only=True)
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)

    class Meta:
        model = Empleado
        fields = ['id', 'text', 'codigo', 'nombres', 'apellidos', 'email', 'cargo', 'cargo_display']
