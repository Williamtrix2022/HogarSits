"""Llegadas de clientes como proceso de Poisson (HU-07, RF-50, RN-40, RN-42).

Módulo de Python puro: **no importa Django**. Recibe instantes (`datetime` con zona) y fechas, y
devuelve estructuras simples; la capa de Django se encarga de leerlos de la base de datos.

Qué calcula:
  * λ (clientes por hora) por franja: por hora del día y por (día de la semana, hora).
  * El ajuste de Poisson a los conteos observados: P(X = k) frente a la frecuencia observada, con
    la prueba χ² de bondad de ajuste y el índice de dispersión (var/media, ≈ 1 en un Poisson).

Qué hay que saber al interpretarlo:
  * Si las llegadas tienen picos (mañana y tarde, hallazgo de la ronda 1), el proceso **no es
    homogéneo** en el día. Mezclar las horas da un índice de dispersión `1 + Var(λ)/E(λ)`: mayor
    que 1, y el χ² lo rechaza **solo si los picos son marcados** (con picos suaves la diferencia
    es pequeña y no se detecta). El ajuste tiene sentido **por franja**, donde sí es Poisson.
  * Con pocas observaciones la estimación no es confiable (RN-40): cada franja trae `suficiente`.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from scipy.stats import chi2 as _chi2

ZONA_BOGOTA = "America/Bogota"  # RN-42: las franjas se calculan en hora local
MIN_LLEGADAS_FRANJA = 30  # RN-40 (valor de partida, a validar con datos reales)
LUNES_A_SABADO = (0, 1, 2, 3, 4, 5)


def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) para X ~ Poisson(λ). Se calcula en logaritmos para que no desborde."""
    if k < 0:
        return 0.0
    if lam < 0:
        raise ValueError("λ no puede ser negativa.")
    if lam == 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


@dataclass(frozen=True)
class Franja:
    """λ estimada de una franja. `dia_semana` es None cuando se agrupan todos los días."""

    dia_semana: int | None  # 0 = lunes … 6 = domingo
    hora: int
    dias_observados: int  # cuántas veces se observó la franja (cuántos días)
    llegadas: int  # total de llegadas en la franja
    lam: float  # clientes por hora (media de llegadas por observación)
    suficiente: bool  # RN-40: ¿hay llegadas suficientes para fiarse de λ?


def conteos_por_hora(
    llegadas: Iterable[datetime],
    desde: date,
    hasta: date,
    apertura: int = 8,
    cierre: int = 18,
    dias_laborales: tuple[int, ...] = LUNES_A_SABADO,
    zona: str = ZONA_BOGOTA,
) -> dict[tuple[date, int], int]:
    """Llegadas por (fecha local, hora). Incluye las horas **sin** llegadas (con 0).

    Los ceros importan: sin ellos λ saldría sobrestimada, porque solo se promediarían las horas
    en que hubo alguien. Solo se cuentan los días laborales y las horas de [apertura, cierre).
    """
    if desde > hasta:
        raise ValueError("`desde` no puede ser posterior a `hasta`.")
    if not 0 <= apertura < cierre <= 24:
        raise ValueError("Horario inválido: se requiere 0 <= apertura < cierre <= 24.")
    tz = ZoneInfo(zona)
    conteos: dict[tuple[date, int], int] = {}
    dia = desde
    while dia <= hasta:
        if dia.weekday() in dias_laborales:
            for hora in range(apertura, cierre):
                conteos[(dia, hora)] = 0
        dia += timedelta(days=1)
    for instante in llegadas:
        if instante.tzinfo is None:
            raise ValueError("Las llegadas deben traer zona horaria (RN-42).")
        local = instante.astimezone(tz)
        clave = (local.date(), local.hour)
        if clave in conteos:
            conteos[clave] += 1
    return conteos


def lambda_por_franja(
    conteos: dict[tuple[date, int], int],
    por_dia_semana: bool = False,
    minimo: int = MIN_LLEGADAS_FRANJA,
) -> list[Franja]:
    """λ por hora del día (o por día de la semana y hora). Ordenadas por franja."""
    grupos: dict[tuple[int | None, int], list[int]] = defaultdict(list)
    for (dia, hora), n in conteos.items():
        clave = (dia.weekday() if por_dia_semana else None, hora)
        grupos[clave].append(n)
    franjas = []
    orden = sorted(grupos.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1]))
    for (dia_semana, hora), lista in orden:
        total = sum(lista)
        franjas.append(
            Franja(
                dia_semana=dia_semana,
                hora=hora,
                dias_observados=len(lista),
                llegadas=total,
                lam=total / len(lista),
                suficiente=total >= minimo,
            )
        )
    return franjas


@dataclass(frozen=True)
class AjustePoisson:
    """Resultado de comparar los conteos observados con un Poisson(λ̂)."""

    n: int  # número de observaciones (horas)
    lam: float  # λ̂ = media de los conteos
    ks: tuple[int, ...]  # 0, 1, …, máximo observado
    observada: tuple[float, ...]  # frecuencia relativa observada de cada k
    esperada: tuple[float, ...]  # P(X = k) teórica (la última clase es «k o más»)
    indice_dispersion: float  # var/media; ≈ 1 si es Poisson, > 1 si hay ráfagas o picos
    chi2: float | None  # estadístico χ² (con clases agrupadas); None si no se puede probar
    grados_libertad: int  # clases agrupadas − 1 − 1 (se estimó λ)
    p_valor: float | None
    rechaza: bool | None  # True si p < α (no parece Poisson); None si no hay prueba


def ajuste_poisson(
    conteos: Iterable[int], minimo_esperado: float = 5.0, alfa: float = 0.05
) -> AjustePoisson:
    """Ajusta un Poisson a los conteos (llegadas por hora) y prueba la bondad de ajuste con χ².

    Las clases con frecuencia esperada menor que `minimo_esperado` se agrupan (regla habitual:
    el χ² solo es fiable con esperados ≥ 5). Si tras agrupar quedan menos de 3 clases no hay
    grados de libertad para probar y `chi2`, `p_valor` y `rechaza` son None.
    """
    datos = [int(c) for c in conteos]
    if not datos:
        raise ValueError("Se necesita al menos una observación.")
    if any(c < 0 for c in datos):
        raise ValueError("Los conteos no pueden ser negativos.")
    n = len(datos)
    lam = sum(datos) / n
    kmax = max(datos)
    ks = tuple(range(kmax + 1))
    frecuencias = [datos.count(k) / n for k in ks]
    esperada = [poisson_pmf(k, lam) for k in ks]
    esperada[-1] = max(0.0, 1.0 - sum(esperada[:-1]))  # la última clase es «kmax o más»
    varianza = sum((c - lam) ** 2 for c in datos) / (n - 1) if n > 1 else 0.0
    dispersion = varianza / lam if lam > 0 else 0.0

    # Agrupar clases con esperado pequeño, de izquierda a derecha.
    obs_cls: list[float] = []
    esp_cls: list[float] = []
    acum_o = acum_e = 0.0
    for k in ks:
        acum_o += datos.count(k)
        acum_e += esperada[k] * n
        if acum_e >= minimo_esperado:
            obs_cls.append(acum_o)
            esp_cls.append(acum_e)
            acum_o = acum_e = 0.0
    if acum_e > 0 or acum_o > 0:  # lo que sobra se une a la última clase
        if esp_cls:
            obs_cls[-1] += acum_o
            esp_cls[-1] += acum_e
        else:
            obs_cls.append(acum_o)
            esp_cls.append(acum_e)

    gl = len(esp_cls) - 2
    if gl < 1:
        estadistico = p_valor = rechaza = None
    else:
        estadistico = sum((o - e) ** 2 / e for o, e in zip(obs_cls, esp_cls, strict=True))
        p_valor = float(_chi2.sf(estadistico, gl))
        rechaza = p_valor < alfa
    return AjustePoisson(
        n=n,
        lam=lam,
        ks=ks,
        observada=tuple(frecuencias),
        esperada=tuple(esperada),
        indice_dispersion=dispersion,
        chi2=estadistico,
        grados_libertad=gl,
        p_valor=p_valor,
        rechaza=rechaza,
    )
