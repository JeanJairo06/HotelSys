from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('huespedes', '0002_huesped_razon_social_fecha_nacimiento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='huesped',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='huesped',
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='huesped',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='huesped',
            name='creado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='huespedes_huesped_creados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
