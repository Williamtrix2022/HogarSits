"""CRUD de clientes sin duplicados (#28, HU-03, RF-20, RF-21, RN-10)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ASESOR, asignar_rol

User = get_user_model()

pytestmark = pytest.mark.django_db

DATOS = {"nombre": "Ana Pérez", "correo": "ana@example.com", "telefono": "300 123 4567"}


@pytest.fixture
def sesion(client):
    u = User.objects.create_user("asesor1", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    client.force_login(u)
    return client


def crear(**extra):
    return Cliente.objects.create(**{**DATOS, **extra})


def test_requiere_sesion(client):
    r = client.get(reverse("clientes:lista"))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_crea_cliente_normalizando_correo_y_nombre(sesion):
    r = sesion.post(
        reverse("clientes:crear"),
        {"nombre": "  Ana   Pérez ", "correo": " ANA@Example.COM ", "telefono": "300 123 4567"},
    )
    assert r.status_code == 302
    c = Cliente.objects.get()
    assert (c.nombre, c.correo) == ("Ana Pérez", "ana@example.com")


def test_correo_duplicado_se_rechaza_sin_distinguir_mayusculas(sesion):
    crear()
    r = sesion.post(reverse("clientes:crear"), {**DATOS, "correo": "ANA@EXAMPLE.COM", "nombre": "Otra"})
    assert r.status_code == 200
    assert "Ya existe un cliente con este correo" in r.content.decode()
    assert Cliente.objects.count() == 1


def test_editar_conservando_su_propio_correo_es_valido(sesion):
    c = crear()
    r = sesion.post(reverse("clientes:editar", args=[c.pk]), {**DATOS, "nombre": "Ana María"})
    assert r.status_code == 302
    c.refresh_from_db()
    assert c.nombre == "Ana María"


def test_editar_no_puede_tomar_el_correo_de_otro(sesion):
    crear()
    otro = crear(nombre="Luis", correo="luis@example.com", telefono="3110000000")
    r = sesion.post(reverse("clientes:editar", args=[otro.pk]), {**DATOS, "nombre": "Luis"})
    assert r.status_code == 200
    otro.refresh_from_db()
    assert otro.correo == "luis@example.com"


@pytest.mark.parametrize("telefono", ["abc", "123", "30012345678901234", "300-12x-4567"])
def test_telefono_invalido(sesion, telefono):
    r = sesion.post(reverse("clientes:crear"), {**DATOS, "telefono": telefono})
    assert r.status_code == 200
    assert not Cliente.objects.exists()


@pytest.mark.parametrize("campo", ["nombre", "correo", "telefono"])
def test_campos_obligatorios(sesion, campo):
    r = sesion.post(reverse("clientes:crear"), {**DATOS, campo: ""})
    assert r.status_code == 200
    assert not Cliente.objects.exists()


def test_telefono_repetido_avisa_pero_guarda(sesion):
    crear()
    r = sesion.post(
        reverse("clientes:crear"),
        {"nombre": "Luis", "correo": "luis@example.com", "telefono": "3001234567"},
        follow=True,
    )
    assert Cliente.objects.count() == 2
    assert "ya lo usa" in r.content.decode()


def test_busqueda_por_nombre_correo_y_telefono(sesion):
    crear()
    crear(nombre="Luis Gómez", correo="luis@example.com", telefono="311 000 0000")
    url = reverse("clientes:lista")
    assert "Ana Pérez" in sesion.get(url, {"q": "pérez"}).content.decode()
    assert "Ana Pérez" not in sesion.get(url, {"q": "luis@"}).content.decode()
    assert "Luis Gómez" in sesion.get(url, {"q": "3110000000"}).content.decode()


def test_lista_vacia_invita_a_registrar(sesion):
    assert "Aún no hay clientes" in sesion.get(reverse("clientes:lista")).content.decode()


def test_la_pantalla_de_edicion_muestra_sus_solicitudes(sesion):
    c = crear()
    r = sesion.get(reverse("clientes:editar", args=[c.pk]))
    assert "aún no tiene solicitudes" in r.content.decode()


def test_el_menu_muestra_clientes(sesion):
    assert reverse("clientes:lista") in sesion.get(reverse("cuentas:inicio")).content.decode()
