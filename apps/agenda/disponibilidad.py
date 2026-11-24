"""Asesores disponibles por franja: el `c` efectivo del análisis de colas (RF-36, HU-09).

c efectivo = asesores con turno que cubre toda la franja − los que están en una visita.
Las visitas no canceladas ocupan al asesor (las Realizadas también: así se calcula con datos
históricos); es el hallazgo de la ronda 1: una visita de 30 a 120 min lo saca de la oficina.
"""

from bisect import bisect_left
from collections import defaultdict
from collections.abc import Iterable
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


def c_efectivo_por_hora(franjas: Iterable[tuple[date, int]]) -> dict[tuple[date, int], int]:
    """El `c` efectivo de muchas franjas de una hora, leyendo turnos y visitas **una sola vez**.

    Misma regla que `disponibilidad()` (el turno cubre toda la hora y ninguna visita no cancelada
    se cruza con ella), pero pensada para el análisis, que necesita cientos de franjas. Las visitas
    de un asesor no se solapan (restricción de la BD), así que basta mirar la última que empieza
    antes del fin de la franja.
    """
    franjas = list(franjas)
    if not franjas:
        return {}
    zona = timezone.get_current_timezone()
    primero = datetime.combine(min(d for d, _ in franjas), time.min, tzinfo=zona)
    ultimo = datetime.combine(max(d for d, _ in franjas), time.min, tzinfo=zona) + timedelta(days=1)

    turnos_por_dia: dict[int, list[tuple[int, time, time]]] = defaultdict(list)
    turnos = HorarioAsesor.objects.filter(asesor__is_active=True).values_list(
        "asesor_id", "dia_semana", "hora_inicio", "hora_fin"
    )
    for asesor_id, dia, ini, fin in turnos:
        turnos_por_dia[dia].append((asesor_id, ini, fin))

    visitas: dict[int, list[tuple[datetime, datetime]]] = defaultdict(list)
    ocupan = (
        Visita.objects.exclude(estado=Visita.Estado.CANCELADA)
        .filter(inicio__lt=ultimo, fin__gt=primero)
        .order_by("inicio")
        .values_list("asesor_id", "inicio", "fin")
    )
    for asesor_id, ini, fin in ocupan:
        visitas[asesor_id].append((ini, fin))
    inicios = {a: [v[0] for v in lista] for a, lista in visitas.items()}

    resultado = {}
    for dia, hora in franjas:
        ini = datetime.combine(dia, time(hora), tzinfo=zona)
        fin = ini + timedelta(hours=1)
        hora_fin = time(hora + 1) if hora < 23 else time.max
        disponibles = set()
        for asesor_id, t_ini, t_fin in turnos_por_dia.get(dia.weekday(), ()):
            if t_ini > time(hora) or t_fin < hora_fin or asesor_id in disponibles:
                continue
            lista = visitas.get(asesor_id, ())
            i = bisect_left(inicios.get(asesor_id, []), fin) - 1  # última visita que empieza antes
            if i >= 0 and lista[i][1] > ini:
                continue  # esa visita se cruza con la hora: el asesor está fuera
            disponibles.add(asesor_id)
        resultado[(dia, hora)] = len(disponibles)
    return resultado
