"""Solicitudes de atención con tiempos de espera y servicio (#29, HU-04, RF-22 a RF-24, RN-11, RN-12, RN-20 a RN-22)."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol
from apps.inmuebles.models import Inmueble
from apps.seguimiento import services
from apps.seguimiento.models import SolicitudAtencion

User = get_user_model()
Estado = SolicitudAtencion.Estado

pytestmark = pytest.mark.django_db


def usuario(nombre, rol=ROL_ASESOR):
    u = User.objects.create_user(nombre, password="Clave-Segura-2026")
    asignar_rol(u, rol)
    return u


@pytest.fixture
def ana():
    return usuario("ana")


@pytest.fixture
def luis():
    return usuario("luis")


@pytest.fixture
def sesion(client, ana):
    client.force_login(ana)
    return client


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(nombre="Marta Ríos", correo="marta@example.com", telefono="3001234567")


def solicitud(cliente, **extra):
    return SolicitudAtencion.objects.create(cliente=cliente, tipo_interes="COMPRA", **extra)


# --- Alta ---------------------------------------------------------------------------------
def test_requiere_sesion(client):
    r = client.get(reverse("seguimiento:cola"))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_registrar_fija_la_llegada_automaticamente_y_queda_en_espera(sesion, cliente):
    antes = timezone.now()
    r = sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "presupuesto": "240.000.000"},
    )
    assert r.status_code == 302
    s = SolicitudAtencion.objects.get()
    assert s.estado == Estado.EN_ESPERA
    assert antes <= s.timestamp_llegada <= timezone.now()
    assert s.presupuesto == 240_000_000


def test_el_formulario_ignora_una_llegada_enviada_a_mano(sesion, cliente):
    """RN-11: la hora de llegada no es editable por el asesor."""
    falsa = timezone.now() - timedelta(days=30)
    sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "timestamp_llegada": falsa.isoformat()},
    )
    assert SolicitudAtencion.objects.get().timestamp_llegada > falsa + timedelta(days=29)


def test_cliente_y_tipo_de_interes_son_obligatorios(sesion, cliente):
    r = sesion.post(reverse("seguimiento:crear"), {"tipo_interes": "COMPRA"})
    assert r.status_code == 200 and not SolicitudAtencion.objects.exists()
    r = sesion.post(reverse("seguimiento:crear"), {"cliente": cliente.pk})
    assert r.status_code == 200 and not SolicitudAtencion.objects.exists()


def test_presupuesto_debe_ser_positivo(sesion, cliente):
    r = sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "presupuesto": "0"},
    )
    assert r.status_code == 200 and not SolicitudAtencion.objects.exists()


def test_el_inmueble_de_interes_es_opcional(sesion, cliente):
    inmueble = Inmueble.objects.create(
        titulo="Casa", tipo_inmueble="CASA", operacion="VENTA", direccion="Cll 1", precio=100
    )
    r = sesion.post(
        reverse("seguimiento:crear"),
        {"cliente": cliente.pk, "tipo_interes": "COMPRA", "inmueble": inmueble.pk},
    )
    assert r.status_code == 302 and SolicitudAtencion.objects.get().inmueble == inmueble


# --- Transiciones y tiempos ---------------------------------------------------------------
def test_tomar_asigna_al_asesor_y_guarda_el_inicio(cliente, ana):
    s = services.tomar(solicitud(cliente), ana)
    assert (s.estado, s.asesor) == (Estado.EN_ATENCION, ana)
    assert s.timestamp_inicio_atencion >= s.timestamp_llegada  # RN-20


def test_ciclo_completo_calcula_espera_y_servicio(cliente, ana):
    llegada = timezone.now() - timedelta(minutes=30)
    s = solicitud(cliente, timestamp_llegada=llegada)
    SolicitudAtencion.objects.filter(pk=s.pk).update(
        estado=Estado.FINALIZADO,
        asesor=ana,
        timestamp_inicio_atencion=llegada + timedelta(minutes=10),
        timestamp_fin_atencion=llegada + timedelta(minutes=25),
    )
    s.refresh_from_db()
    assert services.tiempo_espera(s) == timedelta(minutes=10)  # RN-21: inicio − llegada
    assert services.tiempo_servicio(s) == timedelta(minutes=15)  # RN-21: fin − inicio
    assert services.aporta_a_mu(s)


def test_finalizar_guarda_el_fin_despues_del_inicio(cliente, ana):
    s = services.finalizar(services.tomar(solicitud(cliente), ana), ana)
    assert s.estado == Estado.FINALIZADO
    assert s.timestamp_llegada <= s.timestamp_inicio_atencion <= s.timestamp_fin_atencion


def test_no_se_puede_tomar_dos_veces(cliente, ana, luis):
    s = solicitud(cliente)
    services.tomar(s, ana)
    with pytest.raises(services.TransicionInvalida):
        services.tomar(s, luis)
    s.refresh_from_db()
    assert s.asesor == ana  # RN-12: un único responsable


def test_solo_el_responsable_finaliza(cliente, ana, luis):
    s = services.tomar(solicitud(cliente), ana)
    with pytest.raises(services.TransicionInvalida):
        services.finalizar(s, luis)
    assert services.finalizar(s, luis, es_admin=True).estado == Estado.FINALIZADO


def test_no_se_finaliza_lo_que_no_esta_en_atencion(cliente, ana):
    with pytest.raises(services.TransicionInvalida):
        services.finalizar(solicitud(cliente), ana)


def test_cancelada_no_aporta_a_mu(cliente):
    """RN-22: las canceladas se excluyen de la estimación de μ."""
    s = services.cancelar(solicitud(cliente))
    assert s.estado == Estado.CANCELADO
    assert services.tiempo_servicio(s) is None and not services.aporta_a_mu(s)
    assert services.tiempo_espera(s) is None


def test_solo_se_cancela_lo_que_sigue_en_espera(cliente, ana):
    s = services.tomar(solicitud(cliente), ana)
    with pytest.raises(services.TransicionInvalida):
        services.cancelar(s)


def test_la_espera_de_una_solicitud_abierta_crece_con_el_tiempo(cliente):
    s = solicitud(cliente, timestamp_llegada=timezone.now() - timedelta(minutes=7))
    assert timedelta(minutes=7) <= services.tiempo_espera(s) < timedelta(minutes=8)


# --- Cola (vistas) ------------------------------------------------------------------------
def test_la_cola_muestra_abiertas_por_orden_de_llegada(sesion, cliente):
    otro = Cliente.objects.create(nombre="Zoe Vega", correo="zoe@example.com", telefono="3110000000")
    solicitud(otro, timestamp_llegada=timezone.now() - timedelta(minutes=5))
    solicitud(cliente, timestamp_llegada=timezone.now() - timedelta(minutes=20))
    solicitud(cliente, estado=Estado.CANCELADO)
    html = sesion.get(reverse("seguimiento:cola")).content.decode()
    assert html.index("Marta Ríos") < html.index("Zoe Vega")  # la que llegó antes, primero
    assert "2 solicitudes" in html  # la cancelada no está entre las abiertas


def test_filtrar_por_estado(sesion, cliente):
    solicitud(cliente, estado=Estado.CANCELADO)
    html = sesion.get(reverse("seguimiento:cola"), {"estado": "CANCELADO"}).content.decode()
    assert "1 solicitud con estos filtros" in html


def test_atender_y_finalizar_desde_la_cola(sesion, cliente, ana):
    s = solicitud(cliente)
    assert sesion.post(reverse("seguimiento:tomar", args=[s.pk])).status_code == 302
    s.refresh_from_db()
    assert (s.estado, s.asesor) == (Estado.EN_ATENCION, ana)
    sesion.post(reverse("seguimiento:finalizar", args=[s.pk]))
    s.refresh_from_db()
    assert s.estado == Estado.FINALIZADO


def test_una_accion_invalida_muestra_el_error_y_no_cambia_nada(sesion, cliente, luis):
    s = services.tomar(solicitud(cliente), luis)
    r = sesion.post(reverse("seguimiento:finalizar", args=[s.pk]), follow=True)
    assert "Solo el asesor que la atiende puede finalizarla" in r.content.decode()
    s.refresh_from_db()
    assert s.estado == Estado.EN_ATENCION


def test_las_acciones_solo_aceptan_post(sesion, cliente):
    s = solicitud(cliente)
    assert sesion.get(reverse("seguimiento:tomar", args=[s.pk])).status_code == 405


def test_next_externo_no_redirige_fuera_del_sitio(sesion, cliente):
    s = solicitud(cliente)
    r = sesion.post(reverse("seguimiento:cancelar", args=[s.pk]), {"next": "https://malo.example/"})
    assert r["Location"] == reverse("seguimiento:cola")


def test_el_administrador_puede_finalizar_la_de_otro(client, cliente, luis):
    s = services.tomar(solicitud(cliente), luis)
    client.force_login(usuario("jefe", ROL_ADMIN))
    client.post(reverse("seguimiento:finalizar", args=[s.pk]))
    s.refresh_from_db()
    assert s.estado == Estado.FINALIZADO


def test_el_menu_muestra_solicitudes(sesion):
    assert reverse("seguimiento:cola") in sesion.get(reverse("cuentas:inicio")).content.decode()


def test_filtro_duracion():
    from apps.comun.templatetags.formato import duracion

    assert duracion(None) == "—"
    assert duracion(timedelta(seconds=45)) == "45 s"
    assert duracion(timedelta(minutes=12, seconds=30)) == "12 min"
    assert duracion(timedelta(hours=1, minutes=5)) == "1 h 05 min"
