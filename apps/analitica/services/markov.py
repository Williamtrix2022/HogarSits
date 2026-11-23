"""Cadena de Markov de las etapas comerciales (HU-09, RF-54, RF-55, RN-31, RN-40, RN-43, ADR-002).

Módulo de Python puro: **no importa Django**. Recibe pares (origen, destino) de etapas y devuelve
la matriz P estimada y el análisis de absorción.

Estados: 1 Consulta, 2 Visita, 3 Negociación (transitorios) · 4 Cierre, 5 Abandono (absorbentes).

    P[i][j] = n_ij / Σ_j n_ij        (frecuencia relativa de las transiciones observadas)

Según el ADR-002, un seguimiento que no cambia la etapa se registra como transición con
origen = destino, y **se cuenta** en la diagonal. Por eso un «paso» es un seguimiento, no un día.

Con Q (transitorios → transitorios) y R (transitorios → absorbentes):

    N = (I − Q)⁻¹    matriz fundamental (visitas esperadas a cada etapa)
    B = N·R           probabilidad de acabar en Cierre o en Abandono, según la etapa inicial
    t = N·1           pasos esperados hasta la absorción

RN-43: las filas de P suman 1; una etapa **sin observaciones no se inventa**: su fila queda en
None, se informa, y no se calcula la absorción hasta tenerla.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

CONSULTA, VISITA, NEGOCIACION, CIERRE, ABANDONO = 1, 2, 3, 4, 5
TRANSITORIOS = (CONSULTA, VISITA, NEGOCIACION)
ABSORBENTES = (CIERRE, ABANDONO)
NOMBRES = {1: "Consulta", 2: "Visita", 3: "Negociación", 4: "Cierre", 5: "Abandono"}
MIN_TRANSICIONES_ESTADO = 30  # RN-40 (valor de partida, a validar con datos reales)


def contar_transiciones(pares: Iterable[tuple[int, int]]) -> np.ndarray:
    """Matriz 5x5 de conteos n_ij. Filas y columnas son las etapas 1 a 5 (índice = etapa − 1)."""
    conteos = np.zeros((5, 5), dtype=int)
    for origen, destino in pares:
        if origen not in NOMBRES or destino not in NOMBRES:
            raise ValueError(f"Etapa inválida en la transición ({origen}, {destino}).")
        if origen in ABSORBENTES:
            raise ValueError(
                f"Hay una transición que sale de {NOMBRES[origen]}: es un estado absorbente."
            )
        conteos[origen - 1, destino - 1] += 1
    return conteos


@dataclass(frozen=True)
class Estimacion:
    """La matriz P estimada y cuánta evidencia hay detrás de cada fila."""

    conteos: tuple[tuple[int, ...], ...]  # n_ij
    n_por_origen: tuple[int, ...]  # transiciones observadas que salen de cada etapa
    matriz: tuple[tuple[float, ...] | None, ...]  # P; None donde no hay observaciones (RN-43)
    faltan: tuple[int, ...]  # etapas transitorias sin ninguna observación
    pocas: tuple[int, ...]  # etapas con observaciones, pero menos que el mínimo (RN-40)
    minimo: int

    @property
    def completa(self) -> bool:
        """¿Hay observaciones en las tres etapas transitorias? Sin esto no hay absorción."""
        return not self.faltan

    @property
    def suficiente(self) -> bool:
        return self.completa and not self.pocas


def estimar_matriz(
    pares: Iterable[tuple[int, int]], minimo: int = MIN_TRANSICIONES_ESTADO
) -> Estimacion:
    """Estima P con frecuencias relativas. Cierre y Abandono son absorbentes por definición."""
    conteos = contar_transiciones(pares)
    filas: list[tuple[float, ...] | None] = []
    faltan, pocas = [], []
    for etapa in range(1, 6):
        fila = conteos[etapa - 1]
        total = int(fila.sum())
        if etapa in ABSORBENTES:  # RN-31: no se estiman, se definen
            filas.append(tuple(1.0 if j == etapa - 1 else 0.0 for j in range(5)))
        elif total == 0:  # RN-43: no se inventa la fila
            filas.append(None)
            faltan.append(etapa)
        else:
            filas.append(tuple(float(x) / total for x in fila))
            if total < minimo:
                pocas.append(etapa)
    n_por_origen = tuple(int(conteos[e - 1].sum()) for e in range(1, 6))
    return Estimacion(
        conteos=tuple(tuple(int(x) for x in f) for f in conteos),
        n_por_origen=n_por_origen,
        matriz=tuple(filas),
        faltan=tuple(faltan),
        pocas=tuple(pocas),
        minimo=minimo,
    )


@dataclass(frozen=True)
class Absorcion:
    """Resultado del análisis de absorción, indexado por etapa transitoria (1, 2, 3)."""

    N: tuple[tuple[float, ...], ...]  # matriz fundamental 3x3
    p_cierre: tuple[float, ...]  # P(acabar en Cierre | etapa inicial)
    p_abandono: tuple[float, ...]  # P(acabar en Abandono | etapa inicial)
    pasos: tuple[float, ...]  # pasos esperados hasta Cierre o Abandono

    def desde(self, etapa: int) -> dict[str, float]:
        i = TRANSITORIOS.index(etapa)
        return {
            "p_cierre": self.p_cierre[i],
            "p_abandono": self.p_abandono[i],
            "pasos": self.pasos[i],
        }


def validar_matriz(matriz: Sequence[Sequence[float] | None], tolerancia: float = 1e-9) -> None:
    """RN-43: 5x5, sin probabilidades negativas, filas que suman 1 y estados 4 y 5 absorbentes."""
    if len(matriz) != 5 or any(f is not None and len(f) != 5 for f in matriz):
        raise ValueError("La matriz de transición debe ser de 5x5.")
    for i, fila in enumerate(matriz, start=1):
        if fila is None:
            if i in TRANSITORIOS:
                raise ValueError(f"Falta la fila de {NOMBRES[i]}: no hay observaciones (RN-43).")
            continue
        if any(p < 0 for p in fila):
            raise ValueError(f"La fila de {NOMBRES[i]} tiene probabilidades negativas.")
        if not math.isclose(sum(fila), 1.0, abs_tol=tolerancia):
            raise ValueError(f"La fila de {NOMBRES[i]} debe sumar 1 (suma {sum(fila):.6f}).")
    if tuple(matriz[3] or ()) != (0, 0, 0, 1, 0) or tuple(matriz[4] or ()) != (0, 0, 0, 0, 1):
        raise ValueError("Cierre (4) y Abandono (5) deben ser estados absorbentes.")


def analizar_absorcion(matriz: Sequence[Sequence[float] | None]) -> Absorcion:
    """Matriz fundamental, probabilidades de absorción y pasos esperados (RF-55)."""
    validar_matriz(matriz)
    P = np.array(matriz, dtype=float)
    Q, R = P[:3, :3], P[:3, 3:]
    try:
        N = np.linalg.inv(np.eye(3) - Q)
    except np.linalg.LinAlgError as error:
        raise ValueError(
            "Alguna etapa transitoria nunca sale (probabilidad 1 de quedarse): "
            "no hay absorción. Faltan datos de salida."
        ) from error
    B = N @ R
    pasos = N.sum(axis=1)
    return Absorcion(
        N=tuple(tuple(float(x) for x in fila) for fila in N),
        p_cierre=tuple(float(x) for x in B[:, 0]),
        p_abandono=tuple(float(x) for x in B[:, 1]),
        pasos=tuple(float(x) for x in pasos),
    )


@dataclass(frozen=True)
class Analisis:
    estimacion: Estimacion
    absorcion: Absorcion | None  # None si faltan observaciones en alguna etapa (RN-43)


def analizar(
    pares: Iterable[tuple[int, int]], minimo: int = MIN_TRANSICIONES_ESTADO
) -> Analisis:
    """Estima P desde las transiciones y, si es posible, calcula la absorción."""
    estimacion = estimar_matriz(pares, minimo)
    if not estimacion.completa:
        return Analisis(estimacion, None)
    try:
        return Analisis(estimacion, analizar_absorcion(estimacion.matriz))
    except ValueError:  # una etapa que solo se repite: sin salida observada
        return Analisis(estimacion, None)
