"""Teoría de colas M/M/1 y M/M/c (HU-08, RF-51, RF-52, RF-53, RN-41).

Módulo de Python puro: **no importa Django**. Los tiempos pueden ir en cualquier unidad, siempre
que λ y μ usen la misma (clientes por hora → W y Wq salen en horas).

Modelo: llegadas de Poisson con tasa λ, c servidores y tiempos de servicio exponenciales con
tasa μ cada uno, cola FIFO sin límite. Con a = λ/μ (carga ofrecida) y ρ = λ/(cμ):

    C(c, a) = probabilidad de que un cliente que llega tenga que esperar (Erlang C)
    Lq = C·ρ/(1 − ρ)      Wq = Lq/λ      W = Wq + 1/μ      L = λ·W

Solo hay régimen estable si ρ < 1 (RN-41). Con ρ ≥ 1 la fila crece sin límite y L, Lq, W, Wq no
existen: se devuelve `estable = False` y esas cifras en None, en lugar de números sin sentido.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

RHO_AL_LIMITE = 0.95  # por encima, el sistema es estable pero la espera se dispara


@dataclass(frozen=True)
class Cola:
    lam: float  # tasa de llegadas λ
    mu: float  # tasa de servicio μ de cada servidor
    c: int  # servidores
    rho: float  # utilización ρ = λ/(cμ)
    estable: bool  # ρ < 1
    p_espera: float | None  # Erlang C: probabilidad de tener que esperar
    L: float | None  # clientes en el sistema
    Lq: float | None  # clientes en la fila
    W: float | None  # tiempo en el sistema
    Wq: float | None  # tiempo en la fila

    @property
    def al_limite(self) -> bool:
        """Estable pero con ρ > 0,95: λ y μ se estiman con error, y a esa carga una pequeña
        diferencia cambia la espera de minutos a horas. Conviene advertirlo en pantalla."""
        return self.estable and self.rho > RHO_AL_LIMITE


def _validar(lam: float, mu: float, c: int) -> None:
    if lam < 0:
        raise ValueError("λ no puede ser negativa.")
    if mu <= 0:
        raise ValueError("μ debe ser positiva.")
    if not isinstance(c, int) or isinstance(c, bool) or c < 1:
        raise ValueError("c debe ser un entero de al menos 1.")


def erlang_b(c: int, a: float) -> float:
    """Probabilidad de bloqueo de Erlang B, por recursión (estable aunque c sea grande)."""
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    return b


def erlang_c(c: int, a: float) -> float:
    """Erlang C: P(esperar) con carga ofrecida a = λ/μ. Vale 1 si el sistema no es estable."""
    if a >= c:
        return 1.0
    if a == 0:
        return 0.0
    rho = a / c
    b = erlang_b(c, a)
    return b / (1.0 - rho * (1.0 - b))


def mmc(lam: float, mu: float, c: int) -> Cola:
    """Métricas del sistema M/M/c. Con ρ ≥ 1 solo se informa la inestabilidad (RN-41)."""
    _validar(lam, mu, c)
    rho = lam / (c * mu)
    if rho >= 1.0:
        return Cola(lam, mu, c, rho, False, 1.0, None, None, None, None)
    if lam == 0:
        return Cola(lam, mu, c, 0.0, True, 0.0, 0.0, 0.0, 1.0 / mu, 0.0)
    p_espera = erlang_c(c, lam / mu)
    lq = p_espera * rho / (1.0 - rho)
    wq = lq / lam
    w = wq + 1.0 / mu
    return Cola(lam, mu, c, rho, True, p_espera, lam * w, lq, w, wq)


def mm1(lam: float, mu: float) -> Cola:
    """El caso de un solo servidor."""
    return mmc(lam, mu, 1)


def estimar_mu(duraciones: Iterable[float]) -> float:
    """μ = 1 / (duración media de atención) (RF-52). Las duraciones deben ser positivas.

    Solo deben entrar las atenciones **finalizadas** con inicio y fin (RN-22); eso lo decide
    quien lee los datos.
    """
    datos = list(duraciones)
    if not datos:
        raise ValueError("Se necesita al menos una duración para estimar μ.")
    if any(d <= 0 for d in datos):
        raise ValueError("Las duraciones deben ser positivas.")
    return len(datos) / sum(datos)


def tabla_por_servidores(lam: float, mu: float, c_max: int) -> list[Cola]:
    """El sistema para c = 1 … c_max (sirve para ver cómo baja la espera al sumar asesores)."""
    return [mmc(lam, mu, c) for c in range(1, c_max + 1)]


def c_minimo(lam: float, mu: float, wq_max: float, c_max: int = 100) -> int | None:
    """Menor número de servidores con régimen estable y Wq ≤ `wq_max` (RF-53).

    `wq_max` va en la misma unidad que 1/μ. Devuelve None si ni con `c_max` servidores se logra.
    """
    _validar(lam, mu, 1)
    if wq_max < 0:
        raise ValueError("El umbral de espera no puede ser negativo.")
    c = int(lam / mu) + 1  # menos que esto es inestable (ρ ≥ 1)
    while c <= c_max:
        cola = mmc(lam, mu, c)
        if cola.estable and cola.Wq <= wq_max:
            return c
        c += 1
    return None
