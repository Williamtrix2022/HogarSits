"""Colas M/M/1 y M/M/c (#36, HU-08, RF-51 a RF-53, RN-41). Python puro, sin BD."""

import math
from datetime import date

import numpy as np
import pytest

from apps.analitica.services import colas
from apps.analitica.services import simulacion as sim


def lq_numerico(lam, mu, c, estados=4000):
    """Lq resolviendo a mano la cadena de nacimiento y muerte (truncada), sin las fórmulas."""
    logp = np.zeros(estados)  # log de p_n sin normalizar
    for n in range(1, estados):
        logp[n] = logp[n - 1] + math.log(lam) - math.log(min(n, c) * mu)
    p = np.exp(logp - logp.max())
    p /= p.sum()
    return float(sum((n - c) * p[n] for n in range(c + 1, estados)))


# --- Ejemplo de la Propuesta (M/M/1, λ = 2, μ = 3) ----------------------------------------
def test_mm1_ejemplo_de_la_propuesta():
    q = colas.mm1(2, 3)
    assert q.estable
    assert q.rho == pytest.approx(2 / 3)
    assert q.L == pytest.approx(2.0)
    assert q.W == pytest.approx(1.0)
    assert q.Lq == pytest.approx(4 / 3)
    assert q.Wq == pytest.approx(2 / 3)
    assert q.p_espera == pytest.approx(2 / 3)  # en M/M/1 P(esperar) = ρ


def test_mmc_con_un_servidor_coincide_con_las_formulas_de_mm1():
    for lam, mu in [(1, 2), (2, 3), (0.5, 0.6), (9, 10)]:
        q = colas.mmc(lam, mu, 1)
        rho = lam / mu
        assert q.Lq == pytest.approx(rho**2 / (1 - rho))
        assert q.L == pytest.approx(rho / (1 - rho))
        assert q.Wq == pytest.approx(rho / (mu - lam))


# --- Ejemplos del wireframe W11 (λ = 20 clientes/12 h, μ = 1 cliente/45 min) --------------
LAM_W11, MU_W11 = 20 / 12, 60 / 45  # por hora


def test_dos_asesores_esperan_unos_29_minutos():
    q = colas.mmc(LAM_W11, MU_W11, 2)
    assert q.rho == pytest.approx(0.625)
    assert q.Wq * 60 == pytest.approx(28.8, abs=0.1)  # «unos 29 min» en W11


def test_tres_asesores_esperan_unos_4_minutos():
    q = colas.mmc(LAM_W11, MU_W11, 3)
    assert q.Wq * 60 == pytest.approx(4.0, abs=0.1)  # «unos 4» en W11 (menos de 5)


def test_recomienda_tres_asesores_para_esperar_menos_de_20_minutos():
    assert colas.c_minimo(LAM_W11, MU_W11, wq_max=20 / 60) == 3  # W11: «al menos 3»


# --- Erlang C y validación independiente --------------------------------------------------
def test_erlang_c_valores_conocidos():
    assert colas.erlang_c(2, 1.0) == pytest.approx(1 / 3)  # tabla de Erlang C
    assert colas.erlang_c(1, 0.5) == pytest.approx(0.5)  # c = 1: P(esperar) = ρ
    assert colas.erlang_c(3, 0.0) == 0.0
    assert colas.erlang_c(2, 2.0) == 1.0  # a ≥ c: inestable


@pytest.mark.parametrize(
    ("lam", "mu", "c"),
    [(1.0, 2.0, 1), (2.0, 3.0, 1), (5.0, 3.0, 2), (1.67, 1.33, 2), (1.67, 1.33, 3), (9.0, 1.0, 12)],
)
def test_lq_coincide_con_la_cadena_de_nacimiento_y_muerte(lam, mu, c):
    """Comprobación independiente: no usa Erlang C ni las fórmulas cerradas."""
    q = colas.mmc(lam, mu, c)
    assert q.Lq == pytest.approx(lq_numerico(lam, mu, c), rel=1e-6, abs=1e-9)


@pytest.mark.parametrize(("lam", "mu", "c"), [(2, 3, 1), (5, 3, 2), (1.67, 1.33, 3), (40, 1, 50)])
def test_se_cumple_la_ley_de_little(lam, mu, c):
    q = colas.mmc(lam, mu, c)
    assert q.L == pytest.approx(lam * q.W)
    assert q.Lq == pytest.approx(lam * q.Wq)
    assert q.W == pytest.approx(q.Wq + 1 / mu)
    assert q.L == pytest.approx(q.Lq + lam / mu)  # en el sistema = en fila + en servicio


def test_la_espera_baja_al_agregar_servidores():
    esperas = [q.Wq for q in colas.tabla_por_servidores(4.0, 1.0, 10) if q.estable]
    assert len(esperas) >= 3 and all(a > b for a, b in zip(esperas, esperas[1:], strict=False))


def test_no_desborda_con_muchos_servidores():
    q = colas.mmc(190, 1, 200)
    assert q.estable and 0 <= q.p_espera <= 1 and q.Wq >= 0


# --- Estabilidad (RN-41) ------------------------------------------------------------------
def test_con_rho_mayor_o_igual_a_uno_no_se_inventan_cifras():
    for lam, c in [(3, 2), (2, 2), (10, 1)]:  # ρ = 1,5 · exactamente 1 · 10
        q = colas.mmc(lam, 1.0, c)
        assert not q.estable and q.rho >= 1
        assert q.L is q.Lq is q.W is q.Wq is None


def test_sin_llegadas_no_hay_espera():
    q = colas.mmc(0, 2, 3)
    assert q.estable and (q.L, q.Lq, q.Wq) == (0, 0, 0) and q.W == pytest.approx(0.5)


# --- c mínimo (RF-53) ---------------------------------------------------------------------
def test_c_minimo_es_el_menor_que_cumple_el_umbral():
    lam, mu, umbral = 4.0, 1.0, 0.25
    c = colas.c_minimo(lam, mu, umbral)
    assert colas.mmc(lam, mu, c).Wq <= umbral
    assert c == int(lam / mu) + 1 or colas.mmc(lam, mu, c - 1).Wq > umbral  # y con uno menos no


def test_c_minimo_nunca_devuelve_un_sistema_inestable():
    assert colas.mmc(9, 1, colas.c_minimo(9, 1, wq_max=1e9)).estable


def test_c_minimo_none_si_el_umbral_es_inalcanzable():
    assert colas.c_minimo(10, 1, wq_max=0.0, c_max=15) is None  # siempre hay algo de espera


def test_c_minimo_entradas_invalidas():
    with pytest.raises(ValueError):
        colas.c_minimo(1, 1, wq_max=-1)
    with pytest.raises(ValueError):
        colas.c_minimo(1, 0, wq_max=1)


# --- Estimar μ ----------------------------------------------------------------------------
def test_estimar_mu_es_el_inverso_de_la_duracion_media():
    assert colas.estimar_mu([40, 50, 45]) == pytest.approx(1 / 45)


def test_estimar_mu_recupera_el_valor_de_la_simulacion():
    """Se simuló un servicio medio de 25 min (exponencial)."""
    p = sim.Parametros(fecha_inicio=date(2026, 1, 5), dias=300, servicio_medio_min=25, semilla=7)
    duraciones = [(s.fin - s.inicio).total_seconds() / 60 for s in sim.simular(p).solicitudes]
    assert 1 / colas.estimar_mu(duraciones) == pytest.approx(25, rel=0.05)


def test_estimar_mu_entradas_invalidas():
    with pytest.raises(ValueError):
        colas.estimar_mu([])
    with pytest.raises(ValueError):
        colas.estimar_mu([10, 0])


@pytest.mark.parametrize(("lam", "mu", "c"), [(-1, 1, 1), (1, 0, 1), (1, -2, 1), (1, 1, 0), (1, 1, 1.5)])
def test_parametros_invalidos(lam, mu, c):
    with pytest.raises(ValueError):
        colas.mmc(lam, mu, c)
