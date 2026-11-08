from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Inmueble(models.Model):
    class Operacion(models.TextChoices):
        VENTA = "VENTA", "Venta"
        ALQUILER = "ALQUILER", "Alquiler"

    class TipoInmueble(models.TextChoices):
        CASA = "CASA", "Casa"
        APARTAMENTO = "APARTAMENTO", "Apartamento"

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        RESERVADO = "RESERVADO", "Reservado"
        VENDIDO = "VENDIDO", "Vendido"
        ARRENDADO = "ARRENDADO", "Arrendado"

    titulo = models.CharField(max_length=150)
    tipo_inmueble = models.CharField(
        max_length=15, choices=TipoInmueble.choices, default=TipoInmueble.CASA
    )
    operacion = models.CharField(max_length=10, choices=Operacion.choices)
    direccion = models.CharField(max_length=200)
    barrio = models.CharField(max_length=100, blank=True)
    precio = models.DecimalField(max_digits=14, decimal_places=2)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    habitaciones = models.PositiveSmallIntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.DISPONIBLE)
    activo = models.BooleanField(default=True)  # RF-10: se desactiva, no se borra
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(precio__gt=0), name="inmueble_precio_positivo"),
            models.CheckConstraint(
                condition=Q(area_m2__isnull=True) | Q(area_m2__gt=0),
                name="inmueble_area_positiva",
            ),
            # Coherencia estado/operación: no se arrienda una venta ni se vende un alquiler.
            models.CheckConstraint(
                condition=~Q(estado="VENDIDO", operacion="ALQUILER")
                & ~Q(estado="ARRENDADO", operacion="VENTA"),
                name="inmueble_estado_coherente_con_operacion",
            ),
        ]
        indexes = [
            models.Index(fields=["estado", "operacion"], name="inmueble_estado_oper_idx"),
            models.Index(fields=["precio"], name="inmueble_precio_idx"),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.get_operacion_display()}"


class FotoInmueble(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="inmuebles/%Y/%m/")
    orden = models.PositiveSmallIntegerField(default=0)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return f"Foto {self.orden} de {self.inmueble_id}"


class HistorialEstadoInmueble(models.Model):
    """Bitácora inmutable de cambios de estado (RF-12)."""

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name="historial_estados"
    )
    estado_anterior = models.CharField(max_length=15, choices=Inmueble.Estado.choices, blank=True)
    estado_nuevo = models.CharField(max_length=15, choices=Inmueble.Estado.choices)
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(estado_anterior=F("estado_nuevo")),
                name="historial_estado_cambia",
            ),
        ]
        indexes = [
            models.Index(fields=["inmueble", "fecha"], name="historial_inmueble_fecha_idx")
        ]

    def __str__(self):
        return f"{self.inmueble_id}: {self.estado_anterior or '-'} -> {self.estado_nuevo}"
