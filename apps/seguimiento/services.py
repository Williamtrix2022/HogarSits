"""Transiciones de una solicitud de atención (RF-23, RF-24, RN-11, RN-12, RN-20 a RN-22).

La hora la fija siempre el sistema (RN-11): ni el asesor ni el formulario la escriben, para que
los datos que alimentan λ (llegadas) y μ (servicio) sean fiables.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import Etapa, SeguimientoEtapa, SolicitudAtencion

Estado = SolicitudAtencion.Estado


# RN-30: transiciones válidas. Quedarse en la misma etapa (autotransición) es un seguimiento sin
# avance y cuenta como un paso de la cadena de Markov (ADR-002). RN-31: Cierre y Abandono son
# absorbentes, así que no tienen salidas.
TRANSICIONES = {
    Etapa.CONSULTA: (Etapa.CONSULTA, Etapa.VISITA, Etapa.ABANDONO),
    Etapa.VISITA: (Etapa.VISITA, Etapa.NEGOCIACION, Etapa.ABANDONO),
    Etapa.NEGOCIACION: (Etapa.NEGOCIACION, Etapa.CIERRE, Etapa.ABANDONO),
}
ETAPAS_FINALES = (Etapa.CIERRE, Etapa.ABANDONO)


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


# --- Etapas comerciales (HU-06, RF-40 a RF-42, RN-30 a RN-33) --------------------------------
def destinos_permitidos(solicitud: SolicitudAtencion) -> list[Etapa]:
    """Etapas a las que puede pasar desde la actual; vacío si la solicitud ya terminó."""
    if solicitud.estado == Estado.CANCELADO:
        return []
    return list(TRANSICIONES.get(Etapa(solicitud.etapa_actual), ()))


@transaction.atomic
def registrar_etapa(solicitud: SolicitudAtencion, destino: int, usuario, nota: str = ""):
    """Guarda una transición (origen, destino, fecha, quién) y actualiza la etapa actual.

    Si `destino` es la etapa actual se registra una autotransición: un seguimiento sin avance
    (ADR-002). El historial no se edita ni se borra (RN-33).
    """
    s = _bloquear(solicitud)
    if s.estado == Estado.CANCELADO:
        raise TransicionInvalida("Una solicitud cancelada no admite seguimiento de etapas.")
    origen = Etapa(s.etapa_actual)
    if origen in ETAPAS_FINALES:  # RN-31
        raise TransicionInvalida(
            f"La solicitud ya está en {origen.label}: es una etapa final y no admite cambios."
        )
    try:
        destino = Etapa(int(destino))
    except (ValueError, TypeError):
        raise TransicionInvalida("Elija una etapa válida.") from None
    if destino not in TRANSICIONES[origen]:  # RN-30
        raise TransicionInvalida(
            f"No se puede pasar de {origen.label} a {destino.label}. "
            "Solo se avanza a la etapa siguiente o se abandona."
        )
    transicion = SeguimientoEtapa.objects.create(
        solicitud=s,
        estado_origen=origen,
        estado_destino=destino,
        registrado_por=usuario,
        nota=nota.strip(),
    )
    s.etapa_actual = destino
    s.save(update_fields=["etapa_actual"])
    return transicion


def es_autotransicion(transicion: SeguimientoEtapa) -> bool:
    return transicion.estado_origen == transicion.estado_destino


# --- Pendientes de seguimiento (HU-12, RF-25, RF-26, RN-13) ----------------------------------
@dataclass(frozen=True)
class Pendiente:
    solicitud: SolicitudAtencion
    ultimo_movimiento: datetime
    dias: int  # días completos sin movimiento
    sin_seguimiento: bool  # RN-13: supera el umbral N


def dias_sin_seguimiento() -> int:
    return settings.DIAS_SIN_SEGUIMIENTO


def pendientes_de_seguimiento(asesor=None, ahora=None, umbral_dias=None) -> list[Pendiente]:
    """Solicitudes con una venta o alquiler en curso, la más olvidada primero.

    Pendiente = no cancelada y en Consulta, Visita o Negociación. El último movimiento es el
    seguimiento más reciente o, si nunca hubo uno, la llegada (RN-13). Con `asesor` solo se
    devuelven las suyas; sin él, todas (vista del administrador).
    """
    ahora = ahora or timezone.now()
    limite = timedelta(days=umbral_dias if umbral_dias is not None else dias_sin_seguimiento())
    consulta = (
        SolicitudAtencion.objects.exclude(estado=Estado.CANCELADO)
        .exclude(etapa_actual__in=ETAPAS_FINALES)
        .select_related("cliente", "inmueble", "asesor")
        .annotate(ultimo_seguimiento=Max("seguimientos__fecha_transicion"))
    )
    if asesor is not None:
        consulta = consulta.filter(asesor=asesor)
    pendientes = []
    for s in consulta:
        ultimo = max(s.ultimo_seguimiento or s.timestamp_llegada, s.timestamp_llegada)
        transcurrido = ahora - ultimo
        pendientes.append(
            Pendiente(
                solicitud=s,
                ultimo_movimiento=ultimo,
                dias=max(0, transcurrido.days),
                sin_seguimiento=transcurrido > limite,
            )
        )
    pendientes.sort(key=lambda p: (p.ultimo_movimiento, p.solicitud.pk))  # antigüedad
    return pendientes
