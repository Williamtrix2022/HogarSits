from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("inmuebles", "0001_initial")]

    operations = [migrations.RenameField("inmueble", "tipo", "operacion")]
