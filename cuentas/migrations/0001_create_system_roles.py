from django.db import migrations


def create_system_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')

    role_names = ['admin', 'recepcionista', 'housekeeping']
    groups = {}

    for role_name in role_names:
        group, _ = Group.objects.get_or_create(name=role_name)
        groups[role_name] = group

    for user in User.objects.filter(is_staff=True):
        user.groups.add(groups['admin'])


def remove_system_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['admin', 'recepcionista', 'housekeeping']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_system_roles, remove_system_roles),
    ]
