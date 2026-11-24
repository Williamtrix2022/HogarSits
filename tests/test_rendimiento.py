"""RNF-06: listados y dashboard responden en menos de 3 s con ~10 000 solicitudes (#42).

Es una prueba **lenta** (genera más de 10 000 solicitudes simuladas), así que no corre en el CI
normal. Para ejecutarla:

    set HOGARSITS_RENDIMIENTO=1            (PowerShell: $env:HOGARSITS_RENDIMIENTO = "1")
    pytest tests/test_rendimiento.py -s

Imprime el tiempo de cada pantalla. Mide el servidor en un solo proceso, sin red ni navegador:
es el tiempo de generar la respuesta, no el de pintarla.
"""

import os
import statistics
import time

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.cuentas.roles import ROL_ADMIN, asignar_rol
from apps.seguimiento.models import SolicitudAtencion

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.skipif(
        os.environ.get("HOGARSITS_RENDIMIENTO") != "1",
        reason="prueba lenta: se activa con HOGARSITS_RENDIMIENTO=1",
    ),
]

def imprimir(mensaje: str) -> None:
    """La consola de Windows (cp1252) no imprime λ ni otros símbolos: solo se imprime ASCII."""
    print(mensaje.encode("ascii", "replace").decode("ascii"))


LIMITE_S = 3.0  # RNF-06
REPETICIONES = 3
MINIMO_SOLICITUDES = 10_000


@pytest.fixture(scope="module")
def datos_grandes(django_db_setup, django_db_blocker):
    """~10 300 solicitudes: 300 días con 40 clientes por día laboral."""
    with django_db_blocker.unblock():
        call_command(
            "seed_datos_simulados", "--dias", "300", "--clientes-por-dia", "40",
            "--asesores", "5", "--semilla", "1",
        )
        yield
        call_command("seed_datos_simulados", "--limpiar")


@pytest.fixture
def admin(datos_grandes):
    u = get_user_model().objects.create_user("jefe_rend", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ADMIN)
    c = Client()
    c.force_login(u)
    return c


PANTALLAS = [
    ("cola de solicitudes", "seguimiento:cola", {}),
    ("cola con filtro «todas»", "seguimiento:cola", {"estado": "TODAS"}),
    ("pendientes de seguimiento", "seguimiento:pendientes", {}),
    ("inicio (a quién contactar)", "cuentas:inicio", {}),
    ("clientes", "clientes:lista", {}),
    ("clientes, búsqueda", "clientes:lista", {"q": "0042"}),
    ("inmuebles", "inmuebles:lista", {}),
    ("agenda de la semana", "agenda:semana", {}),
    ("análisis (30 días con datos)", "analitica:inicio", {}),
    ("indicadores por asesor", "analitica:asesores", {}),
    ("exportar λ por hora", "analitica:exportar", {"tabla": "lambda"}),
    ("exportar matriz P", "analitica:exportar", {"tabla": "matriz"}),
]


def medir(cliente, url, params):
    tiempos = []
    consultas = 0
    for _ in range(REPETICIONES):
        with CaptureQueriesContext(connection) as q:
            t0 = time.perf_counter()
            r = cliente.get(url, params)
            tiempos.append(time.perf_counter() - t0)
        assert r.status_code == 200
        consultas = len(q)
    return statistics.median(tiempos), max(tiempos), consultas


def test_hay_el_volumen_de_datos_que_dice_el_requisito(datos_grandes):
    n = SolicitudAtencion.objects.count()
    imprimir(f"Solicitudes en la base: {n}")
    assert n >= MINIMO_SOLICITUDES


@pytest.mark.parametrize(("nombre", "ruta", "params"), PANTALLAS, ids=[p[0] for p in PANTALLAS])
def test_cada_pantalla_responde_en_menos_de_3_segundos(admin, nombre, ruta, params):
    mediana, peor, consultas = medir(admin, reverse(ruta), params)
    imprimir(
        f"{nombre}: mediana {mediana * 1000:.0f} ms | peor {peor * 1000:.0f} ms | "
        f"{consultas} consultas"
    )
    assert peor < LIMITE_S, f"{nombre} tardó {peor:.2f} s (límite {LIMITE_S} s)"


def test_el_analisis_de_un_año_completo_tambien_cumple(admin):
    """El rango máximo permitido por el filtro (366 días) es el peor caso del panel."""
    from apps.analitica import analisis

    primero, ultimo = analisis.rango_por_defecto(366)
    params = {"desde": primero.isoformat(), "hasta": ultimo.isoformat(), "espera_max": 20}
    mediana, peor, consultas = medir(admin, reverse("analitica:inicio"), params)
    imprimir(
        f"analisis, rango maximo ({(ultimo - primero).days + 1} dias): mediana "
        f"{mediana * 1000:.0f} ms | peor {peor * 1000:.0f} ms | {consultas} consultas"
    )
    assert peor < LIMITE_S
