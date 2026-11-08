from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Func, Q
from django.utils import timezone


class TsTzRange(Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class HorarioAsesor(models.Model):
    """Turno semanal de un asesor (RF-36). Sirve para calcular c efectivo por franja."""

    class Dia(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="horarios"
    )
    dia_semana = models.PositiveSmallIntegerField(choices=Dia.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        ordering = ["asesor", "dia_semana", "hora_inicio"]
        constraints = [
            models.CheckConstraint(
                condition=Q(hora_fin__gt=F("hora_inicio")), name="horario_fin_despues_de_inicio"
            ),
            models.UniqueConstraint(
                fields=["asesor", "dia_semana", "hora_inicio"], name="horario_turno_unico"
            ),
        ]

    def __str__(self):
        return f"{self.asesor} {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"


class Visita(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADA = "PROGRAMADA", "Programada"
        REALIZADA = "REALIZADA", "Realizada"
        CANCELADA = "CANCELADA", "Cancelada"

    solicitud = models.ForeignKey(
        "seguimiento.SolicitudAtencion", on_delete=models.PROTECT, related_name="visitas"
    )
    inmueble = models.ForeignKey(
        "inmuebles.Inmueble", on_delete=models.PROTECT, related_name="visitas"
    )
    asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="visitas"
    )
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PROGRAMADA)
    # Reprogramar = cancelar la visita y crear otra que apunta a la anterior (conserva historial).
    reemplaza_a = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reprogramaciones"
    )
    notas = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(fin__gt=F("inicio")), name="visita_fin_despues_de_inicio"
            ),
            # RN-01 / RN-02 / RNF-03: la BD rechaza cruces. Rangos [inicio, fin): una visita que
            # termina cuando empieza otra NO se cruza. Las canceladas liberan el horario (RN-04).
            ExclusionConstraint(
                name="visita_sin_cruce_asesor",
                expressions=[
                    (TsTzRange("inicio", "fin", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("asesor", RangeOperators.EQUAL),
                ],
                condition=~Q(estado="CANCELADA"),
            ),
            ExclusionConstraint(
                name="visita_sin_cruce_inmueble",
                expressions=[
                    (TsTzRange("inicio", "fin", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("inmueble", RangeOperators.EQUAL),
                ],
                condition=~Q(estado="CANCELADA"),
            ),
        ]
        indexes = [
            models.Index(fields=["asesor", "inicio"], name="visita_asesor_inicio_idx"),
            models.Index(fields=["inmueble", "inicio"], name="visita_inmueble_inicio_idx"),
        ]

    def __str__(self):
        return f"Visita {self.pk}: {self.inmueble_id} {self.inicio:%Y-%m-%d %H:%M}"
