from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('huespedes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='huesped',
            name='tipo_doc',
            field=models.CharField(choices=[('DNI', 'DNI'), ('RUC', 'RUC')], default='DNI', max_length=30),
        ),
        migrations.AlterField(
            model_name='huesped',
            name='nombres',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='huesped',
            name='apellidos',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='huesped',
            name='razon_social',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='huesped',
            name='fecha_nacimiento',
            field=models.DateField(blank=True, null=True),
        ),
    ]
