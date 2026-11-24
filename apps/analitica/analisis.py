"""Ensambla el análisis de un periodo: lee los datos, llama a los servicios y deja las
advertencias (RF-50 a RF-57, RN-40 a RN-43). No calcula matemática propia: orquesta.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

from apps.agenda.disponibilidad import c_efectivo_por_hora
from apps.analitica import datos
from apps.analitica.services import colas, markov, poisson
from apps.analitica.services.colas import Cola
from apps.analitica.services.markov import Analisis as AnalisisMarkov
from apps.analitica.services.poisson import AjustePoisson, Franja
from apps.analitica.textos import num

UMBRAL_ESPERA_MIN = 20  # minutos; configurable en pantalla (RF-53, pendiente de validar)
C_MAXIMO = 50


@dataclass(frozen=True)
class Resumen:
    desde: date
    hasta: date
    apertura: int
    cierre: int
    dias_laborales: tuple[int, ...]
    # Demanda (HU-07)
    n_llegadas: int  # las que caen dentro del horario de atención
    n_fuera_de_horario: int  # las que quedan fuera (no entran en λ)
    franjas: list[Franja]
    franja_pico: Franja | None
    franja_valle: Franja | None
    ajuste_pico: AjustePoisson | None
    ajuste_global: AjustePoisson | None
    lam_hora: float | None  # clientes por hora laboral, promedio
    # Colas (HU-08)
    n_servicios: int
    servicio_medio_min: float | None
    mu_hora: float | None
    c_promedio: float | None
    c_usado: int | None
    cola: Cola | None
    lam_pico: float | None
    c_pico: int | None
    cola_pico: Cola | None
    c_recomendado: int | None
    tabla_c: list[Cola]
    umbral_min: float
    # Markov (HU-09)
    markov: AnalisisMarkov
    n_transiciones: int
    # Contexto
    hay_simulados: bool
    advertencias: list[str] = field(default_factory=list)

    @property
    def hay_datos(self) -> bool:
        return self.n_llegadas > 0 or self.n_transiciones > 0


def _redondear_c(promedio: float | None) -> int | None:
    return None if promedio is None else max(1, round(promedio))


def analizar_periodo(desde: date, hasta: date, umbral_min: float = UMBRAL_ESPERA_MIN) -> Resumen:
    if desde > hasta:
        raise ValueError("`desde` no puede ser posterior a `hasta`.")
    apertura, cierre, dias = datos.horario_de_atencion()
    advertencias: list[str] = []

    # --- Demanda: λ por franja y ajuste de Poisson ---------------------------------------
    llegadas = datos.llegadas(desde, hasta)
    conteos = poisson.conteos_por_hora(llegadas, desde, hasta, apertura, cierre, dias)
    n_dentro = sum(conteos.values())
    franjas = poisson.lambda_por_franja(conteos)
    suficientes = [f for f in franjas if f.suficiente]
    candidatas = suficientes or franjas
    pico = max(candidatas, key=lambda f: f.lam, default=None)
    valle = min(candidatas, key=lambda f: f.lam, default=None)
    if pico is not None and pico.lam == 0:
        pico = valle = None  # sin llegadas no hay hora pico
    ajuste_pico = (
        poisson.ajuste_poisson([n for (_, h), n in conteos.items() if h == pico.hora])
        if pico is not None
        else None
    )
    ajuste_global = poisson.ajuste_poisson(list(conteos.values())) if conteos else None
    lam_hora = n_dentro / len(conteos) if conteos else None
    fuera = len(llegadas) - n_dentro
    if fuera:
        advertencias.append(
            f"{fuera} llegada(s) cayeron fuera del horario de atención o en días sin turno y "
            "no se cuentan para λ."
        )
    pocas = [f for f in franjas if not f.suficiente]
    if pocas and franjas:
        advertencias.append(
            f"Pocos datos: {len(pocas)} de {len(franjas)} franjas tienen menos de "
            f"{poisson.MIN_LLEGADAS_FRANJA} llegadas. Esas estimaciones no son confiables (RN-40)."
        )

    # --- Colas: μ, c efectivo y espera ---------------------------------------------------
    duraciones = datos.duraciones_de_servicio_en_horas(desde, hasta)
    mu = colas.estimar_mu(duraciones) if duraciones else None
    servicio_min = 60 / mu if mu else None
    if duraciones and len(duraciones) < poisson.MIN_LLEGADAS_FRANJA:
        advertencias.append(
            f"Solo hay {len(duraciones)} atenciones finalizadas para estimar el tiempo de "
            "servicio: la cifra no es confiable (RN-40)."
        )
    if not duraciones and llegadas:
        advertencias.append(
            "No hay atenciones finalizadas con hora de inicio y fin: no se puede estimar el "
            "tiempo de servicio (RN-22)."
        )

    c_por_hora = c_efectivo_por_hora(conteos.keys())
    hay_horarios = bool(c_por_hora) and datos.hay_horarios()
    c_prom = sum(c_por_hora.values()) / len(c_por_hora) if c_por_hora and hay_horarios else None
    if c_prom is None and conteos:
        advertencias.append(
            "No hay horarios de asesores cargados: no se sabe cuántos asesores hay disponibles "
            "y no se calculan las esperas. Cárguelos en Administración → Horarios."
        )
    elif c_prom is not None and c_prom < 1:
        advertencias.append(
            f"En promedio hay menos de un asesor libre ({num(c_prom, 2)}): casi siempre "
            "están en visita o fuera de turno."
        )
    c_usado = _redondear_c(c_prom)

    cola = None
    if lam_hora and mu and c_usado:
        cola = colas.mmc(lam_hora, mu, c_usado)

    lam_pico = pico.lam if pico else None
    c_pico = None
    if pico is not None and hay_horarios:
        a_esa_hora = [c for (_, h), c in c_por_hora.items() if h == pico.hora]
        c_pico = _redondear_c(sum(a_esa_hora) / len(a_esa_hora)) if a_esa_hora else None
    cola_pico = colas.mmc(lam_pico, mu, c_pico) if lam_pico and mu and c_pico else None
    c_recomendado = None
    tabla: list[Cola] = []
    if lam_pico and mu:
        c_recomendado = colas.c_minimo(lam_pico, mu, umbral_min / 60, C_MAXIMO)
        tope = max(6, (c_recomendado or 0) + 2)
        tabla = colas.tabla_por_servidores(lam_pico, mu, tope)
    for etiqueta, q in (("en promedio", cola), ("en la hora pico", cola_pico)):
        if q is not None and q.al_limite:
            advertencias.append(
                f"La carga {etiqueta} (ρ = {num(q.rho, 2)}) está casi al límite: una pequeña "
                "diferencia en λ o μ cambia la espera de minutos a horas."
            )

    # --- Markov: matriz P y absorción ----------------------------------------------------
    pares = datos.transiciones(desde, hasta)
    resultado = markov.analizar(pares)
    est = resultado.estimacion
    if pares and not est.completa:
        nombres = ", ".join(markov.NOMBRES[e] for e in est.faltan)
        advertencias.append(
            f"Faltan transiciones desde {nombres}: no se inventa la fila de la matriz y no se "
            "calcula la probabilidad de cierre (RN-43)."
        )
    elif pares and est.pocas:
        nombres = ", ".join(f"{markov.NOMBRES[e]} ({est.n_por_origen[e - 1]})" for e in est.pocas)
        advertencias.append(
            f"Pocas transiciones desde {nombres}: menos de {est.minimo}. La estimación no es "
            "confiable (RN-40)."
        )
    elif pares and est.completa and resultado.absorcion is None:
        advertencias.append(
            "Alguna etapa casi nunca sale: no se puede calcular cuánto tarda en cerrar."
        )

    simulados = datos.hay_simulados(desde, hasta)
    if simulados:
        advertencias.append(
            "Este periodo incluye datos simulados (clientes @sim.hogarsits.test). Las cifras "
            "no describen a ninguna inmobiliaria real."
        )

    return Resumen(
        desde=desde, hasta=hasta, apertura=apertura, cierre=cierre, dias_laborales=dias,
        n_llegadas=n_dentro, n_fuera_de_horario=fuera, franjas=franjas,
        franja_pico=pico, franja_valle=valle, ajuste_pico=ajuste_pico,
        ajuste_global=ajuste_global, lam_hora=lam_hora,
        n_servicios=len(duraciones), servicio_medio_min=servicio_min, mu_hora=mu,
        c_promedio=c_prom, c_usado=c_usado, cola=cola, lam_pico=lam_pico, c_pico=c_pico,
        cola_pico=cola_pico, c_recomendado=c_recomendado, tabla_c=tabla, umbral_min=umbral_min,
        markov=resultado, n_transiciones=len(pares), hay_simulados=simulados,
        advertencias=advertencias,
    )


def rango_por_defecto(dias: int = 30) -> tuple[date, date]:
    """Los últimos `dias` días **con datos** (no los últimos del calendario): así el panel no
    aparece vacío cuando los datos son de hace semanas."""
    periodo = datos.periodo_con_datos()
    if periodo is None:
        hoy = date.today()
        return hoy - timedelta(days=dias - 1), hoy
    primero, ultimo = periodo
    return max(primero, ultimo - timedelta(days=dias - 1)), ultimo
