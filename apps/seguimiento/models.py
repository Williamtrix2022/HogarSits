from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Etapa(models.IntegerChoices):
    """Estados de la cadena de Markov (README). 4 y 5 son absorbentes."""

    CONSULTA = 1, "Consulta"
    VISITA = 2, "Visita"
    NEGOCIACION = 3, "Negociación"
    CIERRE = 4, "Cierre"
    ABANDONO = 5, "Abandono"


# Modelo clave para Poisson y Teoría de Colas (M/M/c)
class SolicitudAtencion(models.Model):
    class Interes(models.TextChoices):
        COMPRA = "COMPRA", "Compra"
        ALQUILER = "ALQUILER", "Alquiler"

    class Estado(models.TextChoices):
        EN_ESPERA = "EN_ESPERA", "En espera"
        EN_ATENCION = "EN_ATENCION", "En atención"
        FINALIZADO = "FINALIZADO", "Finalizado"
        CANCELADO = "CANCELADO", "Cancelado"

    # PROTECT: borrar un cliente o inmueble no debe destruir el historial que alimenta los modelos.
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, related_name="solicitudes"
    )
    inmueble = models.ForeignKey(
        "inmuebles.Inmueble",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="solicitudes",
    )
    asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_atendidas",
    )
    tipo_interes = models.CharField(max_length=10, choices=Interes.choices)
    presupuesto = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    # λ (llegadas) y μ (servicio). `default` y no `auto_now_add`: el generador de datos
    # simulados y la carga histórica necesitan fijar la hora; la UI no la expone (RN-11).
    timestamp_llegada = models.DateTimeField(default=timezone.now, editable=False)
    timestamp_inicio_atencion = models.DateTimeField(null=True, blank=True)
    timestamp_fin_atencion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.EN_ESPERA)

    # Copia denormalizada de la última transición (para listados). La fuente de verdad es
    # SeguimientoEtapa; un servicio la actualiza en la misma transacción (Sprint 4, #32).
    etapa_actual = models.PositiveSmallIntegerField(choices=Etapa.choices, default=Etapa.CONSULTA)

    class Meta:
        constraints = [
            # RN-20: llegada <= inicio <= fin
            models.CheckConstraint(
                condition=Q(timestamp_inicio_atencion__isnull=True)
                | Q(timestamp_inicio_atencion__gte=F("timestamp_llegada")),
                name="solicitud_inicio_despues_de_llegada",
            ),
            models.CheckConstraint(
                condition=Q(timestamp_fin_atencion__isnull=True)
                | (
                    Q(timestamp_inicio_atencion__isnull=False)
                    & Q(timestamp_fin_atencion__gte=F("timestamp_inicio_atencion"))
                ),
                name="solicitud_fin_despues_de_inicio",
            ),
            # El estado debe ser coherente con los tiempos registrados.
            models.CheckConstraint(
                condition=~Q(estado="EN_ESPERA", timestamp_inicio_atencion__isnull=False)
                & ~Q(estado="EN_ATENCION", timestamp_inicio_atencion__isnull=True)
                & ~Q(estado="FINALIZADO", timestamp_fin_atencion__isnull=True),
                name="solicitud_estado_coherente_con_tiempos",
            ),
            models.CheckConstraint(
                condition=Q(presupuesto__isnull=True) | Q(presupuesto__gt=0),
                name="solicitud_presupuesto_positivo",
            ),
        ]
        indexes = [
            models.Index(fields=["timestamp_llegada"], name="solicitud_llegada_idx"),
            models.Index(fields=["asesor", "estado"], name="solicitud_asesor_estado_idx"),
            models.Index(fields=["etapa_actual"], name="solicitud_etapa_idx"),
        ]

    def __str__(self):
        return f"Solicitud #{self.pk} - {self.cliente.nombre}"


# Modelo clave para Cadenas de Markov. Registro inmutable de transiciones.
# ADR-002 (pendiente de la ronda 2) decidirá cómo se registran las autotransiciones
# (permanecer en la misma etapa); por eso aquí NO se exige origen != destino.
class SeguimientoEtapa(models.Model):
    solicitud = models.ForeignKey(
        SolicitudAtencion, on_delete=models.CASCADE, related_name="seguimientos"
    )
    estado_origen = models.PositiveSmallIntegerField(choices=Etapa.choices)
    estado_destino = models.PositiveSmallIntegerField(choices=Etapa.choices)
    fecha_transicion = models.DateTimeField(default=timezone.now, editable=False)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    nota = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(estado_origen__in=[1, 2, 3, 4, 5])
                & Q(estado_destino__in=[1, 2, 3, 4, 5]),
                name="seguimiento_etapas_validas",
            ),
            # RN-31: Cierre y Abandono son absorbentes; no se sale de ellos.
            models.CheckConstraint(
                condition=~Q(estado_origen__in=[4, 5]),
                name="seguimiento_origen_no_absorbente",
            ),
        ]
        indexes = [
            models.Index(fields=["solicitud", "fecha_transicion"], name="seguim_solic_fecha_idx"),
            models.Index(fields=["estado_origen", "estado_destino"], name="seguim_transicion_idx"),
        ]

    def __str__(self):
        return (
            f"Solicitud #{self.solicitud_id}: "
            f"{self.get_estado_origen_display()} -> {self.get_estado_destino_display()}"
        )
