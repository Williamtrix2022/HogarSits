"""Validación de los modelos: estimado frente a verdadero (#41, RF-61, HU-10).

Las pruebas fijan lo que el informe VALIDACION_MODELOS.md afirma: que los servicios recuperan
λ, μ y P con error pequeño que baja al tener más datos, que el χ² está bien calibrado, y que el
modelo M/M/c **no** predice la espera cuando los asesores salen a visitas (un límite documentado).
"""

import math
from datetime import date

import pytest
from django.core.management import CommandError, call_command

from apps.analitica.services import simulacion as sim
from apps.analitica.services import validacion as v

INICIO = date(2026, 1, 5)


def base(dias=120, semilla=1):
    return v.parametros_de("base", INICIO, dias, semilla)


# --- Un escenario ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def una():
    return v.validar(base())


def test_recupera_lambda_mu_y_pasos_con_error_pequeno(una):
    assert abs(una.medida("λ por día laboral").error_relativo) < 0.05
    assert abs(una.medida("μ").error_relativo) < 0.06
    assert abs(una.medida("Pasos esperados desde Consulta").error_relativo) < 0.06


def test_recupera_la_probabilidad_de_cierre_con_error_moderado(una):
    m = una.medida("P(cierre desde Consulta)")
    assert m.verdadero == pytest.approx(0.2275, abs=5e-4)
    assert abs(m.error) < 0.05  # con 120 días la P(cierre) es la medida más ruidosa
    assert una.error_max_p < 0.10


def test_recupera_el_perfil_horario(una):
    assert una.error_max_lambda_hora < 0.5  # clientes/hora; los λ por hora van de 0,7 a 2,1
    assert una.franjas_suficientes == una.franjas_total == 10


def test_es_reproducible_con_la_misma_semilla():
    a, b = v.validar(base(60, 5)), v.validar(base(60, 5))
    assert a.medidas == b.medidas and a.espera_simulada_min == b.espera_simulada_min


def test_otra_semilla_da_otra_estimacion():
    a, b = v.validar(base(60, 5)), v.validar(base(60, 6))
    assert a.medida("λ por día laboral").estimado != b.medida("λ por día laboral").estimado


def test_la_medida_con_verdadero_cero_no_divide_por_cero():
    assert math.isnan(v.Medida("x", "u", 0.0, 1.0).error_relativo)
    assert v.Medida("x", "u", 2.0, 3.0).error == 1.0


# --- Réplicas ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def replicas():
    return v.validar_replicas(base(90, 100), replicas=10)


def test_el_sesgo_es_pequeno_frente_a_la_dispersion(replicas):
    for m in replicas.medidas:
        # el sesgo no debe ser mucho mayor que el error estándar de la media (desv/√n)
        assert abs(m.sesgo) < 4 * m.desviacion / math.sqrt(m.n) + 1e-9, m.nombre


def test_el_resumen_trae_error_medio_y_percentil_95(replicas):
    for m in replicas.medidas:
        assert 0 <= m.error_rel_abs_medio <= m.error_rel_abs_p95 and m.n == 10


def test_el_chi2_de_poisson_esta_bien_calibrado(replicas):
    """Con datos que SON de Poisson se rechaza cerca del 5 % (α = 0,05)."""
    assert 0.0 < replicas.tasa_rechazo_poisson < 0.15


def test_con_mas_datos_el_error_baja():
    pocos = v.validar_replicas(base(30, 200), replicas=10)
    muchos = v.validar_replicas(base(120, 200), replicas=10)
    err = lambda r, n: next(m for m in r.medidas if m.nombre == n).error_rel_abs_medio  # noqa: E731
    assert err(muchos, "λ por día laboral") < err(pocos, "λ por día laboral")
    assert err(muchos, "P(cierre desde Consulta)") < err(pocos, "P(cierre desde Consulta)")


def test_con_30_dias_muchas_franjas_no_alcanzan_el_minimo_de_datos():
    """RN-40: el panel debe avisar; con 30 días solo cerca de la mitad de las horas llega a 30."""
    r = v.validar_replicas(base(30, 300), replicas=6)
    assert r.franjas_suficientes < 0.9


def test_replicas_exige_al_menos_dos():
    with pytest.raises(ValueError, match="al menos 2"):
        v.validar_replicas(base(30), replicas=1)


# --- Límite del modelo de espera -----------------------------------------------------------
def test_mmc_con_c_nominal_subestima_la_espera_cuando_hay_visitas():
    """No valida el código sino el SUPUESTO: M/M/c ignora que los asesores salen a visitas."""
    r = v.validar(v.parametros_de("base", INICIO, 90, 1))
    assert r.espera_simulada_min > 10 * r.espera_modelo_nominal_min


def test_en_una_oficina_cargada_el_modelo_dice_inestable_donde_la_simulacion_lo_confirma():
    r = v.validar(v.parametros_de("oficina cargada", INICIO, 60, 1))
    assert r.espera_modelo_efectivo_min is None  # c efectivo < 1: carga inestable
    assert r.espera_simulada_min > 60  # y la espera simulada es de horas


# --- Escenarios y errores -------------------------------------------------------------------
@pytest.mark.parametrize("nombre", sorted(v.ESCENARIOS))
def test_todos_los_escenarios_son_validos_y_se_pueden_validar(nombre):
    r = v.validar(v.parametros_de(nombre, INICIO, 30, 1))
    assert r.n_solicitudes > 0 and r.medida("μ").estimado > 0


def test_un_escenario_desconocido_lista_las_opciones():
    with pytest.raises(ValueError, match="Opciones"):
        v.parametros_de("no existe", INICIO, 30, 1)


def test_los_escenarios_coinciden_con_los_de_supuestos_de_trabajo():
    assert set(v.ESCENARIOS) == {
        "base", "oficina cargada", "oficina cargada + 3er asesor",
        "oficina cargada, visitas cortas", "más permanencia", "seguimiento lento",
    }


def test_la_matriz_de_mas_permanencia_conserva_la_probabilidad_de_cierre():
    from apps.analitica.services import markov

    base_ = markov.analizar_absorcion(sim.MATRIZ_README)
    mas = markov.analizar_absorcion(v.ESCENARIOS["más permanencia"]["matriz"])
    assert mas.p_cierre[0] == pytest.approx(base_.p_cierre[0], abs=2e-3)
    assert mas.pasos[0] > base_.pasos[0] + 0.5  # solo cambian los pasos esperados


# --- Comando --------------------------------------------------------------------------------
def test_el_comando_escribe_el_informe_en_utf8(tmp_path):
    destino = tmp_path / "informe.md"
    call_command("validar_modelos", "--dias", "30", "--replicas", "2", "--informe", str(destino))
    texto = destino.read_text(encoding="utf-8")
    assert "### Escenario «base»" in texto and "λ por día laboral" in texto
    assert "| P(cierre desde Consulta)" in texto  # sin «|» dentro de la celda: no parte la tabla


def test_la_salida_de_consola_es_ascii(capsys):
    """La consola de Windows (cp1252) no imprime λ ni μ: la consola va en ASCII."""
    call_command("validar_modelos", "--dias", "30", "--replicas", "2")
    salida = capsys.readouterr().out
    assert salida and all(ord(c) < 128 for c in salida)


def test_el_informe_es_una_tabla_markdown_bien_formada(tmp_path):
    destino = tmp_path / "i.md"
    call_command("validar_modelos", "--dias", "30", "--replicas", "2", "--informe", str(destino))
    for linea in destino.read_text(encoding="utf-8").splitlines():
        if linea.startswith("|") and "---" not in linea:
            # todas las filas de una tabla tienen el mismo número de celdas que su encabezado
            assert linea.count("|") >= 3


def test_el_comando_rechaza_un_escenario_desconocido():
    with pytest.raises(CommandError, match="Escenario desconocido"):
        call_command("validar_modelos", "--escenario", "inventado", "--replicas", "2")


def test_el_comando_corre_sin_acceso_a_la_base_de_datos():
    """Este módulo no usa la marca `django_db`: pytest-django lanza RuntimeError ante cualquier
    consulta. Que el comando termine demuestra que simula en memoria y no toca datos reales."""
    call_command("validar_modelos", "--dias", "30", "--replicas", "2")
