"""Reglas de negocio de inmuebles que no caben en una restricción de la BD."""

from django.db import transaction

from .models import HistorialEstadoInmueble, Inmueble


@transaction.atomic
def guardar_inmueble(form, usuario) -> Inmueble:
    """Guarda el formulario y deja constancia de cada cambio de estado (RF-12).

    Al crear, se registra el estado inicial (sin estado anterior). Al editar, solo si el
    estado cambió. Todo ocurre en una transacción: nunca queda un cambio sin su bitácora.
    """
    estado_anterior = "" if form.instance.pk is None else form.initial.get("estado", "")
    inmueble = form.save()
    if inmueble.estado != estado_anterior:
        HistorialEstadoInmueble.objects.create(
            inmueble=inmueble,
            estado_anterior=estado_anterior,
            estado_nuevo=inmueble.estado,
            cambiado_por=usuario,
        )
    return inmueble


def cambiar_activo(inmueble: Inmueble, activo: bool) -> Inmueble:
    """Desactiva o reactiva un inmueble (no se borran: tienen historial y solicitudes)."""
    inmueble.activo = activo
    inmueble.save(update_fields=["activo", "actualizado_en"])
    return inmueble
