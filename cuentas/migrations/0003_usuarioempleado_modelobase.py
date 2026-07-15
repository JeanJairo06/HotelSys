from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cuentas', '0002_usuarioempleado'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuarioempleado',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usuarioempleado',
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usuarioempleado',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usuarioempleado',
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
