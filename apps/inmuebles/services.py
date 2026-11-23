"""Reglas de negocio de inmuebles que no caben en una restricción de la BD."""

from django.db import transaction

from .models import HistorialEstadoInmueble, Inmueble

# RN-03: un inmueble cerrado ya no se ofrece en solicitudes ni visitas.
ESTADOS_CERRADOS = (Inmueble.Estado.VENDIDO, Inmueble.Estado.ARRENDADO)

MENSAJE_NO_OFRECIBLE = (
    "Ese inmueble no se puede ofrecer: está vendido, arrendado o inactivo. Elija otro."
)


def inmuebles_ofrecibles():
    """Inmuebles que pueden usarse en una solicitud o visita (activos y no cerrados)."""
    return Inmueble.objects.filter(activo=True).exclude(estado__in=ESTADOS_CERRADOS)


def se_puede_ofrecer(inmueble: Inmueble) -> bool:
    return inmueble.activo and inmueble.estado not in ESTADOS_CERRADOS


def solicitudes_abiertas(inmueble: Inmueble) -> int:
    """Solicitudes En espera o En atención que apuntan a este inmueble."""
    return inmueble.solicitudes.filter(estado__in=["EN_ESPERA", "EN_ATENCION"]).count()


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


def estado_de_cierre(inmueble: Inmueble) -> str:
    """RN-05: una venta cierra como Vendido; un alquiler, como Arrendado."""
    if inmueble.operacion == Inmueble.Operacion.VENTA:
        return Inmueble.Estado.VENDIDO
    return Inmueble.Estado.ARRENDADO


@transaction.atomic
def cambiar_estado(inmueble: Inmueble, nuevo: str, usuario) -> Inmueble:
    """Cambia el estado y deja constancia en la bitácora (RF-12), sin pasar por un formulario."""
    anterior = inmueble.estado
    if anterior == nuevo:
        return inmueble
    inmueble.estado = nuevo
    inmueble.save(update_fields=["estado", "actualizado_en"])
    HistorialEstadoInmueble.objects.create(
        inmueble=inmueble, estado_anterior=anterior, estado_nuevo=nuevo, cambiado_por=usuario
    )
    return inmueble


def cambiar_activo(inmueble: Inmueble, activo: bool) -> Inmueble:
    """Desactiva o reactiva un inmueble (no se borran: tienen historial y solicitudes)."""
    inmueble.activo = activo
    inmueble.save(update_fields=["activo", "actualizado_en"])
    return inmueble
