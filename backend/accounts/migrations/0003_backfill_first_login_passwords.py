from django.db import migrations


def mark_legacy_first_logins(apps, schema_editor):
    user_model = apps.get_model("accounts", "UserModel")
    user_model.objects.filter(last_login__isnull=True, is_superuser=False).update(
        must_change_password=True
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_usermodel_must_change_password"),
    ]

    operations = [
        migrations.RunPython(mark_legacy_first_logins, migrations.RunPython.noop),
    ]
