from rest_framework import serializers

from empleados.models import Empleado
from estancias.models import Estancia
from habitaciones.models import Habitacion, TipoHabitacion
from huespedes.models import Huesped
from reservas.models import Reserva


class EmpleadoAutocompleteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='nombre_completo', read_only=True)
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)

    class Meta:
        model = Empleado
        fields = ['id', 'text', 'codigo', 'nombres', 'apellidos', 'email', 'cargo', 'cargo_display']

class HuespedAutocompleteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='nombre_completo', read_only=True)
    tipo_doc_display = serializers.CharField(source='get_tipo_doc_display', read_only=True)

    class Meta:
        model = Huesped
        fields = ['id', 'text', 'tipo_doc', 'tipo_doc_display', 'num_doc', 'email', 'telefono']

# Serializers del modulo Habitaciones y Estancias.
class TipoHabitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoHabitacion
        fields = ['id', 'nombre', 'capacidad', 'precio_base', 'amenidades']

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


class HabitacionReservaAutocompleteSerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    precio = serializers.DecimalField(source='tipo.precio_base', max_digits=10, decimal_places=2, read_only=True)
    capacidad = serializers.IntegerField(source='tipo.capacidad', read_only=True)

    class Meta:
        model = Habitacion
        fields = [
            'id',
            'text',
            'tipo',
            'tipo_nombre',
            'numero',
            'piso',
            'precio',
            'capacidad',
        ]

    def get_text(self, obj):
        return f'Hab. {obj.numero} ({obj.tipo.nombre})'


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
