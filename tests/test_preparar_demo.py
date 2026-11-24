"""El comando que prepara el despliegue de demostracion: idempotente y sin filtrar claves."""
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, rol_de
from apps.seguimiento.models import SolicitudAtencion

pytestmark = pytest.mark.django_db
RAIZ = Path(__file__).resolve().parent.parent
CLAVE_ADMIN = "Clave-Demo-Admin-2026"
CLAVE_ASESOR = "Clave-Demo-Asesor-2026"


def preparar(monkeypatch, **extra) -> str:
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", CLAVE_ADMIN)
    monkeypatch.setenv("DEMO_ASESOR_PASSWORD", CLAVE_ASESOR)
    salida = StringIO()
    call_command("preparar_demo", "--dias", "10", "--asesores", "2", stdout=salida, **extra)
    return salida.getvalue()


def test_crea_administrador_asesor_y_datos(monkeypatch):
    salida = preparar(monkeypatch)
    User = get_user_model()
    assert rol_de(User.objects.get(username="administradora")) == ROL_ADMIN
    assert rol_de(User.objects.get(username="asesor_demo")) == ROL_ASESOR
    assert SolicitudAtencion.objects.exists()
    assert "Demostración lista" in salida


def test_las_claves_no_aparecen_en_la_salida(monkeypatch):
    salida = preparar(monkeypatch)
    assert CLAVE_ADMIN not in salida and CLAVE_ASESOR not in salida


def test_es_idempotente_y_no_cambia_claves_ni_duplica_datos(monkeypatch):
    preparar(monkeypatch)
    User = get_user_model()
    usuarios, solicitudes = User.objects.count(), SolicitudAtencion.objects.count()
    clave_antes = User.objects.get(username="administradora").password
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "Otra-Clave-Distinta-2026")
    salida = preparar_sin_cambiar_env()
    assert User.objects.count() == usuarios
    assert SolicitudAtencion.objects.count() == solicitudes
    assert User.objects.get(username="administradora").password == clave_antes
    assert "ya existe" in salida and "no se generan datos simulados" in salida


def preparar_sin_cambiar_env() -> str:
    salida = StringIO()
    call_command("preparar_demo", "--dias", "10", "--asesores", "2", stdout=salida)
    return salida.getvalue()


def test_sin_contrasenas_no_crea_usuarios(monkeypatch):
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("DEMO_ASESOR_PASSWORD", raising=False)
    salida = StringIO()
    call_command("preparar_demo", "--dias", "10", "--asesores", "2", stdout=salida)
    assert not get_user_model().objects.filter(username__in=["administradora", "asesor_demo"]).exists()
    assert "no se crea el usuario" in salida.getvalue()


def test_el_administrador_creado_puede_entrar_y_ver_el_analisis(client, monkeypatch):
    preparar(monkeypatch)
    assert client.login(username="administradora", password=CLAVE_ADMIN)
    assert client.get(reverse("analitica:inicio")).status_code == 200


def test_el_asesor_creado_no_ve_el_analisis(client, monkeypatch):
    preparar(monkeypatch)
    assert client.login(username="asesor_demo", password=CLAVE_ASESOR)
    assert client.get(reverse("analitica:inicio")).status_code == 403
    assert client.get(reverse("analitica:asesores")).status_code == 200


def test_el_blueprint_no_contiene_contrasenas_y_las_pide_aparte():
    texto = (RAIZ / "render.yaml").read_text(encoding="utf-8")
    for clave in ("DEMO_ADMIN_PASSWORD", "DEMO_ASESOR_PASSWORD"):
        bloque = texto.split(f"key: {clave}")[1].split("- key:")[0]
        assert "sync: false" in bloque and "value:" not in bloque
    assert "generateValue: true" in texto  # SECRET_KEY nunca va escrita
    assert "fromDatabase" in texto and "postgres://" not in texto


def test_el_arranque_solo_prepara_la_demo_si_se_pide():
    texto = (RAIZ / "scripts" / "entrypoint.sh").read_text(encoding="utf-8")
    assert 'PREPARAR_DEMO:-0}" = "1"' in texto
    assert "\r" not in texto


def test_la_guia_de_render_existe_y_declara_sus_limites():
    texto = (RAIZ / "docs" / "aws" / "DESPLIEGUE_RENDER.md").read_text(encoding="utf-8")
    assert "datos simulados" in texto and "caduca a los 30 días" in texto
    assert "no** reemplaza el despliegue en AWS" in texto
