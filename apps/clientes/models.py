from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Cliente(models.Model):
    """Persona interesada en comprar o arrendar. No es usuario del sistema."""

    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    # default (y no auto_now_add) para poder cargar datos históricos y simulados.
    fecha_registro = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            # RN-10: un correo identifica a un cliente, sin distinguir mayúsculas.
            models.UniqueConstraint(Lower("correo"), name="cliente_correo_unico_ci"),
        ]
        indexes = [models.Index(fields=["telefono"], name="cliente_telefono_idx")]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.correo = self.correo.strip().lower()
        super().save(*args, **kwargs)
