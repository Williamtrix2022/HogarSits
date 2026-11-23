"""Agenda de visitas sin cruces (RF-30 a RF-33, RN-01 a RN-04, RN-06).

La BD ya impide los cruces (`ExclusionConstraint`, RNF-03); aquí se detectan antes de guardar para
decirle al asesor *con quién* se cruza, y se atrapa la carrera de dos asesores guardando a la vez.
Los intervalos son [inicio, fin): una visita que termina cuando empieza otra no se cruza.
"""

from datetime import datetime, time, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.formats import date_format

from apps.inmuebles.services import MENSAJE_NO_OFRECIBLE, se_puede_ofrecer
from apps.seguimiento.models import SolicitudAtencion

from .models import Visita

SOLICITUD_ABIERTA = (SolicitudAtencion.Estado.EN_ESPERA, SolicitudAtencion.Estado.EN_ATENCION)


class AgendaError(Exception):
    """Regla de la agenda incumplida; el mensaje dice qué pasó y qué hacer."""


def _hora(dt) -> str:
    return date_format(timezone.localtime(dt), "j M, H:i")


def activas():
    """Visitas que ocupan horario: las canceladas lo liberan (RN-04)."""
    return Visita.objects.exclude(estado=Visita.Estado.CANCELADA)


def cruces(asesor, inmueble, inicio, fin, excluir_pk=None):
    """(visita del asesor que se cruza, visita del inmueble que se cruza); None si no hay."""
    # RN-01/02: se cruzan si inicio₁ < fin₂ y inicio₂ < fin₁
    base = activas().filter(inicio__lt=fin, fin__gt=inicio)
    if excluir_pk:
        base = base.exclude(pk=excluir_pk)
    return base.filter(asesor=asesor).first(), base.filter(inmueble=inmueble).first()


def verificar_disponibilidad(asesor, inmueble, inicio, fin, excluir_pk=None):
    cruce_asesor, cruce_inmueble = cruces(asesor, inmueble, inicio, fin, excluir_pk)
    if cruce_asesor:
        raise AgendaError(
            f"{asesor.get_full_name() or asesor.username} ya tiene una visita de "
            f"{_hora(cruce_asesor.inicio)} a {_hora(cruce_asesor.fin)}. "
            "Elija otra hora u otro asesor."
        )
    if cruce_inmueble:
        raise AgendaError(
            f"«{inmueble.titulo}» ya tiene una visita de {_hora(cruce_inmueble.inicio)} "
            f"a {_hora(cruce_inmueble.fin)}. Elija otra hora."
        )


def verificar_visita(solicitud, inmueble, asesor, inicio, fin, excluir_pk=None):
    """Todas las reglas previas a guardar, en un solo lugar."""
    if solicitud.estado not in SOLICITUD_ABIERTA:
        raise AgendaError("Solo se agendan visitas para solicitudes abiertas.")
    if not se_puede_ofrecer(inmueble):  # RN-03
        raise AgendaError(MENSAJE_NO_OFRECIBLE)
    if inicio <= timezone.now():  # RN-06
        raise AgendaError("La visita debe programarse en el futuro.")
    verificar_disponibilidad(asesor, inmueble, inicio, fin, excluir_pk)


def _crear(solicitud, inmueble, asesor, inicio, duracion_min, notas="", reemplaza_a=None):
    fin = inicio + timedelta(minutes=duracion_min)
    verificar_visita(solicitud, inmueble, asesor, inicio, fin)
    try:
        with transaction.atomic():
            return Visita.objects.create(
                solicitud=solicitud, inmueble=inmueble, asesor=asesor, inicio=inicio, fin=fin,
                notas=notas, reemplaza_a=reemplaza_a,
            )
    except IntegrityError as error:  # otro asesor guardó en este mismo instante
        raise AgendaError(
            "El horario se ocupó hace un momento. Revise la agenda y elija otro."
        ) from error


def programar(solicitud, inmueble, asesor, inicio, duracion_min, notas="") -> Visita:
    return _crear(solicitud, inmueble, asesor, inicio, duracion_min, notas)


@transaction.atomic
def cancelar(visita: Visita) -> Visita:
    v = Visita.objects.select_for_update().get(pk=visita.pk)
    if v.estado != Visita.Estado.PROGRAMADA:
        raise AgendaError("Solo se cancela una visita programada.")
    v.estado = Visita.Estado.CANCELADA  # libera el horario (RN-04)
    v.save(update_fields=["estado"])
    return v


@transaction.atomic
def realizar(visita: Visita) -> Visita:
    v = Visita.objects.select_for_update().get(pk=visita.pk)
    if v.estado != Visita.Estado.PROGRAMADA:
        raise AgendaError("Solo se marca como realizada una visita programada.")
    if v.inicio > timezone.now():  # RN-06
        raise AgendaError("Esa visita aún no ha empezado; no se puede marcar como realizada.")
    v.estado = Visita.Estado.REALIZADA
    v.save(update_fields=["estado"])
    return v


@transaction.atomic
def reprogramar(visita: Visita, inicio, duracion_min) -> Visita:
    """Cancela la visita y crea otra que apunta a la anterior (conserva el historial).

    Si el nuevo horario no está libre, la excepción deshace todo: la visita original no se pierde.
    """
    v = Visita.objects.select_for_update().get(pk=visita.pk)
    if v.estado != Visita.Estado.PROGRAMADA:
        raise AgendaError("Solo se reprograma una visita programada.")
    v.estado = Visita.Estado.CANCELADA
    v.save(update_fields=["estado"])
    return _crear(v.solicitud, v.inmueble, v.asesor, inicio, duracion_min, v.notas, reemplaza_a=v)


def visitas_proximas(asesor, ahora=None):
    """Visitas programadas del asesor para hoy y mañana, en orden (RF-35, HU-12)."""
    hoy = timezone.localtime(ahora or timezone.now()).date()
    zona = timezone.get_current_timezone()
    desde = datetime.combine(hoy, time.min, tzinfo=zona)
    hasta = desde + timedelta(days=2)
    visitas = (
        Visita.objects.filter(
            asesor=asesor, estado=Visita.Estado.PROGRAMADA, inicio__gte=desde, inicio__lt=hasta
        )
        .select_related("inmueble", "solicitud__cliente")
        .order_by("inicio")
    )
    for v in visitas:
        v.es_hoy = timezone.localtime(v.inicio).date() == hoy
    return list(visitas)
