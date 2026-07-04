from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from config.choices import EstadoEstancia, TipoDocumento
from huespedes.exceptions import HuespedDuplicado


def normalizar_datos_huesped(datos):
    datos = datos.copy()

    if datos.get('num_doc'):
        datos['num_doc'] = datos['num_doc'].strip().upper().replace(' ', '')

    for campo in ('nombres', 'apellidos', 'razon_social', 'nacionalidad'):
        if datos.get(campo):
            datos[campo] = datos[campo].strip()

    if datos.get('email'):
        datos['email'] = datos['email'].strip().lower()

    return datos


def validar_documento_huesped(*, tipo_doc, num_doc, nombres='', apellidos='', razon_social=''):
    errors = {}

    if tipo_doc == TipoDocumento.RUC:
        if not num_doc or not num_doc.isdigit():
            errors['num_doc'] = 'El RUC debe contener solo numeros.'
        elif len(num_doc) != 11:
            errors['num_doc'] = 'El RUC debe tener exactamente 11 digitos.'

        if not razon_social:
            errors['razon_social'] = 'La razon social es obligatoria para RUC.'

    if tipo_doc == TipoDocumento.DNI:
        if not num_doc or not num_doc.isdigit():
            errors['num_doc'] = 'El DNI debe contener solo numeros.'
        elif len(num_doc) != 8:
            errors['num_doc'] = 'El DNI debe tener exactamente 8 digitos.'

        if not nombres:
            errors['nombres'] = 'Los nombres son obligatorios para DNI.'

        if not apellidos:
            errors['apellidos'] = 'Los apellidos son obligatorios para DNI.'

    if errors:
        raise ValidationError(errors)


def validar_datos_huesped(datos, *, huesped_id=None):
    from huespedes.models import Huesped

    datos = normalizar_datos_huesped(datos)
    errors = {}

    tipo_doc = datos.get('tipo_doc')
    num_doc = datos.get('num_doc')
    nombres = datos.get('nombres') or ''
    apellidos = datos.get('apellidos') or ''
    razon_social = datos.get('razon_social') or ''
    fecha_nacimiento = datos.get('fecha_nacimiento')
    telefono = datos.get('telefono')
    email = datos.get('email')
    documento_duplicado = False

    try:
        validar_documento_huesped(
            tipo_doc=tipo_doc,
            num_doc=num_doc,
            nombres=nombres,
            apellidos=apellidos,
            razon_social=razon_social,
        )
    except ValidationError as error:
        errors.update(error.message_dict)

    if tipo_doc == TipoDocumento.DNI and not fecha_nacimiento:
        errors['fecha_nacimiento'] = 'La fecha de nacimiento es obligatoria para DNI.'

    if telefono:
        telefono_limpio = telefono.replace('+', '').replace('-', '').replace(' ', '')
        if not telefono_limpio.isdigit():
            errors['telefono'] = 'El telefono solo debe contener numeros, espacios, + o -.'
        elif len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            errors['telefono'] = 'El telefono debe tener entre 7 y 15 digitos.'

    if fecha_nacimiento and fecha_nacimiento >= date.today():
        errors['fecha_nacimiento'] = 'La fecha de nacimiento debe ser anterior a hoy.'

    if fecha_nacimiento:
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        if edad < 18:
            errors['fecha_nacimiento'] = 'El huesped debe ser mayor de 18 anos.'

    duplicado_doc = Huesped.todos.filter(num_doc=num_doc)
    if huesped_id:
        duplicado_doc = duplicado_doc.exclude(pk=huesped_id)
    if tipo_doc and num_doc and duplicado_doc.exists():
        errors['num_doc'] = 'Ya existe un huesped registrado con este documento.'
        documento_duplicado = True

    if email:
        existe_email = Huesped.todos.filter(email=email)
        if huesped_id:
            existe_email = existe_email.exclude(pk=huesped_id)
        if existe_email.exists():
            errors['email'] = 'Este correo ya esta registrado.'

    if telefono:
        existe_telefono = Huesped.todos.filter(telefono=telefono)
        if huesped_id:
            existe_telefono = existe_telefono.exclude(pk=huesped_id)
        if existe_telefono.exists():
            errors['telefono'] = 'Este telefono ya esta registrado.'

    if errors:
        if documento_duplicado:
            raise HuespedDuplicado(errors)
        raise ValidationError(errors)

    return datos


@transaction.atomic
def crear_huesped(*, usuario=None, **datos):
    from huespedes.models import Huesped

    datos = validar_datos_huesped(datos)
    huesped = Huesped(**datos)
    if getattr(usuario, 'is_authenticated', False):
        huesped.creado_por = usuario

    try:
        huesped.save()
    except IntegrityError as error:
        raise HuespedDuplicado({'num_doc': 'Ya existe un huesped registrado con este documento.'}) from error

    return huesped


@transaction.atomic
def editar_huesped(huesped, *, usuario=None, **datos):
    from huespedes.models import Huesped

    huesped = Huesped.objects.select_for_update().get(pk=huesped.pk)
    datos = validar_datos_huesped(datos, huesped_id=huesped.pk)

    for campo, valor in datos.items():
        setattr(huesped, campo, valor)
    huesped.save()
    return huesped


@transaction.atomic
def eliminar_huesped(huesped, *, usuario=None):
    from huespedes.models import Huesped

    huesped = Huesped.objects.select_for_update().get(pk=huesped.pk)
    return huesped.eliminar(usuario=usuario)


def historial_huesped(huesped):
    from reservas.models import Reserva

    return Reserva.todos.select_related('hotel', 'habitacion', 'habitacion__tipo').filter(
        huesped=huesped,
    ).order_by('-fecha_entrada', '-id')


def estancia_actual_huesped(huesped):
    from estancias.models import Estancia

    return Estancia.objects.select_related(
        'reserva',
        'habitacion',
        'habitacion__tipo',
    ).filter(
        reserva__huesped=huesped,
        estado=EstadoEstancia.ACTIVA,
    ).order_by('-fecha_checkin').first()
