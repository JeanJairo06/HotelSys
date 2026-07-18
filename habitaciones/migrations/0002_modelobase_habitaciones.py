from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def campos_modelobase(model_name):
    return [
        migrations.AddField(
            model_name=model_name,
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name=model_name,
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name=model_name,
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name=model_name,
            name='creado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(app_label)s_%(class)s_creados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('habitaciones', '0001_initial'),
    ]

    operations = [
        *campos_modelobase('tipohabitacion'),
        *campos_modelobase('habitacion'),
    ]
