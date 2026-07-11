from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def asignar_codigos_reserva(apps, schema_editor):
    Reserva = apps.get_model('reservas', 'Reserva')
    for reserva in Reserva.objects.all().order_by('id'):
        fecha = reserva.fecha_entrada or django.utils.timezone.localdate()
        reserva.codigo = f'RSV-{fecha:%Y%m%d}-{reserva.id:04d}'
        reserva.save(update_fields=['codigo'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='reserva',
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='reserva',
            name='codigo',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='reserva',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reserva',
            name='creado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reservas_reserva_creados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(asignar_codigos_reserva, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='reserva',
            name='codigo',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
