"""Indicadores por asesor (HU-13, RF-62).

Por asesor y rango de fechas: solicitudes atendidas, visitas realizadas, cierres y tiempo medio
de atención. Cada solicitud tiene un único asesor responsable (RN-12), y a él se le atribuye.

Definiciones (para que la cifra no admita dos lecturas):
  * **Atendidas:** solicitudes que el asesor empezó a atender en el periodo (hora de inicio).
  * **Visitas realizadas:** visitas en estado Realizada cuyo inicio cae en el periodo.
  * **Cierres:** solicitudes del asesor que pasaron a la etapa Cierre en el periodo.
  * **Atención media:** promedio de (fin − inicio) de sus atenciones **finalizadas** (RN-22).
"""

from dataclasses import dataclass
from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q

from apps.agenda.disponibilidad import asesores_programables
from apps.agenda.models import Visita
from apps.analitica.datos import limites
from apps.seguimiento.models import Etapa, SeguimientoEtapa, SolicitudAtencion

User = get_user_model()


@dataclass(frozen=True)
class Indicador:
    asesor: object  # el usuario
    atendidas: int
    visitas_realizadas: int
    cierres: int
    atencion_media_min: float | None  # None si no hay atenciones finalizadas
    n_finalizadas: int  # atenciones que sustentan la media (con pocas, la media no es firme)

    @property
    def nombre(self) -> str:
        return self.asesor.get_full_name() or self.asesor.username


def _contar(consulta, clave: str, distintos: str = "pk") -> dict[int, int]:
    """Cuenta por asesor los valores **distintos** de `distintos` (por defecto, las filas)."""
    filas = consulta.values(clave).annotate(n=Count(distintos, distinct=True))
    return {fila[clave]: fila["n"] for fila in filas}


def indicadores_por_asesor(desde: date, hasta: date, asesor=None) -> list[Indicador]:
    """Un `Indicador` por asesor. Con `asesor`, solo el suyo (aunque no tenga actividad); sin él,
    todos los asesores programables más cualquier usuario con actividad en el periodo."""
    inicio, fin = limites(desde, hasta)
    atendidas_qs = SolicitudAtencion.objects.filter(
        asesor__isnull=False,
        timestamp_inicio_atencion__gte=inicio,
        timestamp_inicio_atencion__lt=fin,
    )
    visitas_qs = Visita.objects.filter(
        estado=Visita.Estado.REALIZADA, inicio__gte=inicio, inicio__lt=fin
    )
    cierres_qs = SeguimientoEtapa.objects.filter(
        estado_destino=Etapa.CIERRE,
        fecha_transicion__gte=inicio,
        fecha_transicion__lt=fin,
        solicitud__asesor__isnull=False,
    )
    if asesor is not None:
        atendidas_qs = atendidas_qs.filter(asesor=asesor)
        visitas_qs = visitas_qs.filter(asesor=asesor)
        cierres_qs = cierres_qs.filter(solicitud__asesor=asesor)

    atendidas = _contar(atendidas_qs, "asesor")
    visitas = _contar(visitas_qs, "asesor")
    # Un cierre cuenta una vez por solicitud, aunque haya un registro duplicado.
    cierres = _contar(cierres_qs, "solicitud__asesor", distintos="solicitud")

    duracion = ExpressionWrapper(
        F("timestamp_fin_atencion") - F("timestamp_inicio_atencion"), output_field=DurationField()
    )
    finalizadas = {
        f["asesor"]: f
        for f in atendidas_qs.filter(
            estado=SolicitudAtencion.Estado.FINALIZADO, timestamp_fin_atencion__isnull=False
        )
        .values("asesor")
        .annotate(media=Avg(duracion), n=Count("pk"))
    }

    if asesor is not None:
        usuarios = [asesor]
    else:
        con_actividad = set(atendidas) | set(visitas) | set(cierres)
        usuarios = list(
            User.objects.filter(Q(pk__in=con_actividad) | Q(pk__in=asesores_programables()))
            .distinct()
            .order_by("first_name", "username")
        )

    resultado = []
    for u in usuarios:
        f = finalizadas.get(u.pk)
        resultado.append(
            Indicador(
                asesor=u,
                atendidas=atendidas.get(u.pk, 0),
                visitas_realizadas=visitas.get(u.pk, 0),
                cierres=cierres.get(u.pk, 0),
                atencion_media_min=f["media"].total_seconds() / 60 if f else None,
                n_finalizadas=f["n"] if f else 0,
            )
        )
    return resultado


def totales(indicadores: list[Indicador]) -> dict:
    """Suma del equipo; la atención media global pondera por número de atenciones."""
    con_tiempo = [i for i in indicadores if i.atencion_media_min is not None]
    n = sum(i.n_finalizadas for i in con_tiempo)
    media = sum(i.atencion_media_min * i.n_finalizadas for i in con_tiempo) / n if n else None
    return {
        "atendidas": sum(i.atendidas for i in indicadores),
        "visitas_realizadas": sum(i.visitas_realizadas for i in indicadores),
        "cierres": sum(i.cierres for i in indicadores),
        "atencion_media_min": media,
    }
