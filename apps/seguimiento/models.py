from django.conf import settings
from django.db import models


# Modelo clave para Poisson y Teoría de Colas (M/M/c)
class SolicitudAtencion(models.Model):
    ESTADOS = [
        ("EN_ESPERA", "En espera"),
        ("EN_ATENCION", "En atención"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    inmueble = models.ForeignKey(
        "inmuebles.Inmueble", on_delete=models.CASCADE, null=True, blank=True
    )
    asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timestamps para calcular λ (llegadas) y μ (tiempo de servicio)
    timestamp_llegada = models.DateTimeField(auto_now_add=True)
    timestamp_inicio_atencion = models.DateTimeField(null=True, blank=True)
    timestamp_fin_atencion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="EN_ESPERA")

    def __str__(self):
        return f"Solicitud #{self.pk} - {self.cliente.nombre}"


# Modelo clave para Cadenas de Markov (transiciones de estado)
class SeguimientoEtapa(models.Model):
    ETAPAS = [
        (1, "Consulta"),
        (2, "Visita"),
        (3, "Negociación"),
        (4, "Cierre"),  # Estado absorbente 1
        (5, "Abandono"),  # Estado absorbente 2
    ]

    solicitud = models.ForeignKey(
        SolicitudAtencion, on_delete=models.CASCADE, related_name="seguimientos"
    )
    estado_origen = models.IntegerField(choices=ETAPAS)
    estado_destino = models.IntegerField(choices=ETAPAS)
    fecha_transicion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Solicitud #{self.solicitud_id}: "
            f"{self.get_estado_origen_display()} -> {self.get_estado_destino_display()}"
        )
