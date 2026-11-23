"""Matriz P, N = (I−Q)⁻¹ y absorción (#37, HU-09, RF-54, RF-55, RN-31, RN-40, RN-43, ADR-002)."""

from datetime import date

import numpy as np
import pytest

from apps.analitica.services import markov as mk
from apps.analitica.services import simulacion as sim

README = sim.MATRIZ_README  # la del README y la Propuesta


def pares_de(matriz, n_por_fila, semilla=1):
    """Genera transiciones de una cadena conocida, para comprobar que se recupera la matriz."""
    rng = np.random.default_rng(semilla)
    pares = []
    for origen in (1, 2, 3):
        destinos = rng.choice(5, size=n_por_fila, p=matriz[origen - 1])
        pares += [(origen, int(d) + 1) for d in destinos]
    return pares


# --- Ejemplo de la Propuesta / README -----------------------------------------------------
def test_probabilidad_de_cierre_y_pasos_de_la_propuesta():
    a = mk.analizar_absorcion(README)
    # Forma cerrada: Consulta→Visita→Negociación→Cierre, con la espera en cada etapa descontada.
    exacto = (0.50 / 0.80) * (0.45 / 0.85) * (0.55 / 0.80)
    assert a.p_cierre[0] == pytest.approx(exacto, rel=1e-12)
    assert a.p_cierre[0] == pytest.approx(0.2275, abs=5e-4)  # «≈ 22,75 %» de la Propuesta
    t3 = 1 / 0.80  # pasos desde Negociación
    t2 = (1 + 0.45 * t3) / 0.85  # desde Visita
    t1 = (1 + 0.50 * t2) / 0.80  # desde Consulta
    assert a.pasos[0] == pytest.approx(t1, rel=1e-12)
    assert a.pasos[0] == pytest.approx(2.4, abs=0.01)  # «≈ 2,4 pasos» (exacto: 2,3989)


def test_el_valor_exacto_es_22_748_por_ciento_no_22_8():
    """La Propuesta dice «≈ 22,8 %»: sale de redondear 22,748 → 22,75 → 22,8 (doble redondeo)."""
    p = mk.analizar_absorcion(README).p_cierre[0] * 100
    assert round(p, 3) == 22.748 and round(p, 2) == 22.75 and round(p, 1) == 22.7


def test_probabilidades_de_las_otras_etapas_del_wireframe_w12():
    a = mk.analizar_absorcion(README)
    assert round(a.p_cierre[1] * 100) == 36  # Visita → cierre: 36 %
    assert round(a.p_cierre[2] * 100) == 69  # Negociación → cierre: 69 %
    assert round(a.p_cierre[0] * 100) == 23  # Consulta → cierre: 23 %


def test_la_matriz_fundamental_coincide_con_el_calculo_a_mano():
    a = mk.analizar_absorcion(README)
    assert a.N[0][0] == pytest.approx(1 / 0.8)  # 1/(1 − 0,20)
    assert a.N[1][1] == pytest.approx(1 / 0.85)
    assert a.N[2][2] == pytest.approx(1 / 0.8)
    assert a.N[0][1] == pytest.approx(0.5 / (0.8 * 0.85))  # visitas a Visita desde Consulta
    assert a.N[0][2] == pytest.approx(0.5 * 0.45 / (0.8 * 0.85 * 0.8))
    assert a.N[1][0] == 0 and a.N[2][0] == 0 and a.N[2][1] == 0  # no se retrocede


def test_cierre_y_abandono_suman_uno_desde_cada_etapa():
    a = mk.analizar_absorcion(README)
    for i in range(3):
        assert a.p_cierre[i] + a.p_abandono[i] == pytest.approx(1.0)


def test_coincide_con_la_potencia_de_la_matriz():
    """Comprobación independiente: P^k converge a la absorción sin invertir ninguna matriz."""
    limite = np.linalg.matrix_power(np.array(README), 500)
    a = mk.analizar_absorcion(README)
    for i in range(3):
        assert limite[i, 3] == pytest.approx(a.p_cierre[i], abs=1e-9)
        assert limite[i, 4] == pytest.approx(a.p_abandono[i], abs=1e-9)


def test_los_pasos_coinciden_con_la_suma_de_visitas_esperadas():
    """Pasos esperados = Σ_k P(seguir en transitorio tras k pasos), calculado por potencias."""
    Q = np.array(README)[:3, :3]
    esperado = sum(np.linalg.matrix_power(Q, k).sum(axis=1) for k in range(0, 400))
    assert mk.analizar_absorcion(README).pasos == pytest.approx(tuple(esperado))


def test_desde_devuelve_los_valores_de_una_etapa():
    d = mk.analizar_absorcion(README).desde(mk.CONSULTA)
    assert d["p_cierre"] == pytest.approx(0.2275, abs=5e-4)
    assert d["pasos"] == pytest.approx(2.4, abs=0.01)


# --- Estimar P desde las transiciones (RF-54) ---------------------------------------------
def test_estima_frecuencias_relativas():
    e = mk.estimar_matriz([(1, 1), (1, 1), (1, 2), (1, 5)])
    assert e.matriz[0] == pytest.approx((0.5, 0.25, 0, 0, 0.25))
    assert e.n_por_origen[0] == 4


def test_la_autotransicion_se_cuenta_en_la_diagonal():
    """ADR-002: seguir en la misma etapa es un paso y entra en la estimación."""
    e = mk.estimar_matriz([(2, 2)] * 3 + [(2, 3)])
    assert e.matriz[1][1] == pytest.approx(0.75)


def test_cierre_y_abandono_son_absorbentes_por_definicion():
    e = mk.estimar_matriz([(1, 2)])
    assert e.matriz[3] == (0, 0, 0, 1, 0) and e.matriz[4] == (0, 0, 0, 0, 1)


def test_recupera_la_matriz_de_la_simulacion():
    """Mismos datos que generaría el sistema: se debe recuperar P (±0,03)."""
    p = sim.Parametros(fecha_inicio=date(2026, 1, 5), dias=300, clientes_por_dia=12, semilla=7)
    pares = [(e.origen, e.destino) for s in sim.simular(p).solicitudes for e in s.etapas]
    e = mk.estimar_matriz(pares)
    assert e.suficiente
    for i in range(3):
        assert e.matriz[i] == pytest.approx(README[i], abs=0.03)
    assert mk.analizar(pares).absorcion.p_cierre[0] == pytest.approx(0.2275, abs=0.03)


def test_recupera_otra_matriz_distinta():
    otra = (
        (0.5, 0.3, 0, 0, 0.2),
        (0, 0.4, 0.4, 0, 0.2),
        (0, 0, 0.3, 0.6, 0.1),
        (0, 0, 0, 1, 0),
        (0, 0, 0, 0, 1),
    )
    e = mk.estimar_matriz(pares_de(otra, 4000))
    for i in range(3):
        assert e.matriz[i] == pytest.approx(otra[i], abs=0.03)


# --- RN-43: no se inventan filas ----------------------------------------------------------
def test_una_etapa_sin_observaciones_no_se_inventa():
    e = mk.estimar_matriz([(1, 2)] * 5)
    assert e.matriz[1] is None and e.matriz[2] is None
    assert e.faltan == (2, 3) and not e.completa


def test_sin_filas_completas_no_hay_absorcion():
    r = mk.analizar([(1, 2)] * 40)
    assert r.absorcion is None and r.estimacion.faltan == (2, 3)


def test_analizar_absorcion_rechaza_una_fila_faltante():
    e = mk.estimar_matriz([(1, 2)] * 5)
    with pytest.raises(ValueError, match="Falta la fila de Visita"):
        mk.analizar_absorcion(e.matriz)


def test_las_filas_estimadas_suman_uno():
    e = mk.estimar_matriz(pares_de(README, 500))
    for fila in e.matriz[:3]:
        assert sum(fila) == pytest.approx(1.0)


def test_una_etapa_que_solo_se_repite_no_tiene_absorcion():
    pares = [(1, 1)] * 40 + [(2, 3)] * 40 + [(3, 4)] * 40  # Consulta nunca sale
    r = mk.analizar(pares)
    assert r.estimacion.completa and r.absorcion is None


# --- RN-40: evidencia mínima --------------------------------------------------------------
def test_marca_las_etapas_con_pocas_transiciones():
    pares = [(1, 2)] * 30 + [(2, 3)] * 29 + [(3, 4)] * 5
    e = mk.estimar_matriz(pares)
    assert e.pocas == (2, 3) and not e.suficiente  # 29 y 5 < 30; la de 30 sí alcanza


def test_el_minimo_es_configurable():
    pares = [(1, 2)] * 5 + [(2, 3)] * 5 + [(3, 4)] * 5
    assert mk.estimar_matriz(pares, minimo=5).suficiente
    assert not mk.estimar_matriz(pares, minimo=6).suficiente


# --- Validación (RN-31, RN-43) ------------------------------------------------------------
def test_rechaza_transiciones_que_salen_de_un_estado_absorbente():
    with pytest.raises(ValueError, match="absorbente"):
        mk.contar_transiciones([(4, 1)])


def test_rechaza_etapas_invalidas():
    for par in [(0, 1), (1, 6), (7, 2)]:
        with pytest.raises(ValueError, match="inválida"):
            mk.contar_transiciones([par])


def test_validar_matriz_detecta_filas_que_no_suman_uno():
    mala = [list(f) for f in README]
    mala[0][0] = 0.5
    with pytest.raises(ValueError, match="suma"):
        mk.validar_matriz(mala)


def test_validar_matriz_detecta_negativos_y_forma_incorrecta():
    negativa = [list(f) for f in README]
    negativa[0][0], negativa[0][1] = -0.1, 0.8
    with pytest.raises(ValueError, match="negativas"):
        mk.validar_matriz(negativa)
    with pytest.raises(ValueError, match="5x5"):
        mk.validar_matriz(README[:4])


def test_validar_matriz_exige_estados_absorbentes():
    mala = [list(f) for f in README]
    mala[3] = [0, 0, 0, 0.5, 0.5]
    with pytest.raises(ValueError, match="absorbentes"):
        mk.validar_matriz(mala)


def test_sin_transiciones_no_hay_nada_que_estimar():
    e = mk.estimar_matriz([])
    assert e.faltan == (1, 2, 3) and mk.analizar([]).absorcion is None
