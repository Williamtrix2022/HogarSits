"""Ramas de error y casos borde que la medición de cobertura mostró sin probar (#42).

No se escriben para subir un porcentaje: cada una fija un comportamiento que importa (la
carrera de dos asesores guardando a la vez, el reinicio del bloqueo por intentos, los mensajes
cuando una acción ya no aplica).
"""

from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from apps.agenda import services
from apps.agenda.models import Visita
from apps.cuentas.models import IntentoAcceso
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol

User = get_user_model()
CLAVE = "Clave-Segura-2026"

pytestmark = pytest.mark.django_db


def futuro(horas=24):
    return (timezone.now() + timedelta(hours=horas)).replace(second=0, microsecond=0)


@pytest.fixture
def sesion(client, asesor):
    asignar_rol(asesor, ROL_ASESOR)
    client.force_login(asesor)
    return client


# --- Carrera: dos asesores guardan en el mismo instante ------------------------------------------
def test_si_la_bd_rechaza_por_carrera_se_traduce_a_un_mensaje_claro(solicitud, inmueble, asesor):
    """La validación previa pasó, pero otro asesor ocupó el horario antes del INSERT."""
    with mock.patch.object(Visita.objects, "create", side_effect=IntegrityError("exclusion")):
        with pytest.raises(services.AgendaError, match="se ocupó hace un momento"):
            services.programar(solicitud, inmueble, asesor, futuro(), 60)
    assert not Visita.objects.exists()


def test_la_pantalla_muestra_el_error_de_la_carrera_y_no_guarda(sesion, solicitud, inmueble, asesor):
    with mock.patch.object(services, "programar", side_effect=services.AgendaError("choque")):
        r = sesion.post(reverse("agenda:crear"), {
            "solicitud": solicitud.pk, "inmueble": inmueble.pk, "asesor": asesor.pk,
            "inicio": timezone.localtime(futuro()).strftime("%Y-%m-%dT%H:%M"), "duracion": 60})
    assert r.status_code == 200 and "choque" in r.content.decode() and not Visita.objects.exists()


def test_reprogramar_con_carrera_muestra_el_error_y_conserva_la_visita(
    sesion, solicitud, inmueble, asesor
):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    with mock.patch.object(services, "reprogramar", side_effect=services.AgendaError("choque")):
        r = sesion.post(reverse("agenda:reprogramar", args=[v.pk]), {
            "inicio": timezone.localtime(futuro(72)).strftime("%Y-%m-%dT%H:%M"), "duracion": 60})
    v.refresh_from_db()
    assert r.status_code == 200 and "choque" in r.content.decode() and v.estado == "PROGRAMADA"


# --- Acciones que ya no aplican -----------------------------------------------------------------
def test_no_se_marca_realizada_una_visita_cancelada(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    services.cancelar(v)
    with pytest.raises(services.AgendaError, match="visita programada"):
        services.realizar(v)


def test_no_se_reprograma_una_visita_cancelada(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    services.cancelar(v)
    with pytest.raises(services.AgendaError, match="Solo se reprograma"):
        services.reprogramar(v, futuro(48), 60)


def test_cancelar_dos_veces_desde_la_pantalla_muestra_el_error(sesion, solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    sesion.post(reverse("agenda:cancelar", args=[v.pk]))
    r = sesion.post(reverse("agenda:cancelar", args=[v.pk]), follow=True)
    assert "Solo se cancela una visita programada" in r.content.decode()


def test_el_enlace_desde_una_solicitud_preselecciona_la_solicitud(sesion, solicitud):
    r = sesion.get(reverse("agenda:crear"), {"solicitud": solicitud.pk})
    assert f'value="{solicitud.pk}" selected' in r.content.decode()


# --- Bloqueo por intentos: el reinicio cuando el bloqueo ya venció -------------------------------
def test_tras_vencer_el_bloqueo_un_fallo_empieza_de_cero_y_no_vuelve_a_bloquear(client):
    """Antes solo se probaba el acceso correcto tras el vencimiento; un NUEVO fallo también debe
    empezar la cuenta de nuevo, no heredar los 5 fallos anteriores."""
    User.objects.create_user("pepe", password=CLAVE)
    IntentoAcceso.objects.create(
        usuario="pepe", ip="127.0.0.1", fallos=5, bloqueado_hasta=timezone.now() - timedelta(minutes=1)
    )
    r = client.post(reverse("cuentas:login"), {"username": "pepe", "password": "mala"})
    texto = r.content.decode()
    assert "Usuario o contraseña incorrectos" in texto and "Demasiados intentos" not in texto
    intento = IntentoAcceso.objects.get(usuario="pepe")
    assert intento.fallos == 1 and intento.bloqueado_hasta is None


# --- Administración de usuarios ---------------------------------------------------------------------
def test_el_administrador_ve_la_pantalla_de_restablecer_clave(client, asesor):
    jefe = User.objects.create_user("jefe_h", password=CLAVE)
    asignar_rol(jefe, ROL_ADMIN)
    client.force_login(jefe)
    r = client.get(reverse("cuentas:usuario_clave", args=[asesor.pk]))
    assert r.status_code == 200 and f"Restablecer contraseña: {asesor.username}" in r.content.decode()


# --- #43: ninguna pantalla debe mostrar la opcion vacia en ingles ---------------------------------
@pytest.mark.parametrize("nombre_url", ["seguimiento:crear", "inmuebles:crear", "cuentas:usuario_nuevo"])
def test_los_formularios_no_muestran_texto_en_ingles(client, django_user_model, nombre_url):
    from django.urls import reverse

    from apps.cuentas.roles import ROL_ADMIN, asignar_rol

    jefe = django_user_model.objects.create_user("jefe_i18n", password="Clave-Larga-2026")
    asignar_rol(jefe, ROL_ADMIN)
    client.force_login(jefe)
    html = client.get(reverse(nombre_url)).content.decode()
    assert "Select an option" not in html
