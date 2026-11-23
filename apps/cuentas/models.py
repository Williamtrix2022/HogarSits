from django.db import models
from django.utils import timezone


class IntentoAcceso(models.Model):
    """Fallos consecutivos de inicio de sesión por usuario + IP (RNF-04, #60)."""

    usuario = models.CharField(max_length=150)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fallos = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "ip"], name="intento_acceso_usuario_ip_uniq"
            ),
        ]

    def __str__(self):
        return f"{self.usuario} @ {self.ip} ({self.fallos})"

    @property
    def bloqueado(self):
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > timezone.now()
