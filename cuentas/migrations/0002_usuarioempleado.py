from django.db import migrations, models
import django.db.models.deletion


def generar_codigo(Empleado, user):
    base = f'USR{user.pk:07d}'[:10]
    codigo = base
    contador = 1

    while Empleado.objects.filter(codigo=codigo).exists():
        sufijo = str(contador)
        codigo = f'{base[:10 - len(sufijo)]}{sufijo}'
        contador += 1

    return codigo


def generar_email(Empleado, user):
    if user.email and not Empleado.objects.filter(email=user.email).exists():
        return user.email

    base = f'{user.username}@hotelsys.local'.lower()
    if not Empleado.objects.filter(email=base).exists():
        return base

    contador = 1
    while True:
        email = f'{user.username}{contador}@hotelsys.local'.lower()
        if not Empleado.objects.filter(email=email).exists():
            return email
        contador += 1


def crear_perfiles_usuario_empleado(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Empleado = apps.get_model('empleados', 'Empleado')
    UsuarioEmpleado = apps.get_model('cuentas', 'UsuarioEmpleado')

    for user in User.objects.all().order_by('id'):
        if UsuarioEmpleado.objects.filter(usuario=user).exists():
            continue

        empleado = None
        if user.email:
            empleado = Empleado.objects.filter(email=user.email).first()
            if empleado and UsuarioEmpleado.objects.filter(empleado=empleado).exists():
                empleado = None

        if empleado is None:
            empleado = Empleado.objects.create(
                codigo=generar_codigo(Empleado, user),
                nombres=user.first_name or user.username,
                apellidos=user.last_name or '-',
                cargo='OTRO',
                email=generar_email(Empleado, user),
                estado=1,
                fecha_ingreso=user.date_joined.date(),
            )

        UsuarioEmpleado.objects.create(usuario=user, empleado=empleado)


def eliminar_perfiles_usuario_empleado(apps, schema_editor):
    UsuarioEmpleado = apps.get_model('cuentas', 'UsuarioEmpleado')
    UsuarioEmpleado.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('empleados', '0002_alter_empleado_cargo'),
        ('cuentas', '0001_create_system_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsuarioEmpleado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('empleado', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='cuenta_usuario', to='empleados.empleado')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_empleado', to='auth.user')),
            ],
            options={
                'verbose_name': 'Usuario empleado',
                'verbose_name_plural': 'Usuarios empleados',
                'db_table': 'usuarios_empleados',
            },
        ),
        migrations.RunPython(crear_perfiles_usuario_empleado, eliminar_perfiles_usuario_empleado),
    ]
