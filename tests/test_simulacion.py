"""La simulación debe recuperar los parámetros con los que se generó (RF-60, HU-10)."""

from collections import Counter
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest

from apps.analitica.services import simulacion as sim

LARGA = sim.Parametros(fecha_inicio=date(2026, 1, 5), dias=300, clientes_por_dia=12, semilla=7)


@pytest.fixture(scope="module")
def corrida():
    return sim.simular(LARGA)


def test_es_reproducible_con_la_misma_semilla():
    p = sim.Parametros(fecha_inicio=date(2026, 1, 5), dias=20, semilla=3)
    a, b = sim.simular(p), sim.simular(p)
    assert [s.llegada for s in a.solicitudes] == [s.llegada for s in b.solicitudes]
    assert [s.etapa_actual for s in a.solicitudes] == [s.etapa_actual for s in b.solicitudes]


def test_semillas_distintas_dan_resultados_distintos():
    base = dict(fecha_inicio=date(2026, 1, 5), dias=20)
    a = sim.simular(sim.Parametros(semilla=1, **base))
    b = sim.simular(sim.Parametros(semilla=2, **base))
    assert [s.llegada for s in a.solicitudes] != [s.llegada for s in b.solicitudes]


def test_recupera_lambda_diario(corrida):
    laborales = sum(
        1
        for d in range(LARGA.dias)
        if (LARGA.fecha_inicio + timedelta(days=d)).weekday() in LARGA.dias_laborales
    )
    lam = len(corrida.solicitudes) / laborales
    assert lam == pytest.approx(12, rel=0.05)


def test_llegadas_tienen_picos_de_manana_y_tarde(corrida):
    por_hora = Counter(s.llegada.hour for s in corrida.solicitudes)
    mediodia = por_hora[12] + por_hora[13]
    assert por_hora[10] > 1.4 * por_hora[12]
    assert por_hora[16] > 1.4 * por_hora[13]
    assert por_hora[10] + por_hora[16] > 2 * mediodia


def test_ninguna_llegada_fuera_de_horario_ni_en_domingo(corrida):
    assert all(8 <= s.llegada.hour < 18 for s in corrida.solicitudes)
    assert all(s.llegada.weekday() != 6 for s in corrida.solicitudes)


def test_recupera_el_tiempo_medio_de_servicio(corrida):
    servicio = [(s.fin - s.inicio).total_seconds() / 60 for s in corrida.solicitudes]
    assert np.mean(servicio) == pytest.approx(25, rel=0.05)


def test_la_espera_nunca_es_negativa_y_la_hay(corrida):
    esperas = [(s.inicio - s.llegada).total_seconds() for s in corrida.solicitudes]
    assert min(esperas) >= 0
    assert max(esperas) > 0  # con picos y visitas ocupando asesores, a veces hay cola


def test_un_asesor_no_atiende_dos_clientes_a_la_vez(corrida):
    for a in range(LARGA.n_asesores):
        tramos = sorted((s.inicio, s.fin) for s in corrida.solicitudes if s.asesor == a)
        assert all(prev[1] <= sig[0] for prev, sig in zip(tramos, tramos[1:], strict=False))


def test_visitas_sin_cruces_por_asesor_ni_inmueble_y_en_horario(corrida):
    visitas = [v for s in corrida.solicitudes for v in s.visitas]
    assert len(visitas) > 100
    for clave in ("asesor", "inmueble"):
        grupos = {}
        for v in visitas:
            grupos.setdefault(getattr(v, clave), []).append((v.inicio, v.fin))
        for tramos in grupos.values():
            tramos.sort()
            assert all(a[1] <= b[0] for a, b in zip(tramos, tramos[1:], strict=False))
    assert all(v.inicio.date() == v.fin.date() and 8 <= v.inicio.hour for v in visitas)
    assert all(30 <= (v.fin - v.inicio).total_seconds() / 60 <= 120 for v in visitas)


def test_una_visita_ocupa_al_asesor_y_no_se_le_asignan_consultas_encima(corrida):
    visitas = [(v.asesor, v.inicio, v.fin) for s in corrida.solicitudes for v in s.visitas]
    consultas = [(s.asesor, s.inicio, s.fin) for s in corrida.solicitudes]
    for asesor, ini, fin in visitas[:300]:
        assert all(
            c_fin <= ini or c_ini >= fin
            for a, c_ini, c_fin in consultas
            if a == asesor
        )


def test_transiciones_validas(corrida):
    for s in corrida.solicitudes:
        for e in s.etapas:
            assert e.origen in (1, 2, 3)  # no se sale de Cierre ni Abandono
            assert sim.MATRIZ_README[e.origen - 1][e.destino - 1] > 0
            assert e.fecha > s.fin
        fechas = [e.fecha for e in s.etapas]
        assert fechas == sorted(fechas)


def test_recupera_la_probabilidad_de_cierre_de_la_propuesta(corrida):
    """P(cierre | Consulta) = 22,8 % y 2,4 pasos hasta absorción (Propuesta §5.3)."""
    # Se excluyen las solicitudes cercanas al fin del periodo (trayectorias truncadas).
    corte = datetime(2026, 8, 1, tzinfo=UTC)
    completas = [s for s in corrida.solicitudes if s.llegada < corte]
    cierres = sum(1 for s in completas if s.etapa_actual == sim.CIERRE)
    assert cierres / len(completas) == pytest.approx(0.2275, abs=0.025)
    pasos = np.mean([len(s.etapas) for s in completas])
    assert pasos == pytest.approx(2.40, abs=0.15)


def test_matriz_estimada_se_parece_a_la_real(corrida):
    conteos = np.zeros((5, 5))
    for s in corrida.solicitudes:
        for e in s.etapas:
            conteos[e.origen - 1, e.destino - 1] += 1
    filas = conteos[:3]
    estimada = filas / filas.sum(axis=1, keepdims=True)
    real = np.array(sim.MATRIZ_README)[:3]
    assert np.abs(estimada - real).max() < 0.03


def test_parametros_invalidos_se_rechazan():
    base = dict(fecha_inicio=date(2026, 1, 5))
    malas = {
        "matriz que no suma 1": dict(matriz=((0.5, 0.5, 0, 0, 0.1),) + sim.MATRIZ_README[1:]),
        "estado absorbente roto": dict(
            matriz=sim.MATRIZ_README[:3] + ((0, 0, 0, 0.5, 0.5),) + sim.MATRIZ_README[4:]
        ),
        "sin asesores": dict(n_asesores=0),
        "cierre antes de apertura": dict(hora_apertura=18, hora_cierre=8),
        "visita no cabe": dict(hora_apertura=8, hora_cierre=9),
    }
    for nombre, extra in malas.items():
        with pytest.raises(ValueError):
            sim.simular(sim.Parametros(**base, **extra))
            pytest.fail(f"se aceptó: {nombre}")


def test_el_modulo_no_depende_de_django():
    with open(sim.__file__, encoding="utf-8") as f:
        lineas = [ln.strip() for ln in f]
    assert not [ln for ln in lineas if ln.startswith(("import django", "from django"))]
