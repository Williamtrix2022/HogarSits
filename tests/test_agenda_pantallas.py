"""Agenda de visitas: servicio y pantallas (#30, HU-05, RF-30 a RF-34, RN-01 a RN-04, RN-06)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.agenda import services
from apps.agenda.models import Visita

pytestmark = pytest.mark.django_db


def futuro(horas=24, minutos=0):
    """Instante futuro redondeado al minuto (los formularios no envían segundos)."""
    return (timezone.now() + timedelta(hours=horas, minutes=minutos)).replace(second=0, microsecond=0)


@pytest.fixture
def sesion(client, asesor):
    client.force_login(asesor)
    return client


def datos(solicitud, inmueble, asesor, inicio, duracion=60, **extra):
    local = timezone.localtime(inicio)
    return {
        "solicitud": solicitud.pk, "inmueble": inmueble.pk, "asesor": asesor.pk,
        "inicio": local.strftime("%Y-%m-%dT%H:%M"), "duracion": duracion, **extra,
    }


# --- Servicio -----------------------------------------------------------------------------
def test_programar_crea_la_visita_programada(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 45)
    assert v.estado == "PROGRAMADA" and v.fin - v.inicio == timedelta(minutes=45)


def test_rechaza_cruce_de_asesor_e_indica_con_cual(solicitud, inmueble, otro_inmueble, asesor):
    services.programar(solicitud, inmueble, asesor, futuro(), 60)
    with pytest.raises(services.AgendaError, match="ya tiene una visita"):
        services.programar(solicitud, otro_inmueble, asesor, futuro(minutos=30), 60)


def test_rechaza_cruce_de_inmueble(solicitud, inmueble, asesor, otro_asesor):
    services.programar(solicitud, inmueble, asesor, futuro(), 60)
    with pytest.raises(services.AgendaError, match="ya tiene una visita"):
        services.programar(solicitud, inmueble, otro_asesor, futuro(minutos=59), 60)


def test_visitas_contiguas_estan_permitidas(solicitud, inmueble, asesor):
    services.programar(solicitud, inmueble, asesor, futuro(), 60)
    services.programar(solicitud, inmueble, asesor, futuro(minutos=60), 60)
    assert Visita.objects.count() == 2


def test_una_cancelada_libera_el_horario(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    services.cancelar(v)
    services.programar(solicitud, inmueble, asesor, futuro(minutos=30), 60)
    assert Visita.objects.exclude(estado="CANCELADA").count() == 1


def test_no_se_agenda_en_el_pasado(solicitud, inmueble, asesor):
    with pytest.raises(services.AgendaError, match="futuro"):
        services.programar(solicitud, inmueble, asesor, futuro(horas=-2), 60)


def test_no_se_agenda_un_inmueble_cerrado(solicitud, inmueble, asesor):
    inmueble.estado = "VENDIDO"
    inmueble.save()
    with pytest.raises(services.AgendaError, match="no se puede ofrecer"):
        services.programar(solicitud, inmueble, asesor, futuro(), 60)


@pytest.mark.parametrize("estado", ["FINALIZADO", "CANCELADO"])
def test_solo_para_solicitudes_abiertas(solicitud, inmueble, asesor, estado):
    llegada = solicitud.timestamp_llegada
    campos = {"estado": estado}
    if estado == "FINALIZADO":  # la BD exige llegada ≤ inicio ≤ fin
        campos.update(
            timestamp_inicio_atencion=llegada + timedelta(minutes=1),
            timestamp_fin_atencion=llegada + timedelta(minutes=5),
        )
    type(solicitud).objects.filter(pk=solicitud.pk).update(**campos)
    solicitud.refresh_from_db()
    with pytest.raises(services.AgendaError, match="abiertas"):
        services.programar(solicitud, inmueble, asesor, futuro(), 60)


def test_realizada_solo_si_ya_empezo(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    with pytest.raises(services.AgendaError, match="aún no ha empezado"):
        services.realizar(v)
    Visita.objects.filter(pk=v.pk).update(
        inicio=timezone.now() - timedelta(hours=2), fin=timezone.now() - timedelta(hours=1)
    )
    assert services.realizar(v).estado == "REALIZADA"


def test_reprogramar_cancela_la_original_y_enlaza_la_nueva(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    nueva = services.reprogramar(v, futuro(horas=48), 90)
    v.refresh_from_db()
    assert v.estado == "CANCELADA" and nueva.reemplaza_a == v and nueva.estado == "PROGRAMADA"


def test_reprogramar_con_conflicto_conserva_la_original(
    solicitud, inmueble, otro_inmueble, asesor
):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    services.programar(solicitud, otro_inmueble, asesor, futuro(horas=48), 60)
    with pytest.raises(services.AgendaError):
        services.reprogramar(v, futuro(horas=48, minutos=30), 60)
    v.refresh_from_db()
    assert v.estado == "PROGRAMADA"  # nada se perdió


def test_reprogramar_puede_correr_la_hora_sobre_si_misma(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    nueva = services.reprogramar(v, futuro(minutos=15), 60)  # se solapa solo con la original
    assert nueva.estado == "PROGRAMADA"


def test_no_se_cancela_dos_veces(solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    services.cancelar(v)
    with pytest.raises(services.AgendaError):
        services.cancelar(v)


# --- Pantallas ----------------------------------------------------------------------------
def test_requiere_sesion(client):
    r = client.get(reverse("agenda:semana"))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_agendar_desde_el_formulario(sesion, solicitud, inmueble, asesor):
    r = sesion.post(reverse("agenda:crear"), datos(solicitud, inmueble, asesor, futuro()))
    assert r.status_code == 302
    assert Visita.objects.get().asesor == asesor


def test_el_formulario_muestra_el_cruce_y_no_guarda(sesion, solicitud, inmueble, asesor):
    services.programar(solicitud, inmueble, asesor, futuro(), 60)
    r = sesion.post(
        reverse("agenda:crear"), datos(solicitud, inmueble, asesor, futuro(minutos=30))
    )
    assert r.status_code == 200
    assert "ya tiene una visita" in r.content.decode()
    assert Visita.objects.count() == 1


def test_el_formulario_exige_los_campos(sesion):
    r = sesion.post(reverse("agenda:crear"), {})
    assert r.status_code == 200 and not Visita.objects.exists()


def test_la_agenda_semanal_lista_las_visitas_de_la_semana(sesion, solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    fecha = timezone.localtime(v.inicio).date().isoformat()
    html = sesion.get(reverse("agenda:semana"), {"fecha": fecha}).content.decode()
    assert inmueble.titulo in html and "1 visita esta semana" in html


def test_la_agenda_filtra_por_asesor(sesion, solicitud, inmueble, asesor, otro_asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    fecha = timezone.localtime(v.inicio).date().isoformat()
    html = sesion.get(
        reverse("agenda:semana"), {"fecha": fecha, "asesor": otro_asesor.pk}
    ).content.decode()
    assert "0 visitas esta semana" in html


def test_una_fecha_invalida_cae_en_la_semana_actual(sesion):
    assert sesion.get(reverse("agenda:semana"), {"fecha": "no-es-fecha"}).status_code == 200


def test_cancelar_desde_la_pantalla(sesion, solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    sesion.post(reverse("agenda:cancelar", args=[v.pk]))
    v.refresh_from_db()
    assert v.estado == "CANCELADA"


def test_reprogramar_desde_la_pantalla(sesion, solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    r = sesion.post(
        reverse("agenda:reprogramar", args=[v.pk]),
        {"inicio": timezone.localtime(futuro(horas=72)).strftime("%Y-%m-%dT%H:%M"),
         "duracion": 60},
    )
    assert r.status_code == 302
    assert Visita.objects.filter(estado="PROGRAMADA", reemplaza_a=v).exists()


def test_reprogramar_muestra_el_formulario_con_la_duracion_actual(
    sesion, solicitud, inmueble, asesor
):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 90)
    assert sesion.get(reverse("agenda:reprogramar", args=[v.pk])).status_code == 200


def test_las_acciones_solo_aceptan_post(sesion, solicitud, inmueble, asesor):
    v = services.programar(solicitud, inmueble, asesor, futuro(), 60)
    assert sesion.get(reverse("agenda:cancelar", args=[v.pk])).status_code == 405


def test_el_menu_muestra_agenda(sesion):
    assert reverse("agenda:semana") in sesion.get(reverse("cuentas:inicio")).content.decode()
