from datetime import date

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.dateparse import parse_date

from config.choices import CargoEmpleado, EstadoGeneral
from empleados.exceptions import (
    CargoEmpleadoInvalido,
    DatosEmpleadoInvalidos,
    EmpleadoDuplicado,
)
from empleados.models import Empleado


class EmpleadoService:
    @staticmethod
    def empleados_queryset(*, q=None, incluir_inactivos=True):
        queryset = Empleado.todos.all() if incluir_inactivos else Empleado.objects.all()

        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q)
                | Q(nombres__icontains=q)
                | Q(apellidos__icontains=q)
                | Q(cargo__icontains=q)
                | Q(email__icontains=q)
            )

        return queryset.order_by('apellidos', 'nombres')

    @staticmethod
    def detalle_queryset():
        return Empleado.todos.all()

    @staticmethod
    def generar_codigo():
        return Empleado.generar_codigo()

    @staticmethod
    @transaction.atomic
    def crear_empleado(*, data, usuario_actor=None):
        datos = EmpleadoService._preparar_datos(data)
        EmpleadoService._validar_datos(datos)

        empleado = Empleado(**datos)
        if EmpleadoService._usuario_persistido(usuario_actor):
            empleado.creado_por = usuario_actor

        try:
            empleado.save()
        except IntegrityError as exc:
            raise EmpleadoDuplicado() from exc

        return empleado

    @staticmethod
    @transaction.atomic
    def actualizar_empleado(*, empleado, data, usuario_actor=None):
        datos = EmpleadoService._preparar_datos(data, empleado=empleado)
        EmpleadoService._validar_datos(datos, empleado=empleado)

        for campo, valor in datos.items():
            setattr(empleado, campo, valor)

        try:
            empleado.save()
        except IntegrityError as exc:
            raise EmpleadoDuplicado() from exc

        return empleado

    @staticmethod
    @transaction.atomic
    def desactivar_empleado(*, empleado, usuario_actor=None):
        empleado.estado = EstadoGeneral.INACTIVO
        empleado.activo = False
        empleado.save(update_fields=['estado', 'activo', 'actualizado_en'])
        return empleado

    @staticmethod
    @transaction.atomic
    def activar_empleado(*, empleado, usuario_actor=None):
        empleado.estado = EstadoGeneral.ACTIVO
        empleado.activo = True
        empleado.save(update_fields=['estado', 'activo', 'actualizado_en'])
        return empleado

    @staticmethod
    def _preparar_datos(data, *, empleado=None):
        datos = {
            'codigo': data.get('codigo') or '',
            'nombres': data.get('nombres') or '',
            'apellidos': data.get('apellidos') or '',
            'cargo': data.get('cargo') or CargoEmpleado.RECEPCIONISTA,
            'email': data.get('email') or '',
            'telefono': data.get('telefono') or '',
            'estado': data.get('estado', EstadoGeneral.ACTIVO),
            'fecha_ingreso': EmpleadoService._normalizar_fecha(data.get('fecha_ingreso')),
        }

        if empleado and empleado.pk:
            datos['codigo'] = empleado.codigo

        datos['codigo'] = datos['codigo'].strip().upper() if datos['codigo'] else ''
        datos['nombres'] = datos['nombres'].strip()
        datos['apellidos'] = datos['apellidos'].strip()
        datos['email'] = datos['email'].strip().lower()
        datos['telefono'] = datos['telefono'].strip() if datos['telefono'] else None

        return datos

    @staticmethod
    def _validar_datos(datos, *, empleado=None):
        EmpleadoService._validar_cargo(datos['cargo'])
        EmpleadoService._validar_fecha_ingreso(datos['fecha_ingreso'])
        EmpleadoService._validar_telefono(datos['telefono'])
        EmpleadoService._validar_email_unico(datos['email'], empleado=empleado)
        EmpleadoService._validar_telefono_unico(datos['telefono'], empleado=empleado)

    @staticmethod
    def _normalizar_fecha(valor):
        if isinstance(valor, str):
            return parse_date(valor)
        return valor

    @staticmethod
    def _validar_cargo(cargo):
        cargos_validos = {choice.value for choice in CargoEmpleado}
        if cargo not in cargos_validos:
            raise CargoEmpleadoInvalido()

    @staticmethod
    def _validar_fecha_ingreso(fecha_ingreso):
        if fecha_ingreso and fecha_ingreso > date.today():
            raise DatosEmpleadoInvalidos(
                'La fecha de ingreso no puede ser futura.',
                detail={'fecha_ingreso': 'La fecha de ingreso no puede ser futura.'},
            )

    @staticmethod
    def _validar_telefono(telefono):
        if not telefono:
            return

        telefono_limpio = telefono.replace('+', '').replace('-', '').replace(' ', '')
        if not telefono_limpio.isdigit():
            raise DatosEmpleadoInvalidos(
                'El telefono solo debe contener numeros, espacios, + o -.',
                detail={'telefono': 'El telefono solo debe contener numeros, espacios, + o -.'},
            )

        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            raise DatosEmpleadoInvalidos(
                'El telefono debe tener entre 7 y 15 digitos.',
                detail={'telefono': 'El telefono debe tener entre 7 y 15 digitos.'},
            )

    @staticmethod
    def _validar_email_unico(email, *, empleado=None):
        queryset = Empleado.todos.filter(email=email)
        if empleado and empleado.pk:
            queryset = queryset.exclude(pk=empleado.pk)

        if queryset.exists():
            raise EmpleadoDuplicado('Este correo ya esta registrado.')

    @staticmethod
    def _validar_telefono_unico(telefono, *, empleado=None):
        if not telefono:
            return

        queryset = Empleado.todos.filter(telefono=telefono)
        if empleado and empleado.pk:
            queryset = queryset.exclude(pk=empleado.pk)

        if queryset.exists():
            raise EmpleadoDuplicado('Este telefono ya esta registrado.')

    @staticmethod
    def _usuario_persistido(user):
        return bool(user and getattr(user, 'is_authenticated', False) and user.pk)
