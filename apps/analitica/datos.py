"""Lectura de los datos que alimentan el análisis (capa de Django, delgada).

Aquí se aplican las **reglas de qué dato cuenta** y se entrega a los servicios puros listas
simples. No hay matemática: eso vive en `services/`.
"""

from datetime import date, datetime, time, timedelta

from django.db.models import Max, Min
from django.utils import timezone

from apps.agenda.models import HorarioAsesor
from apps.analitica.management.commands.seed_datos_simulados import DOMINIO
from apps.analitica.services.poisson import LUNES_A_SABADO
from apps.clientes.models import Cliente
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion

HORARIO_POR_DEFECTO = (8, 18, LUNES_A_SABADO)


def limites(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """[desde 00:00, hasta + 1 día 00:00) en hora local de Bogotá (RN-42)."""
    zona = timezone.get_current_timezone()
    inicio = datetime.combine(desde, time.min, tzinfo=zona)
    fin = datetime.combine(hasta, time.min, tzinfo=zona) + timedelta(days=1)
    return inicio, fin


def llegadas(desde: date, hasta: date) -> list[datetime]:
    """Instante de llegada de cada solicitud del periodo.

    Cuentan **todas**, también las canceladas: el cliente llegó aunque luego se fuera.
    """
    inicio, fin = limites(desde, hasta)
    return list(
        SolicitudAtencion.objects.filter(timestamp_llegada__gte=inicio, timestamp_llegada__lt=fin)
        .values_list("timestamp_llegada", flat=True)
    )


def duraciones_de_servicio_en_horas(desde: date, hasta: date) -> list[float]:
    """RN-22: solo las **finalizadas** con inicio y fin aportan a μ; las canceladas se excluyen."""
    inicio, fin = limites(desde, hasta)
    pares = SolicitudAtencion.objects.filter(
        estado=SolicitudAtencion.Estado.FINALIZADO,
        timestamp_inicio_atencion__isnull=False,
        timestamp_fin_atencion__isnull=False,
        timestamp_llegada__gte=inicio,
        timestamp_llegada__lt=fin,
    ).values_list("timestamp_inicio_atencion", "timestamp_fin_atencion")
    return [
        (f - i).total_seconds() / 3600
        for i, f in pares
        if f > i  # una duración de cero no sirve para estimar μ
    ]


def transiciones(desde: date, hasta: date) -> list[tuple[int, int]]:
    """Pares (origen, destino) de las transiciones de etapa del periodo.

    Incluye las autotransiciones (seguimientos sin avance), que el ADR-002 manda contar.
    """
    inicio, fin = limites(desde, hasta)
    return list(
        SeguimientoEtapa.objects.filter(fecha_transicion__gte=inicio, fecha_transicion__lt=fin)
        .values_list("estado_origen", "estado_destino")
    )


def periodo_con_datos() -> tuple[date, date] | None:
    """Primer y último día (hora local) con llegadas, o None si no hay ninguna."""
    r = SolicitudAtencion.objects.aggregate(
        primero=Min("timestamp_llegada"), ultimo=Max("timestamp_llegada")
    )
    if r["primero"] is None:
        return None
    return timezone.localtime(r["primero"]).date(), timezone.localtime(r["ultimo"]).date()


def hay_horarios() -> bool:
    """¿Hay al menos un turno de un asesor activo? Sin turnos no se sabe cuántos asesores hay."""
    return HorarioAsesor.objects.filter(asesor__is_active=True).exists()


def horario_de_atencion() -> tuple[int, int, tuple[int, ...]]:
    """(apertura, cierre, días laborales) deducidos de los turnos cargados; si no hay, 8–18 L–S."""
    turnos = HorarioAsesor.objects.filter(asesor__is_active=True)
    if not turnos.exists():
        return HORARIO_POR_DEFECTO
    r = turnos.aggregate(ini=Min("hora_inicio"), fin=Max("hora_fin"))
    apertura = r["ini"].hour
    cierre = r["fin"].hour + (1 if r["fin"].minute or r["fin"].second else 0)
    dias = tuple(sorted(set(turnos.values_list("dia_semana", flat=True))))
    return apertura, min(24, max(cierre, apertura + 1)), dias


def hay_simulados(desde: date, hasta: date) -> bool:
    """¿Hay clientes simulados con llegadas o transiciones en el periodo? Se avisa en pantalla."""
    inicio, fin = limites(desde, hasta)
    por_llegada = Cliente.objects.filter(
        correo__endswith=DOMINIO,
        solicitudes__timestamp_llegada__gte=inicio,
        solicitudes__timestamp_llegada__lt=fin,
    ).exists()
    # Un cliente simulado que llegó antes del periodo pero avanzó de etapa dentro de él también
    # alimenta la matriz P.
    por_transicion = SeguimientoEtapa.objects.filter(
        solicitud__cliente__correo__endswith=DOMINIO,
        fecha_transicion__gte=inicio,
        fecha_transicion__lt=fin,
    ).exists()
    return por_llegada or por_transicion

