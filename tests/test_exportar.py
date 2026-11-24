"""Exportar resultados a CSV (#40, RF-58)."""

import csv
import io
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import HttpResponse
from django.urls import reverse

from apps.analitica import analisis, exportar
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client):
    u = User.objects.create_user("jefe", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ADMIN)
    client.force_login(u)
    return client


@pytest.fixture
def simulados(db):
    call_command("seed_datos_simulados", "--dias", "60", "--semilla", "7", "--asesores", "3")


def leer(respuesta):
    """Filas del CSV como las lee Excel en español: separador `;`, UTF-8 con BOM."""
    texto = respuesta.content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(texto), delimiter=";"))


# --- Celdas: formato y seguridad (sin BD) -------------------------------------------------
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(None, ""), (True, "sí"), (False, "no"), (7, "7"), (2.5, "2,5"), (0.2275, "0,2275"),
     (2.0, "2"), (1.23456789, "1,234568"), (0.000012, "0,000012"), (-0.0, "0"),
     (-1.5, "-1,5"), ("Consulta", "Consulta")],
)
def test_formato_de_las_celdas(valor, esperado):
    assert exportar.celda(valor) == esperado


@pytest.mark.parametrize("peligroso", ["=SUMA(A1:A9)", "+cmd|' /C calc'!A0", "-2+3", "@SUMA(1)", "\tx", "\rx"])
def test_el_texto_que_parece_formula_se_neutraliza(peligroso):
    """Inyección de CSV: Excel ejecutaría estas celdas como fórmulas."""
    assert exportar.celda(peligroso).startswith("'")


def test_los_numeros_negativos_no_se_confunden_con_formulas():
    assert exportar.celda(-3) == "-3" and exportar.celda(-1.5) == "-1,5"  # son números, no texto


def test_el_csv_usa_punto_y_coma_bom_y_crlf():
    r = HttpResponse()
    exportar.escribir(r, ["a", "b"], [[1, 2.5], ["x;y", None]])
    assert r.content.startswith("﻿".encode())
    assert r.content.decode("utf-8-sig") == 'a;b\r\n1;2,5\r\n"x;y";\r\n'


def test_las_tildes_sobreviven():
    r = HttpResponse()
    exportar.escribir(r, ["probabilidad_negociación"], [["Abandono"]])
    assert "negociación" in r.content.decode("utf-8-sig")


def test_nombre_de_archivo_lleva_la_tabla_y_el_periodo():
    from datetime import date

    assert exportar.nombre_de_archivo("colas", date(2026, 3, 1), date(2026, 3, 31)) == (
        "hogarsits_colas_2026-03-01_2026-03-31.csv"
    )


# --- Descarga -----------------------------------------------------------------------------
def test_requiere_ser_administrador(client):
    r = client.get(reverse("analitica:exportar"), {"tabla": "lambda"})
    assert r.status_code == 302 and "ingresar" in r["Location"]
    u = User.objects.create_user("asesor9", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    client.force_login(u)
    assert client.get(reverse("analitica:exportar"), {"tabla": "lambda"}).status_code == 403


@pytest.mark.parametrize("tabla", sorted(exportar.TABLAS))
def test_cada_tabla_se_descarga_como_csv(admin_client, simulados, tabla):
    r = admin_client.get(reverse("analitica:exportar"), {"tabla": tabla})
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
    assert r["Content-Disposition"].startswith('attachment; filename="hogarsits_' + tabla)
    filas = leer(r)
    assert len(filas) >= 2  # encabezado y al menos una fila
    assert all(len(f) == len(filas[0]) for f in filas)  # rectangular: Excel no se desordena


def test_el_archivo_trae_la_advertencia_de_datos_simulados(admin_client, simulados):
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "matriz"}))
    assert filas[0][-1] == "datos_simulados"
    assert {f[-1] for f in filas[1:]} == {"sí"}


def test_la_tabla_lambda_coincide_con_el_analisis(admin_client, simulados):
    desde, hasta = analisis.rango_por_defecto()
    r = analisis.analizar_periodo(desde, hasta)
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "lambda"}))[1:]
    assert len(filas) == len(r.franjas)
    for fila, franja in zip(filas, r.franjas, strict=True):
        assert fila[0] == f"{franja.hora:02d}:00"
        assert float(fila[3].replace(",", ".")) == pytest.approx(franja.lam, abs=1e-6)


def test_la_matriz_exportada_suma_uno_por_fila_y_los_absorbentes_son_identidad(
    admin_client, simulados
):
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "matriz"}))[1:]
    for fila in filas:
        probs = [float(x.replace(",", ".")) for x in fila[1:6]]
        assert sum(probs) == pytest.approx(1.0, abs=1e-5)
    assert [f[1:6] for f in filas[3:]] == [["0", "0", "0", "1", "0"], ["0", "0", "0", "0", "1"]]


def test_la_absorcion_exportada_coincide_con_el_panel(admin_client, simulados):
    desde, hasta = analisis.rango_por_defecto()
    absorcion = analisis.analizar_periodo(desde, hasta).markov.absorcion
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "absorcion"}))[1:]
    assert float(filas[0][1].replace(",", ".")) == pytest.approx(absorcion.p_cierre[0] * 100, abs=1e-4)
    assert float(filas[0][3].replace(",", ".")) == pytest.approx(absorcion.pasos[0], abs=1e-5)


def test_una_cola_inestable_exporta_celdas_vacias_no_numeros(admin_client, simulados):
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "colas"}))
    enc = filas[0]
    inestables = [f for f in filas[1:] if f[enc.index("estable")] == "no"]
    for f in inestables:
        assert f[enc.index("Wq_min")] == "" and f[enc.index("W_min")] == ""


def test_respeta_el_filtro_de_fechas(admin_client, simulados):
    desde, hasta = analisis.rango_por_defecto(60)
    todo = leer(admin_client.get(reverse("analitica:exportar"), {
        "tabla": "lambda", "desde": desde.isoformat(), "hasta": hasta.isoformat(), "espera_max": 20}))
    una_semana = leer(admin_client.get(reverse("analitica:exportar"), {
        "tabla": "lambda", "desde": desde.isoformat(),
        "hasta": (desde + timedelta(days=6)).isoformat(), "espera_max": 20}))
    suma = lambda filas: sum(int(f[2]) for f in filas[1:])  # noqa: E731  (columna «llegadas»)
    assert suma(una_semana) < suma(todo)


def test_el_nombre_del_archivo_refleja_el_periodo(admin_client, simulados):
    r = admin_client.get(reverse("analitica:exportar"), {
        "tabla": "lambda", "desde": "2026-10-01", "hasta": "2026-10-31", "espera_max": 20})
    assert "hogarsits_lambda_2026-10-01_2026-10-31.csv" in r["Content-Disposition"]


@pytest.mark.parametrize("tabla", ["", "no_existe", "../etc/passwd", "lambda;rm"])
def test_una_tabla_desconocida_da_404(admin_client, tabla):
    assert admin_client.get(reverse("analitica:exportar"), {"tabla": tabla}).status_code == 404


def test_un_filtro_invalido_da_400_y_no_exporta_otro_periodo(admin_client, simulados):
    r = admin_client.get(reverse("analitica:exportar"), {
        "tabla": "lambda", "desde": "2026-03-10", "hasta": "2026-03-01", "espera_max": 20})
    assert r.status_code == 400 and "Filtro no válido" in r.content.decode()


def test_sin_datos_exporta_solo_el_encabezado(admin_client):
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "absorcion"}))
    assert len(filas) == 1 and filas[0][0] == "desde_etapa"


def test_el_panel_enlaza_a_las_descargas(admin_client, simulados):
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    for tabla in ("lambda", "poisson", "colas", "matriz", "absorcion"):
        assert f"exportar/?tabla={tabla}&amp;" in html, tabla
