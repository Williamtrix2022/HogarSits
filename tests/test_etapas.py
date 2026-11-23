"""Seguimiento de etapas con historial (#32, HU-06, RF-40 a RF-43, RN-30 a RN-33, ADR-002)."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ASESOR, asignar_rol
from apps.inmuebles.models import HistorialEstadoInmueble, Inmueble
from apps.seguimiento import services
from apps.seguimiento.models import Etapa, SeguimientoEtapa, SolicitudAtencion

User = get_user_model()

pytestmark = pytest.mark.django_db

C, V, N, CI, AB = Etapa.CONSULTA, Etapa.VISITA, Etapa.NEGOCIACION, Etapa.CIERRE, Etapa.ABANDONO


@pytest.fixture
def ana():
    u = User.objects.create_user("ana", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    return u


@pytest.fixture
def sesion(client, ana):
    client.force_login(ana)
    return client


@pytest.fixture
def cliente():
    return Cliente.objects.create(nombre="Marta Ríos", correo="m@example.com", telefono="3001234567")


def solicitud(cliente, etapa=C, **extra):
    return SolicitudAtencion.objects.create(
        cliente=cliente, tipo_interes="COMPRA", etapa_actual=etapa, **extra
    )


def inmueble(operacion="VENTA"):
    return Inmueble.objects.create(
        titulo="Casa 12", tipo_inmueble="CASA", operacion=operacion, direccion="Cll 1", precio=100
    )


# --- Reglas del servicio ------------------------------------------------------------------
def test_toda_solicitud_nace_en_consulta(cliente):  # RN-32
    assert solicitud(cliente).etapa_actual == C


def test_avanzar_guarda_la_transicion_y_actualiza_la_etapa(cliente, ana):
    s = solicitud(cliente)
    t = services.registrar_etapa(s, V, ana, "Visitó la casa")
    s.refresh_from_db()
    assert s.etapa_actual == V
    assert (t.estado_origen, t.estado_destino, t.registrado_por, t.nota) == (C, V, ana, "Visitó la casa")
    assert t.fecha_transicion is not None  # RN-33


@pytest.mark.parametrize(
    ("origen", "destino"),
    [(C, N), (C, CI), (V, C), (V, CI), (N, C), (N, V)],
)
def test_no_se_saltan_ni_se_retroceden_etapas(cliente, ana, origen, destino):
    s = solicitud(cliente, origen)
    with pytest.raises(services.TransicionInvalida, match="No se puede pasar"):
        services.registrar_etapa(s, destino, ana)
    assert not SeguimientoEtapa.objects.exists()
    s.refresh_from_db()
    assert s.etapa_actual == origen


@pytest.mark.parametrize("etapa", [C, V, N])
def test_cualquier_etapa_transitoria_puede_abandonarse(cliente, ana, etapa):
    s = solicitud(cliente, etapa)
    services.registrar_etapa(s, AB, ana)
    s.refresh_from_db()
    assert s.etapa_actual == AB


@pytest.mark.parametrize("final", [CI, AB])
@pytest.mark.parametrize("destino", [C, V, N, CI, AB])
def test_cierre_y_abandono_son_absorbentes(cliente, ana, final, destino):  # RN-31
    s = solicitud(cliente, final)
    with pytest.raises(services.TransicionInvalida, match="etapa final"):
        services.registrar_etapa(s, destino, ana)


@pytest.mark.parametrize("etapa", [C, V, N])
def test_seguir_en_la_misma_etapa_es_una_autotransicion(cliente, ana, etapa):  # ADR-002
    s = solicitud(cliente, etapa)
    t = services.registrar_etapa(s, etapa, ana, "no contestó")
    s.refresh_from_db()
    assert s.etapa_actual == etapa
    assert t.estado_origen == t.estado_destino == etapa
    assert services.es_autotransicion(t)


def test_cada_seguimiento_suma_un_paso_aunque_no_haya_avance(cliente, ana):
    s = solicitud(cliente)
    for destino in (C, C, V, V, N, CI):
        services.registrar_etapa(s, destino, ana)
    pares = list(
        SeguimientoEtapa.objects.order_by("id").values_list("estado_origen", "estado_destino")
    )
    assert pares == [(1, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 4)]


def test_una_solicitud_cancelada_no_admite_etapas(cliente, ana):
    s = solicitud(cliente, estado="CANCELADO")
    with pytest.raises(services.TransicionInvalida, match="cancelada"):
        services.registrar_etapa(s, V, ana)
    assert services.destinos_permitidos(s) == []


def test_una_etapa_invalida_se_rechaza(cliente, ana):
    with pytest.raises(services.TransicionInvalida, match="válida"):
        services.registrar_etapa(solicitud(cliente), 99, ana)
    with pytest.raises(services.TransicionInvalida, match="válida"):
        services.registrar_etapa(solicitud(cliente), "abc", ana)


def test_destinos_permitidos_siguen_la_tabla_rn30(cliente):
    assert services.destinos_permitidos(solicitud(cliente, C)) == [C, V, AB]
    assert services.destinos_permitidos(solicitud(cliente, V)) == [V, N, AB]
    assert services.destinos_permitidos(solicitud(cliente, N)) == [N, CI, AB]
    assert services.destinos_permitidos(solicitud(cliente, CI)) == []


def test_la_bd_tambien_impide_salir_de_un_estado_final(cliente):
    s = solicitud(cliente, CI)
    with pytest.raises(IntegrityError), transaction.atomic():
        SeguimientoEtapa.objects.create(solicitud=s, estado_origen=CI, estado_destino=C)


# --- Pantalla (W9) ------------------------------------------------------------------------
def test_requiere_sesion(client, cliente):
    r = client.get(reverse("seguimiento:detalle", args=[solicitud(cliente).pk]))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_el_detalle_ofrece_solo_las_etapas_permitidas(sesion, cliente):
    s = solicitud(cliente, V)
    html = sesion.get(reverse("seguimiento:detalle", args=[s.pk])).content.decode()
    assert "Seguir en Visita (sin avance)" in html
    assert "Pasar a Negociación" in html and "Marcar como Abandono" in html
    assert "Pasar a Cierre" not in html and "Pasar a Consulta" not in html


def test_el_detalle_de_una_solicitud_final_es_de_solo_lectura(sesion, cliente):
    s = solicitud(cliente, CI)
    html = sesion.get(reverse("seguimiento:detalle", args=[s.pk])).content.decode()
    assert "etapa final" in html and "Guardar seguimiento" not in html


def test_registrar_desde_la_pantalla_y_ver_el_historial(sesion, cliente):
    s = solicitud(cliente)
    r = sesion.post(
        reverse("seguimiento:etapa", args=[s.pk]), {"etapa": V.value, "nota": "Agendó visita"},
        follow=True,
    )
    html = r.content.decode()
    s.refresh_from_db()
    assert s.etapa_actual == V
    assert "Consulta → Visita" in html and "Agendó visita" in html and "ana" in html


def test_la_autotransicion_se_muestra_como_sin_avance(sesion, cliente):
    s = solicitud(cliente)
    html = sesion.post(
        reverse("seguimiento:etapa", args=[s.pk]), {"etapa": C.value, "nota": "no contestó"},
        follow=True,
    ).content.decode()
    assert "Consulta (sin avance)" in html and "no contestó" in html


def test_una_etapa_no_permitida_por_post_no_cambia_nada(sesion, cliente):
    s = solicitud(cliente)
    r = sesion.post(reverse("seguimiento:etapa", args=[s.pk]), {"etapa": N.value})
    assert r.status_code == 200  # vuelve al detalle con el error del formulario
    s.refresh_from_db()
    assert s.etapa_actual == C and not SeguimientoEtapa.objects.exists()


def test_la_etapa_es_obligatoria(sesion, cliente):
    s = solicitud(cliente)
    assert sesion.post(reverse("seguimiento:etapa", args=[s.pk]), {}).status_code == 200


def test_registrar_solo_acepta_post(sesion, cliente):
    assert sesion.get(reverse("seguimiento:etapa", args=[solicitud(cliente).pk])).status_code == 405


def test_la_cola_enlaza_al_detalle(sesion, cliente):
    s = solicitud(cliente)
    assert reverse("seguimiento:detalle", args=[s.pk]) in sesion.get(
        reverse("seguimiento:cola")
    ).content.decode()


# --- Cierre y estado del inmueble (RN-05, RF-43) ------------------------------------------
@pytest.mark.parametrize(
    ("operacion", "esperado"), [("VENTA", "VENDIDO"), ("ALQUILER", "ARRENDADO")]
)
def test_cierre_marcando_el_inmueble_lo_cierra_con_bitacora(sesion, cliente, operacion, esperado):
    casa = inmueble(operacion)
    s = solicitud(cliente, N, inmueble=casa)
    sesion.post(
        reverse("seguimiento:etapa", args=[s.pk]), {"etapa": CI.value, "marcar_inmueble": "on"}
    )
    casa.refresh_from_db()
    assert casa.estado == esperado
    assert HistorialEstadoInmueble.objects.filter(inmueble=casa, estado_nuevo=esperado).exists()


def test_cierre_sin_marcar_el_inmueble_solo_recuerda(sesion, cliente):
    casa = inmueble()
    s = solicitud(cliente, N, inmueble=casa)
    html = sesion.post(
        reverse("seguimiento:etapa", args=[s.pk]), {"etapa": CI.value}, follow=True
    ).content.decode()
    casa.refresh_from_db()
    assert casa.estado == "DISPONIBLE" and "Recuerde actualizar" in html


def test_cierre_sin_inmueble_no_ofrece_marcar(sesion, cliente):
    s = solicitud(cliente, N)
    html = sesion.get(reverse("seguimiento:detalle", args=[s.pk])).content.decode()
    assert "marcar_inmueble" not in html
    sesion.post(reverse("seguimiento:etapa", args=[s.pk]), {"etapa": CI.value})
    s.refresh_from_db()
    assert s.etapa_actual == CI
