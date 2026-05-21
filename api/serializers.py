from rest_framework import serializers

from empleados.models import Empleado
from estancias.models import Estancia
from habitaciones.models import Habitacion


class EmpleadoAutocompleteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='nombre_completo', read_only=True)
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)

    class Meta:
        model = Empleado
        fields = ['id', 'text', 'codigo', 'nombres', 'apellidos', 'email', 'cargo', 'cargo_display']


class HabitacionSerializer(serializers.ModelSerializer):
    hotel_nombre = serializers.CharField(source='hotel.nombre', read_only=True)
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Habitacion
        fields = [
            'id',
            'hotel',
            'hotel_nombre',
            'tipo',
            'tipo_nombre',
            'numero',
            'piso',
            'estado',
            'estado_display',
        ]


class HabitacionEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Habitacion._meta.get_field('estado').choices)


class EstanciaSerializer(serializers.ModelSerializer):
    reserva_codigo = serializers.CharField(source='reserva.id', read_only=True)
    huesped_nombre = serializers.CharField(source='reserva.huesped.nombre_completo', read_only=True)
    habitacion_numero = serializers.CharField(source='habitacion.numero', read_only=True)
    hotel_nombre = serializers.CharField(source='habitacion.hotel.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Estancia
        fields = [
            'id',
            'reserva',
            'reserva_codigo',
            'huesped_nombre',
            'habitacion',
            'habitacion_numero',
            'hotel_nombre',
            'fecha_checkin',
            'fecha_checkout',
            'precio_final',
            'estado',
            'estado_display',
        ]
