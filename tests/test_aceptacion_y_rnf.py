"""Criterios de aceptación y requisitos no funcionales que solo se cumplían «por configuración» (#42).

Al armar la trazabilidad del plan de pruebas se vio que estos puntos no tenían una prueba que los
fijara: si alguien cambiara un ajuste, nada avisaría.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cuentas.roles import ROL_ASESOR, asignar_rol
from apps.inmuebles.models import Inmueble

User = get_user_model()
RAIZ = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.django_db


@pytest.fixture
def sesion(client):
    u = User.objects.create_user("asesor_rnf", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    client.force_login(u)
    return client


def datos_inmueble(**extra):
    return {
        "titulo": "Casa", "tipo_inmueble": "CASA", "operacion": "VENTA", "direccion": "Cll 1",
        "barrio": "", "precio": "100.000.000", "area_m2": "", "habitaciones": 2,
        "estado": "DISPONIBLE", "descripcion": "", **extra,
    }


# --- HU-01 CA3: el estado solo toma los cuatro valores ---------------------------------------
@pytest.mark.parametrize("estado", ["PERDIDO", "disponible", "", "VENDIDA", "1"])
def test_un_estado_inventado_no_se_acepta(sesion, estado):
    r = sesion.post(reverse("inmuebles:crear"), datos_inmueble(estado=estado))
    assert r.status_code == 200 and not Inmueble.objects.exists()


@pytest.mark.parametrize("estado", ["DISPONIBLE", "RESERVADO"])
def test_los_estados_validos_si_se_aceptan(sesion, estado):
    r = sesion.post(reverse("inmuebles:crear"), datos_inmueble(estado=estado))
    assert r.status_code == 302 and Inmueble.objects.get().estado == estado


def test_el_modelo_define_exactamente_cuatro_estados():
    assert {v for v, _ in Inmueble.Estado.choices} == {
        "DISPONIBLE", "RESERVADO", "VENDIDO", "ARRENDADO"}


# --- RNF-02: la lógica estocástica son funciones puras ---------------------------------------
def test_ningun_servicio_estocastico_importa_django():
    servicios = sorted((RAIZ / "apps" / "analitica" / "services").glob("*.py"))
    assert len(servicios) >= 5
    for archivo in servicios:
        importados = re.findall(r"^\s*(?:from|import)\s+(\S+)", archivo.read_text(encoding="utf-8"),
                                re.M)
        assert not [m for m in importados if m.split(".")[0] == "django"], archivo.name


# --- RNF-04: seguridad ---------------------------------------------------------------------------
def test_las_contrasenas_se_guardan_con_hash():
    u = User.objects.create_user("hash_rnf", password="Clave-Segura-2026")
    assert "Clave-Segura-2026" not in u.password and u.password.startswith("pbkdf2_")


def test_el_acceso_exige_sesion_por_defecto_con_el_middleware():
    assert "django.contrib.auth.middleware.LoginRequiredMiddleware" in settings.MIDDLEWARE


def test_la_produccion_exige_https_y_cookies_seguras(monkeypatch):
    monkeypatch.delenv("SECURE_SSL_REDIRECT", raising=False)
    import importlib

    from config.settings import prod

    prod = importlib.reload(prod)
    assert prod.DEBUG is False
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.SESSION_COOKIE_SECURE is True and prod.CSRF_COOKIE_SECURE is True
    assert prod.SECURE_HSTS_SECONDS >= 31536000
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_el_gitignore_protege_los_secretos_y_los_datos_de_encuestas():
    lineas = {linea.strip() for linea in (RAIZ / ".gitignore").read_text().splitlines()}
    assert ".env" in lineas  # secretos solo en .env (RNF-04)
    assert "docs/*.csv" in lineas  # datos crudos de encuestas: repositorio público (RNF-08)
    assert "media/" in lineas  # fotos subidas en desarrollo


def test_el_ejemplo_de_entorno_no_trae_secretos_reales():
    ejemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    asignaciones = dict(
        linea.split("=", 1) for linea in ejemplo.splitlines()
        if "=" in linea and not linea.lstrip().startswith("#")
    )
    assert "cambia-esto" in asignaciones["SECRET_KEY"]
    assert "AKIA" not in ejemplo  # ninguna clave de AWS


# --- RNF-05 y RNF-07: idioma y zona horaria --------------------------------------------------------
def test_la_interfaz_esta_en_espanol_de_colombia():
    assert settings.LANGUAGE_CODE == "es-co"


def test_la_zona_horaria_es_bogota_y_los_datos_se_guardan_en_utc():
    from datetime import timedelta

    from django.utils import timezone

    from apps.clientes.models import Cliente
    from apps.seguimiento.models import SolicitudAtencion

    assert settings.TIME_ZONE == "America/Bogota" and settings.USE_TZ is True
    c = Cliente.objects.create(nombre="Z", correo="z@example.com", telefono="3001234567")
    s = SolicitudAtencion.objects.create(cliente=c, tipo_interes="COMPRA")
    guardado = SolicitudAtencion.objects.values_list("timestamp_llegada", flat=True).get(pk=s.pk)
    assert guardado.utcoffset() == timedelta(0)  # la BD devuelve UTC
    assert timezone.localtime(guardado).utcoffset() == timedelta(hours=-5)  # y se muestra en Bogotá


@pytest.mark.xfail(
    strict=True,
    reason="HU-01 CA3: solo el formulario valida el estado; la BD no tiene un CHECK de valores "
    "(hallazgo abierto del plan de pruebas)",
)
def test_la_bd_tambien_rechaza_un_estado_inventado():
    """RNF-03 pide integridad en la BD. Hoy un `create(estado="PERDIDO")` fuera del formulario
    (admin, shell, una carga de datos) entra sin error. Cuando exista el CHECK, pasará: `strict`
    obligará a quitar esta marca."""
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        Inmueble.objects.create(
            titulo="X", tipo_inmueble="CASA", operacion="VENTA", direccion="Cll 1",
            precio=100, estado="PERDIDO",
        )
