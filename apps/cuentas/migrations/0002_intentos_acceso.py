from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cuentas", "0001_roles"),
    ]

    operations = [
        migrations.CreateModel(
            name="IntentoAcceso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usuario", models.CharField(max_length=150)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("fallos", models.PositiveSmallIntegerField(default=0)),
                ("bloqueado_hasta", models.DateTimeField(blank=True, null=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("usuario", "ip"), name="intento_acceso_usuario_ip_uniq")
                ],
            },
        ),
    ]
