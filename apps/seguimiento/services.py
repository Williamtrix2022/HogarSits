"""Transiciones de una solicitud de atención (RF-23, RF-24, RN-11, RN-12, RN-20 a RN-22).

La hora la fija siempre el sistema (RN-11): ni el asesor ni el formulario la escriben, para que
los datos que alimentan λ (llegadas) y μ (servicio) sean fiables.
"""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import SolicitudAtencion

Estado = SolicitudAtencion.Estado


class TransicionInvalida(Exception):
    """La acción no aplica al estado actual de la solicitud; el mensaje dice qué pasó."""


def tiempo_espera(solicitud: SolicitudAtencion) -> timedelta | None:
    """RN-21: inicio − llegada. Mientras sigue en espera, es lo que lleva esperando."""
    if solicitud.timestamp_inicio_atencion is not None:
        return solicitud.timestamp_inicio_atencion - solicitud.timestamp_llegada
    if solicitud.estado == Estado.EN_ESPERA:
        return timezone.now() - solicitud.timestamp_llegada
    return None  # cancelada sin ser atendida


def tiempo_servicio(solicitud: SolicitudAtencion) -> timedelta | None:
    """RN-21: fin − inicio. Solo existe si la solicitud ya terminó."""
    if solicitud.timestamp_inicio_atencion and solicitud.timestamp_fin_atencion:
        return solicitud.timestamp_fin_atencion - solicitud.timestamp_inicio_atencion
    return None


def aporta_a_mu(solicitud: SolicitudAtencion) -> bool:
    """RN-22: solo las Finalizadas con ambos tiempos entran en la estimación de μ."""
    return solicitud.estado == Estado.FINALIZADO and tiempo_servicio(solicitud) is not None


def _bloquear(solicitud: SolicitudAtencion) -> SolicitudAtencion:
    """Relee la fila con bloqueo: dos asesores no pueden tomar la misma solicitud a la vez."""
    return SolicitudAtencion.objects.select_for_update().get(pk=solicitud.pk)


@transaction.atomic
def tomar(solicitud: SolicitudAtencion, asesor) -> SolicitudAtencion:
    """En espera → En atención. El asesor que la toma queda como responsable (RN-12)."""
    s = _bloquear(solicitud)
    if s.estado != Estado.EN_ESPERA:
        raise TransicionInvalida(
            f"La solicitud ya no está en espera (estado: {s.get_estado_display()})."
        )
    s.estado = Estado.EN_ATENCION
    s.asesor = asesor
    s.timestamp_inicio_atencion = max(timezone.now(), s.timestamp_llegada)
    s.save(update_fields=["estado", "asesor", "timestamp_inicio_atencion"])
    return s


@transaction.atomic
def finalizar(solicitud: SolicitudAtencion, usuario, *, es_admin: bool = False):
    """En atención → Finalizado. Solo la termina su asesor responsable (o un administrador)."""
    s = _bloquear(solicitud)
    if s.estado != Estado.EN_ATENCION:
        raise TransicionInvalida("Solo se puede finalizar una solicitud que está en atención.")
    if s.asesor_id != usuario.pk and not es_admin:
        raise TransicionInvalida("Solo el asesor que la atiende puede finalizarla.")
    s.estado = Estado.FINALIZADO
    s.timestamp_fin_atencion = max(timezone.now(), s.timestamp_inicio_atencion)
    s.save(update_fields=["estado", "timestamp_fin_atencion"])
    return s


@transaction.atomic
def cancelar(solicitud: SolicitudAtencion) -> SolicitudAtencion:
    """En espera → Cancelado (el cliente se fue antes de ser atendido; no cuenta para μ)."""
    s = _bloquear(solicitud)
    if s.estado != Estado.EN_ESPERA:
        raise TransicionInvalida(
            "Solo se puede cancelar una solicitud que sigue en espera "
            f"(estado: {s.get_estado_display()})."
        )
    s.estado = Estado.CANCELADO
    s.save(update_fields=["estado"])
    return s
