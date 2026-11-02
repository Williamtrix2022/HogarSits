from django.db import models


class Inmueble(models.Model):
    TIPO_OPERACION = [("VENTA", "Venta"), ("ALQUILER", "Alquiler")]
    ESTADO = [
        ("DISPONIBLE", "Disponible"),
        ("RESERVADO", "Reservado"),
        ("VENDIDO", "Vendido"),
        ("ARRENDADO", "Arrendado"),
    ]

    titulo = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_OPERACION)
    estado = models.CharField(max_length=15, choices=ESTADO, default="DISPONIBLE")

    def __str__(self):
        return f"{self.titulo} - {self.tipo}"
