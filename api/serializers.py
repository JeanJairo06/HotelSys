from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from config.choices import EstadoReserva
from empleados.models import Empleado
from estancias.models import Estancia
from habitaciones.models import Habitacion, TipoHabitacion
from huespedes.models import Huesped
from reservas.models import Reserva
from reservas.services import calcular_precio_total_reserva


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
    tarifas = serializers.SerializerMethodField()

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
            'tarifas',
        ]

    def get_text(self, obj):
        return f'Hab. {obj.numero} ({obj.tipo.nombre})'

    def get_tarifas(self, obj):
        return [
            {
                'fechaInicio': tarifa.fecha_inicio.isoformat(),
                'fechaFin': tarifa.fecha_fin.isoformat(),
                'precio': str(tarifa.precio_noche),
            }
            for tarifa in obj.tipo.tarifas.all()
        ]


class ReservaSerializer(serializers.ModelSerializer):
    hotel = serializers.PrimaryKeyRelatedField(read_only=True)
    estado = serializers.CharField(read_only=True)
    precio_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    noches = serializers.IntegerField(read_only=True)
    habitacion_numero = serializers.CharField(source='habitacion.numero', read_only=True)
    tipo_habitacion = serializers.IntegerField(source='habitacion.tipo_id', read_only=True)
    tipo_habitacion_nombre = serializers.CharField(source='habitacion.tipo.nombre', read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id',
            'hotel',
            'huesped',
            'habitacion',
            'habitacion_numero',
            'tipo_habitacion',
            'tipo_habitacion_nombre',
            'fecha_entrada',
            'fecha_salida',
            'noches',
            'num_adultos',
            'estado',
            'origen',
            'precio_total',
        ]
        read_only_fields = [
            'id',
            'hotel',
            'habitacion_numero',
            'tipo_habitacion',
            'tipo_habitacion_nombre',
            'noches',
            'estado',
            'precio_total',
        ]

    def validate(self, attrs):
        habitacion = attrs.get('habitacion')
        fecha_entrada = attrs.get('fecha_entrada')
        fecha_salida = attrs.get('fecha_salida')
        num_adultos = attrs.get('num_adultos', 1)

        if fecha_entrada and fecha_entrada < timezone.localdate():
            raise serializers.ValidationError({
                'fecha_entrada': 'La fecha de entrada no puede ser anterior a hoy.',
            })

        if fecha_entrada and fecha_salida and fecha_salida <= fecha_entrada:
            raise serializers.ValidationError({
                'fecha_salida': 'La fecha de salida debe ser mayor a la fecha de entrada.',
            })

        if num_adultos is not None and num_adultos < 1:
            raise serializers.ValidationError({
                'num_adultos': 'Debe registrar al menos un adulto.',
            })

        if habitacion and num_adultos and num_adultos > habitacion.tipo.capacidad:
            raise serializers.ValidationError({
                'num_adultos': 'La cantidad de adultos supera la capacidad del tipo de habitacion.',
            })

        if habitacion and fecha_entrada and fecha_salida:
            self._validar_disponibilidad(habitacion, fecha_entrada, fecha_salida)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            habitacion = Habitacion.objects.select_for_update().select_related('hotel', 'tipo').get(
                pk=validated_data['habitacion'].pk,
            )
            fecha_entrada = validated_data['fecha_entrada']
            fecha_salida = validated_data['fecha_salida']

            self._validar_disponibilidad(habitacion, fecha_entrada, fecha_salida)
            precio_total = calcular_precio_total_reserva(
                habitacion.tipo,
                fecha_entrada,
                fecha_salida,
            )

            return Reserva.objects.create(
                hotel=habitacion.hotel,
                huesped=validated_data['huesped'],
                habitacion=habitacion,
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                num_adultos=validated_data.get('num_adultos', 1),
                origen=validated_data.get('origen', Reserva._meta.get_field('origen').default),
                estado=EstadoReserva.CONFIRMADA,
                precio_total=precio_total,
            )

    @staticmethod
    def _validar_disponibilidad(habitacion, fecha_entrada, fecha_salida):
        reserva_solapada = Reserva.objects.filter(
            habitacion=habitacion,
            fecha_entrada__lt=fecha_salida,
            fecha_salida__gt=fecha_entrada,
        ).exclude(
            estado__in=[EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA],
        ).exists()

        if reserva_solapada:
            raise serializers.ValidationError({
                'habitacion': 'La habitacion ya tiene una reserva activa en ese rango de fechas.',
            })


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
