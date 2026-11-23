"""Inmuebles vendidos o arrendados no se ofrecen (#31, HU-02, RF-15, RN-03)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ASESOR, asignar_rol
from apps.inmuebles import services
from apps.inmuebles.models import Inmueble
from apps.seguimiento.models import SolicitudAtencion

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def sesion(client):
    u = User.objects.create_user("asesor1", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    client.force_login(u)
    return client


@pytest.fixture
def cliente():
    return Cliente.objects.create(nombre="Ana", correo="ana@example.com", telefono="3001234567")


def inmueble(titulo="Casa", operacion="VENTA", estado="DISPONIBLE", **extra):
    return Inmueble.objects.create(
        titulo=titulo, tipo_inmueble="CASA", operacion=operacion, direccion="Cll 1", precio=100,
        estado=estado, **extra,
    )


@pytest.mark.parametrize(
    ("operacion", "estado"), [("VENTA", "VENDIDO"), ("ALQUILER", "ARRENDADO")]
)
def test_una_solicitud_rechaza_un_inmueble_cerrado(sesion, cliente, operacion, estado):
    cerrado = inmueble(operacion=operacion, estado=estado)
    r = sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "inmueble": cerrado.pk},
    )
    assert r.status_code == 200
    assert "no se puede ofrecer" in r.content.decode()
    assert not SolicitudAtencion.objects.exists()


def test_una_solicitud_rechaza_un_inmueble_inactivo(sesion, cliente):
    inactivo = inmueble(activo=False)
    r = sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "inmueble": inactivo.pk},
    )
    assert r.status_code == 200 and not SolicitudAtencion.objects.exists()


@pytest.mark.parametrize("estado", ["DISPONIBLE", "RESERVADO"])
def test_disponible_y_reservado_si_se_ofrecen(sesion, cliente, estado):
    ok = inmueble(estado=estado)
    r = sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "inmueble": ok.pk},
    )
    assert r.status_code == 302 and SolicitudAtencion.objects.get().inmueble == ok


def test_el_selector_no_lista_los_cerrados(sesion):
    inmueble("Casa libre")
    inmueble("Casa vendida", estado="VENDIDO")
    html = sesion.get(reverse("seguimiento:crear")).content.decode()
    assert "Casa libre" in html and "Casa vendida" not in html


def test_ofrecibles_excluye_cerrados_e_inactivos():
    libre = inmueble("Libre")
    inmueble("Vendida", estado="VENDIDO")
    inmueble("Arrendada", operacion="ALQUILER", estado="ARRENDADO")
    inmueble("Inactiva", activo=False)
    assert list(services.inmuebles_ofrecibles()) == [libre]
    assert services.se_puede_ofrecer(libre)
    assert not services.se_puede_ofrecer(Inmueble.objects.get(titulo="Vendida"))


def test_cerrar_un_inmueble_con_solicitudes_abiertas_avisa(sesion, cliente):
    casa = inmueble()
    SolicitudAtencion.objects.create(cliente=cliente, inmueble=casa, tipo_interes="COMPRA")
    datos = {
        "titulo": casa.titulo, "tipo_inmueble": "CASA", "operacion": "VENTA",
        "direccion": "Cll 1", "barrio": "", "precio": "100", "area_m2": "", "habitaciones": 0,
        "estado": "VENDIDO", "descripcion": "", "activo": "on",
    }
    r = sesion.post(reverse("inmuebles:editar", args=[casa.pk]), datos, follow=True)
    assert "1 solicitud(es) abierta(s)" in r.content.decode()


def test_cerrar_un_inmueble_sin_solicitudes_no_avisa(sesion):
    casa = inmueble()
    datos = {
        "titulo": casa.titulo, "tipo_inmueble": "CASA", "operacion": "VENTA",
        "direccion": "Cll 1", "barrio": "", "precio": "100", "area_m2": "", "habitaciones": 0,
        "estado": "VENDIDO", "descripcion": "", "activo": "on",
    }
    r = sesion.post(reverse("inmuebles:editar", args=[casa.pk]), datos, follow=True)
    assert "solicitud(es)" not in r.content.decode()
