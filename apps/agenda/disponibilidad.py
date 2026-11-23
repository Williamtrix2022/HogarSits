"""Asesores disponibles por franja: el `c` efectivo del análisis de colas (RF-36, HU-09).

c efectivo = asesores con turno que cubre toda la franja − los que están en una visita.
Las visitas no canceladas ocupan al asesor (las Realizadas también: así se calcula con datos
históricos); es el hallazgo de la ronda 1: una visita de 30 a 120 min lo saca de la oficina.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.cuentas.roles import ROL_ASESOR

from .models import HorarioAsesor, Visita

User = get_user_model()


@dataclass(frozen=True)
class Disponibilidad:
    inicio: datetime
    fin: datetime
    con_turno: list = field(default_factory=list)
    en_visita: list = field(default_factory=list)
    disponibles: list = field(default_factory=list)

    @property
    def c(self) -> int:
        """Asesores disponibles para atender en la franja (el `c` de M/M/c)."""
        return len(self.disponibles)


def asesores_programables():
    """Usuarios activos con horario asignable: asesores, o con turnos ya cargados."""
    return (
        User.objects.filter(is_active=True)
        .filter(Q(groups__name=ROL_ASESOR) | Q(horarios__isnull=False))
        .distinct()
        .order_by("first_name", "username")
    )


def disponibilidad(inicio: datetime, fin: datetime) -> Disponibilidad:
    """Quiénes pueden atender entre `inicio` y `fin` (la franja debe caer en un mismo día)."""
    local_ini, local_fin = timezone.localtime(inicio), timezone.localtime(fin)
    hora_ini = local_ini.time()
    # Una franja que termina a medianoche cuenta hasta el final del día.
    hora_fin = local_fin.time() if local_fin.date() == local_ini.date() else time.max
    turnos = HorarioAsesor.objects.filter(
        dia_semana=local_ini.weekday(),
        hora_inicio__lte=hora_ini,
        hora_fin__gte=hora_fin,
        asesor__is_active=True,
    ).select_related("asesor")
    con_turno = sorted({t.asesor for t in turnos}, key=lambda u: (u.first_name, u.username))
    ocupados = set(
        Visita.objects.exclude(estado=Visita.Estado.CANCELADA)
        .filter(asesor__in=con_turno, inicio__lt=fin, fin__gt=inicio)
        .values_list("asesor_id", flat=True)
    )
    return Disponibilidad(
        inicio=inicio,
        fin=fin,
        con_turno=con_turno,
        en_visita=[a for a in con_turno if a.pk in ocupados],
        disponibles=[a for a in con_turno if a.pk not in ocupados],
    )


def disponibilidad_del_dia(dia: date, franja_minutos: int = 60) -> list[Disponibilidad]:
    """Una fila por franja entre el primer turno y el último del día (vacío si nadie trabaja)."""
    turnos = HorarioAsesor.objects.filter(dia_semana=dia.weekday(), asesor__is_active=True)
    horas = list(turnos.values_list("hora_inicio", "hora_fin"))
    if not horas:
        return []
    zona = timezone.get_current_timezone()
    paso = timedelta(minutes=franja_minutos)
    actual = datetime.combine(dia, min(h[0] for h in horas), tzinfo=zona)
    limite = datetime.combine(dia, max(h[1] for h in horas), tzinfo=zona)
    franjas = []
    while actual + paso <= limite:
        franjas.append(disponibilidad(actual, actual + paso))
        actual += paso
    return franjas
