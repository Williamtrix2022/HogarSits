"""Alertas y recordatorios de seguimiento (#33 y #52; HU-12, RF-25, RF-26, RF-35, RN-13)."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.agenda import services as agenda
from apps.agenda.models import Visita
from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol
from apps.inmuebles.models import Inmueble
from apps.seguimiento import services
from apps.seguimiento.models import Etapa, SeguimientoEtapa, SolicitudAtencion

User = get_user_model()

pytestmark = pytest.mark.django_db


def usuario(nombre, rol=ROL_ASESOR):
    u = User.objects.create_user(nombre, password="Clave-Segura-2026", first_name=nombre.title())
    asignar_rol(u, rol)
    return u


@pytest.fixture
def ana():
    return usuario("ana")


@pytest.fixture
def luis():
    return usuario("luis")


@pytest.fixture
def jefe():
    return usuario("jefe", ROL_ADMIN)


def cliente(nombre="Marta Ríos"):
    n = Cliente.objects.count()  # el correo es único (RN-10)
    return Cliente.objects.create(
        nombre=nombre, correo=f"cliente{n}@example.com", telefono="3001234567"
    )


def solicitud(asesor, hace_dias=0, nombre="Marta Ríos", **extra):
    """Una solicitud que llegó hace `hace_dias` días y tiene un asesor responsable."""
    llegada = timezone.now() - timedelta(days=hace_dias)
    return SolicitudAtencion.objects.create(
        cliente=cliente(nombre), tipo_interes="COMPRA", asesor=asesor,
        timestamp_llegada=llegada, **extra,
    )


# --- Servicio: qué es un pendiente --------------------------------------------------------
def test_se_ordenan_por_antiguedad_la_mas_olvidada_primero(ana):
    solicitud(ana, 1, "Reciente Uno")
    solicitud(ana, 6, "Vieja Dos")
    solicitud(ana, 3, "Media Tres")
    nombres = [p.solicitud.cliente.nombre for p in services.pendientes_de_seguimiento(ana)]
    assert nombres == ["Vieja Dos", "Media Tres", "Reciente Uno"]


def test_se_marca_sin_seguimiento_solo_al_superar_n_dias(ana, settings):
    settings.DIAS_SIN_SEGUIMIENTO = 3
    ahora = timezone.now()
    solicitud(ana, 2, "Dos Dias")
    solicitud(ana, 3, "Tres Dias")  # exactamente N: todavía no «más de N»
    solicitud(ana, 4, "Cuatro Dias")
    por_nombre = {
        p.solicitud.cliente.nombre: p.sin_seguimiento
        for p in services.pendientes_de_seguimiento(ana, ahora=ahora + timedelta(seconds=1))
    }
    assert por_nombre == {"Dos Dias": False, "Tres Dias": True, "Cuatro Dias": True}


def test_n_es_configurable(ana, settings):
    solicitud(ana, 5)
    settings.DIAS_SIN_SEGUIMIENTO = 10
    assert not services.pendientes_de_seguimiento(ana)[0].sin_seguimiento
    settings.DIAS_SIN_SEGUIMIENTO = 2
    assert services.pendientes_de_seguimiento(ana)[0].sin_seguimiento
    assert services.pendientes_de_seguimiento(ana, umbral_dias=30)[0].sin_seguimiento is False


def test_un_seguimiento_reinicia_el_conteo(ana):
    s = solicitud(ana, 8)
    assert services.pendientes_de_seguimiento(ana)[0].sin_seguimiento
    services.registrar_etapa(s, Etapa.CONSULTA, ana, "llamé")  # autotransición: también cuenta
    p = services.pendientes_de_seguimiento(ana)[0]
    assert p.dias == 0 and not p.sin_seguimiento


def test_el_ultimo_movimiento_es_el_seguimiento_mas_reciente(ana):
    s = solicitud(ana, 10)
    antiguo = SeguimientoEtapa.objects.create(solicitud=s, estado_origen=1, estado_destino=1)
    SeguimientoEtapa.objects.filter(pk=antiguo.pk).update(
        fecha_transicion=timezone.now() - timedelta(days=6)
    )
    assert services.pendientes_de_seguimiento(ana)[0].dias == 6


def test_no_son_pendientes_las_canceladas_ni_las_etapas_finales(ana):
    solicitud(ana, 9, "Cancelada Uno", estado="CANCELADO")
    solicitud(ana, 9, "Cerrada Dos", etapa_actual=Etapa.CIERRE)
    solicitud(ana, 9, "Abandonada Tres", etapa_actual=Etapa.ABANDONO)
    solicitud(ana, 9, "Activa Cuatro")
    nombres = [p.solicitud.cliente.nombre for p in services.pendientes_de_seguimiento(ana)]
    assert nombres == ["Activa Cuatro"]


def test_cada_asesor_ve_solo_lo_suyo_y_sin_filtro_se_ve_todo(ana, luis):
    solicitud(ana, 1, "De Ana")
    solicitud(luis, 1, "De Luis")
    assert [p.solicitud.cliente.nombre for p in services.pendientes_de_seguimiento(ana)] == ["De Ana"]
    assert len(services.pendientes_de_seguimiento()) == 2


def test_una_solicitud_sin_asesor_solo_aparece_en_la_vista_del_equipo(ana):
    solicitud(None, 1, "Sin Asesor")
    assert services.pendientes_de_seguimiento(ana) == []
    assert len(services.pendientes_de_seguimiento()) == 1


def test_dias_cuenta_dias_completos(ana):
    solicitud(ana, 0)
    assert services.pendientes_de_seguimiento(ana)[0].dias == 0


# --- Pantalla de inicio -------------------------------------------------------------------
def test_el_inicio_lista_lo_pendiente_del_asesor_con_la_marca(client, ana):
    solicitud(ana, 6, "Olvidada Uno")
    solicitud(ana, 0, "Fresca Dos")
    client.force_login(ana)
    html = client.get(reverse("cuentas:inicio")).content.decode()
    assert "A quién contactar hoy" in html
    assert html.index("Olvidada Uno") < html.index("Fresca Dos")
    assert "Sin seguimiento" in html and "sin movimiento hace 6 días" in html


def test_el_inicio_vacio_dice_todo_al_dia(client, ana):
    client.force_login(ana)
    html = client.get(reverse("cuentas:inicio")).content.decode()
    assert "Todo al día. No tiene seguimientos pendientes." in html
    assert "No tiene visitas hoy ni mañana" in html


def test_el_inicio_no_muestra_lo_de_otro_asesor(client, ana, luis):
    solicitud(luis, 6, "Cliente De Luis")
    client.force_login(ana)
    assert "Cliente De Luis" not in client.get(reverse("cuentas:inicio")).content.decode()


def test_el_inicio_limita_el_panel_y_enlaza_a_todas(client, ana):
    for i in range(7):
        solicitud(ana, i + 1, f"Cliente{i} Apellido")
    client.force_login(ana)
    html = client.get(reverse("cuentas:inicio")).content.decode()
    assert "Ver las 7 pendientes" in html
    assert html.count('class="pendiente') == 5


def test_el_inicio_cuenta_las_solicitudes_en_espera(client, ana):
    solicitud(ana, 0, "En Espera")
    client.force_login(ana)
    assert "<strong>1</strong> en espera" in client.get(reverse("cuentas:inicio")).content.decode()


def test_el_administrador_ve_todo_el_equipo_y_puede_filtrar(client, jefe, ana, luis):
    solicitud(ana, 5, "De Ana")
    solicitud(luis, 5, "De Luis")
    client.force_login(jefe)
    todo = client.get(reverse("cuentas:inicio")).content.decode()
    assert "De Ana" in todo and "De Luis" in todo
    solo_ana = client.get(reverse("cuentas:inicio"), {"asesor": ana.pk}).content.decode()
    assert "De Ana" in solo_ana and "De Luis" not in solo_ana


def test_un_asesor_no_puede_ver_lo_de_otro_pasando_el_parametro(client, ana, luis):
    solicitud(luis, 5, "De Luis")
    client.force_login(ana)
    html = client.get(reverse("cuentas:inicio"), {"asesor": luis.pk}).content.decode()
    assert "De Luis" not in html
    html = client.get(reverse("seguimiento:pendientes"), {"asesor": luis.pk}).content.decode()
    assert "De Luis" not in html


def test_un_parametro_de_asesor_invalido_no_rompe(client, jefe):
    client.force_login(jefe)
    assert client.get(reverse("cuentas:inicio"), {"asesor": "abc"}).status_code == 200
    assert client.get(reverse("cuentas:inicio"), {"asesor": "9999"}).status_code == 200


def test_la_pagina_de_pendientes_lista_todas(client, ana):
    for i in range(7):
        solicitud(ana, i + 1, f"Cliente{i} Apellido")
    client.force_login(ana)
    html = client.get(reverse("seguimiento:pendientes")).content.decode()
    assert "7 solicitudes pendientes" in html and html.count('class="pendiente') == 7


def test_la_pagina_de_pendientes_vacia(client, ana):
    client.force_login(ana)
    assert "Todo al día" in client.get(reverse("seguimiento:pendientes")).content.decode()


def test_requieren_sesion(client):
    for nombre in ("cuentas:inicio", "seguimiento:pendientes"):
        r = client.get(reverse(nombre))
        assert r.status_code == 302 and "ingresar" in r["Location"]


# --- Mis visitas de hoy y mañana (#52, RF-35) ----------------------------------------------
def visita(asesor, inicio, estado="PROGRAMADA", titulo="Casa 12"):
    casa = Inmueble.objects.create(
        titulo=titulo, tipo_inmueble="CASA", operacion="VENTA", direccion="Cll 1", precio=100
    )
    s = solicitud(asesor, 0, f"Visitante {titulo.split()[-1]}")
    return Visita.objects.create(
        solicitud=s, inmueble=casa, asesor=asesor, inicio=inicio,
        fin=inicio + timedelta(hours=1), estado=estado,
    )


def a_las(dias, hora):
    base = timezone.localtime(timezone.now()).replace(hour=hora, minute=0, second=0, microsecond=0)
    return base + timedelta(days=dias)


def test_visitas_de_hoy_y_manana_solamente(ana):
    visita(ana, a_las(0, 23), titulo="Casa 1")
    visita(ana, a_las(1, 9), titulo="Casa 2")
    visita(ana, a_las(2, 9), titulo="Casa 3")  # pasado mañana: no
    visita(ana, a_las(-1, 9), titulo="Casa 4")  # ayer: no
    titulos = [v.inmueble.titulo for v in agenda.visitas_proximas(ana)]
    assert titulos == ["Casa 1", "Casa 2"]


def test_las_visitas_marcan_si_son_de_hoy(ana):
    visita(ana, a_las(0, 23), titulo="Casa 1")
    visita(ana, a_las(1, 9), titulo="Casa 2")
    assert [v.es_hoy for v in agenda.visitas_proximas(ana)] == [True, False]


def test_solo_las_programadas_y_solo_las_propias(ana, luis):
    visita(ana, a_las(1, 8), estado="CANCELADA", titulo="Casa 1")
    visita(ana, a_las(1, 10), estado="REALIZADA", titulo="Casa 2")
    visita(luis, a_las(1, 12), titulo="Casa 3")
    assert agenda.visitas_proximas(ana) == []
    assert len(agenda.visitas_proximas(luis)) == 1


def test_el_inicio_muestra_mis_visitas(client, ana):
    visita(ana, a_las(1, 9), titulo="Casa 7")
    client.force_login(ana)
    html = client.get(reverse("cuentas:inicio")).content.decode()
    assert "Mañana 09:00" in html and "Casa 7" in html
