"""Validación de los modelos: parámetros estimados frente a los usados para simular (RF-61, HU-10).

Módulo de Python puro: **no importa Django**. La idea es la de toda validación con datos
sintéticos: como el simulador conoce λ, μ y P *verdaderos*, se corren los mismos servicios que usa
el panel sobre los datos que genera y se mide **cuánto se equivocan**. Si el error es pequeño y se
reduce al tener más datos, el código estima bien; lo que quede de error es el límite del método.

Qué mide:
  * λ por día laboral y λ por hora (la forma del perfil con picos).
  * μ (a partir de las duraciones de atención).
  * La matriz P, la probabilidad de cierre desde Consulta y los pasos esperados.
  * La calibración de la prueba χ² de Poisson: con datos que SON de Poisson, se rechaza cerca del
    5 % de las veces (α = 0,05). Mucho más o mucho menos sería un defecto de la prueba.
  * La espera simulada frente a la que predice M/M/c, con c nominal y con c efectivo (asesores
    menos los que están en visita). Esto **no** valida el código sino el **supuesto** del modelo.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from . import colas, markov, poisson
from . import simulacion as sim


@dataclass(frozen=True)
class Medida:
    nombre: str
    unidad: str
    verdadero: float
    estimado: float

    @property
    def error(self) -> float:
        return self.estimado - self.verdadero

    @property
    def error_relativo(self) -> float:
        return self.error / self.verdadero if self.verdadero else math.nan


@dataclass(frozen=True)
class Validacion:
    parametros: sim.Parametros
    n_solicitudes: int
    n_transiciones: int
    medidas: tuple[Medida, ...]
    error_max_p: float  # máx |P estimada − P verdadera| en las filas transitorias
    error_max_lambda_hora: float  # máx |λ̂ − λ| por hora, en clientes/hora
    franjas_suficientes: int
    franjas_total: int
    probadas_poisson: int  # franjas con datos para el χ²
    rechazos_poisson: int  # de ellas, las que el χ² rechaza al 5 %
    espera_simulada_min: float
    c_nominal: int
    c_efectivo: float
    espera_modelo_nominal_min: float | None  # M/M/c con c nominal; None si inestable
    espera_modelo_efectivo_min: float | None  # M/M/c con c efectivo; None si inestable
    espera_modelo_por_franja_min: float | None  # M/M/c hora por hora; None si alguna es inestable

    def medida(self, nombre: str) -> Medida:
        return next(m for m in self.medidas if m.nombre == nombre)


def _dias_laborales(p: sim.Parametros) -> list[date]:
    dias = [p.fecha_inicio + timedelta(days=i) for i in range(p.dias)]
    return [d for d in dias if d.weekday() in p.dias_laborales]


def _redondear(x: float) -> int:
    return max(1, int(x + 0.5))  # mitades hacia arriba (Python redondea al par)


def _libres_por_franja(
    r: sim.Resultado, claves: list[tuple[date, int]]
) -> dict[tuple[date, int], int]:
    """Asesores menos los que están en visita, en cada franja (fecha, hora)."""
    p = r.parametros
    zona = ZoneInfo(p.zona)
    ocupados: dict[tuple[date, int], set[int]] = defaultdict(set)
    for s in r.solicitudes:
        for v in s.visitas:
            ini, fin = v.inicio.astimezone(zona), v.fin.astimezone(zona)
            t = ini.replace(minute=0, second=0, microsecond=0)
            while t < fin:
                if ini < t + timedelta(hours=1) and fin > t:  # la visita toca esa hora
                    ocupados[(t.date(), t.hour)].add(v.asesor)
                t += timedelta(hours=1)
    return {k: p.n_asesores - len(ocupados.get(k, ())) for k in claves}


def _espera_por_franja(lam_por_hora: dict[int, float], libres: dict[tuple[date, int], int],
                       mu: float) -> float | None:
    """Espera media (min) del modelo aplicado **hora por hora**, ponderada por las llegadas.

    Cada hora del día usa su propia λ y el promedio de asesores libres a esa hora. Es lo que un
    modelo único para todo el día esconde: a las horas pico suele haber menos asesores libres.
    Devuelve None si alguna hora es inestable (la espera media no existe).
    """
    por_hora: dict[int, list[int]] = defaultdict(list)
    for (_, h), c in libres.items():
        por_hora[h].append(c)
    total = pesos = 0.0
    for h, lam in lam_por_hora.items():
        c = _redondear(sum(por_hora[h]) / len(por_hora[h]))
        q = colas.mmc(lam, mu, c)
        if not q.estable:
            return None
        total += lam * q.Wq * 60
        pesos += lam
    return total / pesos if pesos else None


def validar(p: sim.Parametros) -> Validacion:
    """Simula con `p`, estima con los servicios y compara con los valores verdaderos."""
    p.validar()
    r = sim.simular(p)
    sol = r.solicitudes
    hasta = p.fecha_inicio + timedelta(days=p.dias - 1)

    # --- Demanda: λ -----------------------------------------------------------------------
    conteos = poisson.conteos_por_hora(
        [s.llegada for s in sol], p.fecha_inicio, hasta, p.hora_apertura, p.hora_cierre,
        p.dias_laborales, p.zona,
    )
    n_dias = len(_dias_laborales(p))
    lam_dia = sum(conteos.values()) / n_dias
    franjas = poisson.lambda_por_franja(conteos)
    pesos = p.perfil_horario or sim.perfil_horario_por_defecto(p.hora_apertura, p.hora_cierre)
    verdadero_hora = {h: p.clientes_por_dia * w for h, w in zip(
        range(p.hora_apertura, p.hora_cierre), pesos, strict=True)}
    err_hora = max(abs(f.lam - verdadero_hora[f.hora]) for f in franjas)

    probadas = rechazos = 0
    for f in franjas:
        if f.suficiente:
            a = poisson.ajuste_poisson([n for (_, h), n in conteos.items() if h == f.hora])
            if a.probado:
                probadas += 1
                rechazos += bool(a.rechaza)

    # --- Servicio: μ ----------------------------------------------------------------------
    horas_servicio = [(s.fin - s.inicio).total_seconds() / 3600 for s in sol if s.fin > s.inicio]
    mu_est = colas.estimar_mu(horas_servicio)
    mu_real = 60 / p.servicio_medio_min

    # --- Markov: P ------------------------------------------------------------------------
    pares = [(e.origen, e.destino) for s in sol for e in s.etapas]
    est = markov.estimar_matriz(pares)
    real = markov.analizar_absorcion(p.matriz)
    medidas = [
        Medida("λ por día laboral", "clientes/día", p.clientes_por_dia, lam_dia),
        Medida("μ", "clientes/hora por asesor", mu_real, mu_est),
    ]
    err_p = math.nan
    if est.completa:
        err_p = max(
            abs(est.matriz[i][j] - p.matriz[i][j]) for i in range(3) for j in range(5)
        )
        a = markov.analizar(pares).absorcion
        if a is not None:
            medidas += [
                Medida("P(cierre desde Consulta)", "probabilidad", real.p_cierre[0], a.p_cierre[0]),
                Medida("Pasos esperados desde Consulta", "seguimientos", real.pasos[0], a.pasos[0]),
            ]

    # --- Espera: simulada frente a M/M/c ----------------------------------------------------
    espera_sim = sum((s.inicio - s.llegada).total_seconds() for s in sol) / len(sol) / 60
    libres = _libres_por_franja(r, list(conteos))
    c_efectivo = sum(libres.values()) / len(libres)
    lam_hora = sum(conteos.values()) / len(conteos)

    def espera_modelo(c: int) -> float | None:
        q = colas.mmc(lam_hora, mu_est, c)
        return q.Wq * 60 if q.estable else None

    return Validacion(
        parametros=p, n_solicitudes=len(sol), n_transiciones=len(pares), medidas=tuple(medidas),
        error_max_p=err_p, error_max_lambda_hora=err_hora,
        franjas_suficientes=sum(f.suficiente for f in franjas), franjas_total=len(franjas),
        probadas_poisson=probadas, rechazos_poisson=rechazos, espera_simulada_min=espera_sim,
        c_nominal=p.n_asesores, c_efectivo=c_efectivo,
        espera_modelo_nominal_min=espera_modelo(p.n_asesores),
        espera_modelo_efectivo_min=espera_modelo(_redondear(c_efectivo)),
        espera_modelo_por_franja_min=_espera_por_franja(
            {f.hora: f.lam for f in franjas}, libres, mu_est
        ),
    )


@dataclass(frozen=True)
class ResumenMedida:
    nombre: str
    unidad: str
    verdadero: float
    media_estimada: float
    desviacion: float  # de las estimaciones entre réplicas
    sesgo: float  # media(estimado) − verdadero
    error_rel_abs_medio: float  # media de |error relativo|
    error_rel_abs_p95: float  # percentil 95 de |error relativo|
    n: int  # réplicas en las que se pudo estimar


@dataclass(frozen=True)
class ResumenReplicas:
    parametros: sim.Parametros
    replicas: int
    medidas: tuple[ResumenMedida, ...]
    error_max_p_medio: float
    error_max_lambda_hora_medio: float
    tasa_rechazo_poisson: float  # rechazos / franjas probadas (esperado ≈ 0,05)
    franjas_suficientes: float  # fracción media
    sin_absorcion: int  # réplicas donde faltaron datos para P(cierre)
    espera_simulada_min: float
    espera_modelo_nominal_min: float | None
    espera_modelo_efectivo_min: float | None
    espera_modelo_por_franja_min: float | None
    c_efectivo: float


def _media(xs):
    xs = [x for x in xs if x is not None and not math.isnan(x)]
    return float(np.mean(xs)) if xs else None


def validar_replicas(p: sim.Parametros, replicas: int = 20) -> ResumenReplicas:
    """Repite la validación con semillas distintas y resume sesgo, dispersión y error."""
    if replicas < 2:
        raise ValueError("Se necesitan al menos 2 réplicas.")
    corridas = [validar(replace(p, semilla=p.semilla + i)) for i in range(replicas)]
    por_nombre: dict[str, list[Medida]] = defaultdict(list)
    for c in corridas:
        for m in c.medidas:
            por_nombre[m.nombre].append(m)
    resumen = []
    for nombre, ms in por_nombre.items():
        est = np.array([m.estimado for m in ms])
        rel = np.abs([m.error_relativo for m in ms])
        resumen.append(ResumenMedida(
            nombre=nombre, unidad=ms[0].unidad, verdadero=ms[0].verdadero,
            media_estimada=float(est.mean()), desviacion=float(est.std(ddof=1)),
            sesgo=float(est.mean() - ms[0].verdadero), error_rel_abs_medio=float(rel.mean()),
            error_rel_abs_p95=float(np.percentile(rel, 95)), n=len(ms),
        ))
    probadas = sum(c.probadas_poisson for c in corridas)
    return ResumenReplicas(
        parametros=p, replicas=replicas, medidas=tuple(resumen),
        error_max_p_medio=_media([c.error_max_p for c in corridas]),
        error_max_lambda_hora_medio=_media([c.error_max_lambda_hora for c in corridas]),
        tasa_rechazo_poisson=(
            sum(c.rechazos_poisson for c in corridas) / probadas if probadas else math.nan
        ),
        franjas_suficientes=_media([c.franjas_suficientes / c.franjas_total for c in corridas]),
        sin_absorcion=sum(1 for c in corridas if len(c.medidas) < 4),
        espera_simulada_min=_media([c.espera_simulada_min for c in corridas]),
        espera_modelo_nominal_min=_media([c.espera_modelo_nominal_min for c in corridas]),
        espera_modelo_efectivo_min=_media([c.espera_modelo_efectivo_min for c in corridas]),
        espera_modelo_por_franja_min=_media([c.espera_modelo_por_franja_min for c in corridas]),
        c_efectivo=_media([c.c_efectivo for c in corridas]),
    )


# Escenarios de SUPUESTOS_DE_TRABAJO.md (todos hipotéticos: sirven para medir sensibilidad).
_MAS = ((0.4, 0.375, 0, 0, 0.225), (0, 0.3, 0.371, 0, 0.329), (0, 0, 0.4, 0.413, 0.187),
        (0, 0, 0, 1, 0), (0, 0, 0, 0, 1))
ESCENARIOS: dict[str, dict] = {
    "base": {},
    "oficina cargada": dict(clientes_por_dia=20, n_asesores=2, servicio_medio_min=45,
                            hora_apertura=7, hora_cierre=19),
    "oficina cargada + 3er asesor": dict(clientes_por_dia=20, n_asesores=3, servicio_medio_min=45,
                                         hora_apertura=7, hora_cierre=19),
    "oficina cargada, visitas cortas": dict(clientes_por_dia=20, n_asesores=2,
                                            servicio_medio_min=45, hora_apertura=7,
                                            hora_cierre=19, visita_min=30, visita_max=45),
    "más permanencia": dict(matriz=_MAS),
    "seguimiento lento": dict(dias_entre_etapas=5.0),
}


def parametros_de(escenario: str, fecha_inicio: date, dias: int, semilla: int) -> sim.Parametros:
    if escenario not in ESCENARIOS:
        raise ValueError(f"Escenario desconocido: {escenario!r}. Opciones: {sorted(ESCENARIOS)}.")
    return sim.Parametros(
        fecha_inicio=fecha_inicio, dias=dias, semilla=semilla, **ESCENARIOS[escenario]
    )


__all__ = [
    "ESCENARIOS", "Medida", "ResumenMedida", "ResumenReplicas", "Validacion",
    "parametros_de", "validar", "validar_replicas",
]
