"""λ por franja y ajuste de Poisson (#35, HU-07, RF-50, RN-40, RN-42). Python puro, sin BD."""

import math
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from apps.analitica.services import poisson as po
from apps.analitica.services import simulacion as sim

BOGOTA = ZoneInfo("America/Bogota")
LARGA = sim.Parametros(fecha_inicio=date(2026, 1, 5), dias=300, clientes_por_dia=12, semilla=7)


@pytest.fixture(scope="module")
def corrida():
    return sim.simular(LARGA)


@pytest.fixture(scope="module")
def conteos(corrida):
    llegadas = [s.llegada for s in corrida.solicitudes]
    return po.conteos_por_hora(llegadas, LARGA.fecha_inicio, LARGA.fecha_inicio + timedelta(days=299))


# --- Distribución -------------------------------------------------------------------------
@pytest.mark.parametrize("k", range(0, 8))
def test_pmf_coincide_con_la_formula(k):
    lam = 2.5
    assert po.poisson_pmf(k, lam) == pytest.approx(math.exp(-lam) * lam**k / math.factorial(k))


def test_pmf_suma_uno_y_la_media_es_lambda():
    lam = 3.7
    probs = [po.poisson_pmf(k, lam) for k in range(0, 80)]
    assert sum(probs) == pytest.approx(1.0)
    assert sum(k * p for k, p in enumerate(probs)) == pytest.approx(lam)


def test_pmf_casos_borde():
    assert po.poisson_pmf(-1, 2.0) == 0.0
    assert po.poisson_pmf(0, 0.0) == 1.0 and po.poisson_pmf(3, 0.0) == 0.0
    assert po.poisson_pmf(500, 400.0) > 0  # no desborda con valores grandes
    with pytest.raises(ValueError):
        po.poisson_pmf(1, -0.1)


# --- Conteos y λ por franja ---------------------------------------------------------------
def llegada(dia, hora, minuto=0):
    return datetime(dia.year, dia.month, dia.day, hora, minuto, tzinfo=BOGOTA)


def test_las_horas_sin_llegadas_cuentan_como_cero():
    lunes = date(2026, 3, 2)
    c = po.conteos_por_hora([llegada(lunes, 9), llegada(lunes, 9, 30)], lunes, lunes, 8, 12)
    assert c == {(lunes, 8): 0, (lunes, 9): 2, (lunes, 10): 0, (lunes, 11): 0}


def test_solo_cuenta_dias_laborales_y_horas_de_atencion():
    lunes, domingo = date(2026, 3, 2), date(2026, 3, 8)
    llegadas = [llegada(domingo, 10), llegada(lunes, 7), llegada(lunes, 18), llegada(lunes, 10)]
    c = po.conteos_por_hora(llegadas, lunes, domingo, 8, 18)
    assert sum(c.values()) == 1  # domingo, antes de abrir y a las 18:00 quedan fuera
    assert not any(d == domingo for d, _ in c)


def test_la_hora_es_la_de_bogota_no_la_utc():
    """RN-42: 14:30 UTC son las 09:30 en Bogotá."""
    lunes = date(2026, 3, 2)
    utc = datetime(2026, 3, 2, 14, 30, tzinfo=UTC)
    c = po.conteos_por_hora([utc], lunes, lunes, 8, 18)
    assert c[(lunes, 9)] == 1 and c[(lunes, 14)] == 0  # no se cuenta como las 14:00


def test_una_llegada_cerca_de_medianoche_utc_cae_en_el_dia_local_correcto():
    lunes = date(2026, 3, 2)
    utc = datetime(2026, 3, 3, 2, 0, tzinfo=UTC)  # 21:00 del lunes en Bogotá
    c = po.conteos_por_hora([utc], lunes, date(2026, 3, 3), 0, 24)
    assert c[(lunes, 21)] == 1 and c[(date(2026, 3, 3), 2)] == 0


def test_rechaza_entradas_invalidas():
    d = date(2026, 3, 2)
    with pytest.raises(ValueError, match="zona horaria"):
        po.conteos_por_hora([datetime(2026, 3, 2, 9, 0)], d, d)
    with pytest.raises(ValueError):
        po.conteos_por_hora([], date(2026, 3, 3), d)
    with pytest.raises(ValueError):
        po.conteos_por_hora([], d, d, apertura=18, cierre=8)


def test_lambda_es_la_media_de_llegadas_por_observacion():
    lunes, martes = date(2026, 3, 2), date(2026, 3, 3)
    llegadas = [llegada(lunes, 9)] * 3 + [llegada(martes, 9)]  # 3 el lunes y 1 el martes
    c = po.conteos_por_hora(llegadas, lunes, martes, 9, 10)
    (f,) = po.lambda_por_franja(c)
    assert (f.hora, f.dias_observados, f.llegadas, f.lam) == (9, 2, 4, 2.0)


def test_lambda_por_dia_de_la_semana_separa_los_dias():
    lunes, martes = date(2026, 3, 2), date(2026, 3, 3)
    c = po.conteos_por_hora([llegada(lunes, 9)] * 3, lunes, martes, 9, 10)
    por_dia = {(f.dia_semana, f.hora): f.lam for f in po.lambda_por_franja(c, por_dia_semana=True)}
    assert por_dia == {(0, 9): 3.0, (1, 9): 0.0}


def test_la_franja_con_pocas_llegadas_se_marca_no_suficiente():
    lunes = date(2026, 3, 2)
    c = po.conteos_por_hora([llegada(lunes, 9)] * 29, lunes, lunes, 9, 10)
    assert po.lambda_por_franja(c)[0].suficiente is False  # RN-40: 29 < 30
    c = po.conteos_por_hora([llegada(lunes, 9)] * 30, lunes, lunes, 9, 10)
    assert po.lambda_por_franja(c)[0].suficiente is True


# --- Recuperar los parámetros de la simulación --------------------------------------------
def test_recupera_las_llegadas_por_dia_laboral(conteos):
    """Se simularon 12 clientes por día laboral (lunes a sábado)."""
    dias = {d for d, _ in conteos}
    total = sum(conteos.values())
    assert total / len(dias) == pytest.approx(12, rel=0.05)


def test_recupera_lambda_por_hora_y_los_picos(conteos):
    por_hora = {f.hora: f.lam for f in po.lambda_por_franja(conteos)}
    pesos = sim.perfil_horario_por_defecto(8, 18)
    for hora, peso in zip(range(8, 18), pesos, strict=True):
        assert por_hora[hora] == pytest.approx(12 * peso, rel=0.2), hora
    # picos de mañana y tarde por encima del valle del mediodía
    assert por_hora[10] > por_hora[13] and por_hora[16] > por_hora[13]


def test_todas_las_franjas_de_una_corrida_larga_son_suficientes(conteos):
    assert all(f.suficiente for f in po.lambda_por_franja(conteos))


# --- Ajuste de Poisson --------------------------------------------------------------------
def test_una_franja_con_llegadas_de_poisson_no_se_rechaza(conteos):
    """Dentro de una misma hora el proceso es de Poisson: el χ² no debe rechazarlo."""
    horas_pico = [n for (d, h), n in conteos.items() if h == 10]
    ajuste = po.ajuste_poisson(horas_pico)
    assert ajuste.rechaza is False and ajuste.p_valor > 0.05
    assert ajuste.lam == pytest.approx(sum(horas_pico) / len(horas_pico))
    assert ajuste.indice_dispersion == pytest.approx(1.0, abs=0.25)


def test_mezclar_horas_da_la_dispersion_teorica_de_un_poisson_mixto(conteos):
    """Mezclar horas con λ distinta da var/media = 1 + Var(λ)/E(λ): un poco más de 1.

    Con el perfil suave por defecto la diferencia es pequeña y el χ² no la detecta; lo que sí
    debe cumplirse es que el índice observado coincida con el teórico.
    """
    lams = [12 * w for w in sim.perfil_horario_por_defecto(8, 18)]
    media = sum(lams) / len(lams)
    var = sum((x - media) ** 2 for x in lams) / len(lams)
    teorico = 1 + var / media
    observado = po.ajuste_poisson(list(conteos.values())).indice_dispersion
    assert teorico > 1.0
    assert observado == pytest.approx(teorico, abs=0.05)


def test_picos_marcados_hacen_que_mezclar_las_horas_se_rechace():
    """Con picos fuertes el proceso claramente no es homogéneo: el ajuste global falla."""
    perfil = (0.02, 0.30, 0.03, 0.03, 0.03, 0.03, 0.02, 0.30, 0.20, 0.04)  # suma 1
    p = sim.Parametros(
        fecha_inicio=date(2026, 1, 5), dias=300, clientes_por_dia=12, semilla=11,
        perfil_horario=perfil,
    )
    llegadas = [s.llegada for s in sim.simular(p).solicitudes]
    c = po.conteos_por_hora(llegadas, p.fecha_inicio, p.fecha_inicio + timedelta(days=299))
    ajuste = po.ajuste_poisson(list(c.values()))
    assert ajuste.rechaza is True and ajuste.indice_dispersion > 1.5
    # y por franja, en cambio, cada hora sí es Poisson
    pico = po.ajuste_poisson([n for (_, h), n in c.items() if h == 9])
    assert pico.rechaza is False


def test_llegadas_a_rafagas_se_rechazan():
    rafagas = [0, 0, 0, 0, 0, 0, 12, 0, 0, 0] * 20  # misma media (1,2) pero agrupadas
    ajuste = po.ajuste_poisson(rafagas)
    assert ajuste.rechaza is True and ajuste.indice_dispersion > 5


def test_frecuencias_observada_y_esperada_suman_uno(conteos):
    a = po.ajuste_poisson([n for (_, h), n in conteos.items() if h == 16])
    assert sum(a.observada) == pytest.approx(1.0) and sum(a.esperada) == pytest.approx(1.0)
    assert len(a.ks) == len(a.observada) == len(a.esperada)


def test_chi2_calculado_a_mano_con_clases_agrupadas():
    """Conteos 0×6, 1×3, 2×1 (n=10, λ=0,5). Con esperado mínimo 0 no se agrupa nada."""
    datos = [0] * 6 + [1] * 3 + [2]
    a = po.ajuste_poisson(datos, minimo_esperado=0.0)
    esperados = [10 * math.exp(-0.5) * 0.5**k / math.factorial(k) for k in range(2)]
    esperados.append(10 - sum(esperados))  # la última clase es «2 o más»
    observados = [6, 3, 1]
    manual = sum((o - e) ** 2 / e for o, e in zip(observados, esperados, strict=True))
    assert a.chi2 == pytest.approx(manual) and a.grados_libertad == 1


def test_con_pocos_datos_no_hay_prueba_pero_si_lambda():
    a = po.ajuste_poisson([1, 2, 1])
    assert a.lam == pytest.approx(4 / 3)
    assert a.chi2 is None and a.p_valor is None and a.rechaza is None


def test_todo_ceros_no_rompe():
    a = po.ajuste_poisson([0, 0, 0, 0])
    assert a.lam == 0 and a.indice_dispersion == 0 and a.rechaza is None


def test_entradas_invalidas():
    with pytest.raises(ValueError):
        po.ajuste_poisson([])
    with pytest.raises(ValueError):
        po.ajuste_poisson([1, -1])
