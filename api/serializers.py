from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from empleados.models import Empleado
from estancias.models import Estancia
from habitaciones.models import Habitacion, TipoHabitacion
from huespedes.models import Huesped
from reservas.models import Reserva
from reservas.services import crear_reserva, editar_reserva, validar_reserva


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
    codigo = serializers.CharField(read_only=True)
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
            'codigo',
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
            'codigo',
            'hotel',
            'habitacion_numero',
            'tipo_habitacion',
            'tipo_habitacion_nombre',
            'noches',
            'estado',
            'precio_total',
        ]

    def validate(self, attrs):
        habitacion = attrs.get('habitacion', self.instance.habitacion if self.instance else None)
        fecha_entrada = attrs.get('fecha_entrada', self.instance.fecha_entrada if self.instance else None)
        fecha_salida = attrs.get('fecha_salida', self.instance.fecha_salida if self.instance else None)
        num_adultos = attrs.get('num_adultos', self.instance.num_adultos if self.instance else 1)

        if habitacion or fecha_entrada or fecha_salida or num_adultos is not None:
            try:
                validar_reserva(
                    habitacion=habitacion,
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    num_adultos=num_adultos,
                    reserva_id=self.instance.pk if self.instance else None,
                )
            except DjangoValidationError as error:
                raise serializers.ValidationError(self._format_django_error(error)) from error

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        try:
            return crear_reserva(
                huesped=validated_data['huesped'],
                habitacion=validated_data['habitacion'],
                fecha_entrada=validated_data['fecha_entrada'],
                fecha_salida=validated_data['fecha_salida'],
                num_adultos=validated_data.get('num_adultos', 1),
                origen=validated_data.get('origen', Reserva._meta.get_field('origen').default),
                usuario=request.user if request else None,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(self._format_django_error(error)) from error

    def update(self, instance, validated_data):
        request = self.context.get('request')
        try:
            return editar_reserva(
                instance,
                huesped=validated_data.get('huesped', instance.huesped),
                habitacion=validated_data.get('habitacion', instance.habitacion),
                fecha_entrada=validated_data.get('fecha_entrada', instance.fecha_entrada),
                fecha_salida=validated_data.get('fecha_salida', instance.fecha_salida),
                num_adultos=validated_data.get('num_adultos', instance.num_adultos),
                origen=validated_data.get('origen', instance.origen),
                usuario=request.user if request else None,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(self._format_django_error(error)) from error

    @staticmethod
    def _format_django_error(error):
        if hasattr(error, 'message_dict'):
            return error.message_dict
        return {'detail': error.messages}


class HabitacionEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Habitacion._meta.get_field('estado').choices)


class EstanciaSerializer(serializers.ModelSerializer):
    reserva_codigo = serializers.CharField(source='reserva.codigo', read_only=True)
    huesped_nombre = serializers.CharField(source='reserva.huesped.nombre_completo', read_only=True)
    habitacion_numero = serializers.CharField(source='habitacion.numero', read_only=True)
    hotel_nombre = serializers.CharField(source='habitacion.hotel.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    folio_id = serializers.IntegerField(source='folio.id', read_only=True)
    folio_estado = serializers.CharField(source='folio.estado', read_only=True)
    folio_total = serializers.DecimalField(source='folio.total', max_digits=10, decimal_places=2, read_only=True)
    folio_pagado = serializers.DecimalField(source='folio.total_pagado', max_digits=10, decimal_places=2, read_only=True)
    folio_saldo = serializers.DecimalField(source='folio.saldo_pendiente', max_digits=10, decimal_places=2, read_only=True)

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
            'folio_id',
            'folio_estado',
            'folio_total',
            'folio_pagado',
            'folio_saldo',
        ]
