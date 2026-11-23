"""Horario semanal de asesores y asesores disponibles por franja (#53, RF-36, HU-09)."""

from datetime import date, datetime, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.agenda import disponibilidad
from apps.agenda.forms_horario import horas_semana
from apps.agenda.models import HorarioAsesor, Visita
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol

User = get_user_model()

pytestmark = pytest.mark.django_db

LUNES = date(2026, 3, 2)  # un lunes


def a(hora, minuto=0, dia=LUNES):
    return timezone.make_aware(datetime.combine(dia, time(hora, minuto)))


def turno(asesor, dia_semana=0, ini=(8, 0), fin=(12, 0)):
    return HorarioAsesor.objects.create(
        asesor=asesor, dia_semana=dia_semana, hora_inicio=time(*ini), hora_fin=time(*fin)
    )


@pytest.fixture
def jefe():
    u = User.objects.create_user("jefe", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ADMIN)
    return u


@pytest.fixture
def con_rol(asesor):
    asignar_rol(asesor, ROL_ASESOR)
    return asesor


@pytest.fixture
def admin_client(client, jefe):
    client.force_login(jefe)
    return client


def visita(solicitud, inmueble, asesor, ini, fin, estado="PROGRAMADA"):
    return Visita.objects.create(
        solicitud=solicitud, inmueble=inmueble, asesor=asesor, inicio=ini, fin=fin, estado=estado
    )


# --- c efectivo: turno menos visitas ------------------------------------------------------
def test_con_turno_y_sin_visitas_esta_disponible(asesor):
    turno(asesor)
    d = disponibilidad.disponibilidad(a(9), a(10))
    assert d.c == 1 and d.disponibles == [asesor] and d.en_visita == []


def test_el_turno_debe_cubrir_toda_la_franja(asesor):
    turno(asesor, ini=(8, 0), fin=(12, 0))
    assert disponibilidad.disponibilidad(a(11, 30), a(12, 30)).c == 0  # se pasa del turno
    assert disponibilidad.disponibilidad(a(7, 30), a(8, 30)).c == 0  # empieza antes del turno
    assert disponibilidad.disponibilidad(a(11), a(12)).c == 1  # termina justo con el turno


def test_una_visita_saca_al_asesor_de_la_oficina(asesor, solicitud, inmueble):
    turno(asesor)
    visita(solicitud, inmueble, asesor, a(9, 30), a(10, 30))
    d = disponibilidad.disponibilidad(a(9), a(10))
    assert d.c == 0 and d.en_visita == [asesor] and d.con_turno == [asesor]


def test_una_visita_contigua_no_ocupa_la_franja(asesor, solicitud, inmueble):
    turno(asesor)
    visita(solicitud, inmueble, asesor, a(10), a(11))
    assert disponibilidad.disponibilidad(a(9), a(10)).c == 1  # la visita empieza cuando termina


def test_las_canceladas_no_ocupan_pero_las_realizadas_si(
    asesor, otro_asesor, solicitud, inmueble, otro_inmueble
):
    turno(asesor)
    turno(otro_asesor)
    visita(solicitud, inmueble, asesor, a(9), a(10), estado="CANCELADA")
    visita(solicitud, otro_inmueble, otro_asesor, a(9), a(10), estado="REALIZADA")
    d = disponibilidad.disponibilidad(a(9), a(10))
    assert d.disponibles == [asesor] and d.en_visita == [otro_asesor]


def test_la_visita_de_otro_asesor_no_me_ocupa(asesor, otro_asesor, solicitud, inmueble):
    turno(asesor)
    turno(otro_asesor)
    visita(solicitud, inmueble, otro_asesor, a(9), a(10))
    d = disponibilidad.disponibilidad(a(9), a(10))
    assert d.c == 1 and d.disponibles == [asesor]


def test_otro_dia_de_la_semana_no_cuenta(asesor):
    turno(asesor, dia_semana=1)  # martes
    assert disponibilidad.disponibilidad(a(9), a(10)).c == 0  # lunes


def test_un_asesor_inactivo_no_cuenta(asesor):
    turno(asesor)
    asesor.is_active = False
    asesor.save()
    assert disponibilidad.disponibilidad(a(9), a(10)).c == 0


def test_dos_asesores_suman(asesor, otro_asesor):
    turno(asesor)
    turno(otro_asesor)
    assert disponibilidad.disponibilidad(a(9), a(10)).c == 2


# --- Por día ------------------------------------------------------------------------------
def test_el_dia_va_del_primer_turno_al_ultimo_en_franjas_de_una_hora(asesor):
    turno(asesor, ini=(8, 0), fin=(10, 0))
    turno(asesor, ini=(14, 0), fin=(16, 0))
    franjas = disponibilidad.disponibilidad_del_dia(LUNES)
    horas = [f.inicio.astimezone().hour for f in franjas]
    assert len(franjas) == 8 and [f.c for f in franjas] == [1, 1, 0, 0, 0, 0, 1, 1]
    assert horas[0] == franjas[0].inicio.astimezone().hour


def test_un_dia_sin_turnos_no_tiene_franjas():
    assert disponibilidad.disponibilidad_del_dia(LUNES) == []


def test_el_dia_descuenta_las_visitas(asesor, otro_asesor, solicitud, inmueble):
    turno(asesor, ini=(8, 0), fin=(10, 0))
    turno(otro_asesor, ini=(8, 0), fin=(10, 0))
    visita(solicitud, inmueble, asesor, a(8), a(9))
    assert [f.c for f in disponibilidad.disponibilidad_del_dia(LUNES)] == [1, 2]


def test_asesores_programables_incluye_asesores_y_a_quien_ya_tiene_turnos(
    con_rol, otro_asesor, jefe
):
    assert set(disponibilidad.asesores_programables()) == {con_rol}
    turno(otro_asesor)  # sin rol, pero con turnos (p. ej. los asesores simulados)
    assert set(disponibilidad.asesores_programables()) == {con_rol, otro_asesor}


def test_horas_semana():
    class T:  # solo necesita las horas
        def __init__(self, i, f):
            self.hora_inicio, self.hora_fin = time(*i), time(*f)

    assert horas_semana([T((8, 0), (12, 0)), T((14, 0), (17, 30))]) == 7.5


# --- Pantallas (solo administrador) -------------------------------------------------------
def test_un_asesor_no_entra_a_los_horarios(client, con_rol):
    client.force_login(con_rol)
    for nombre, args in (
        ("horarios:lista", []),
        ("horarios:disponibilidad", []),
        ("horarios:asesor", [con_rol.pk]),
    ):
        assert client.get(reverse(nombre, args=args)).status_code == 403


def test_un_anonimo_va_al_login(client):
    r = client.get(reverse("horarios:lista"))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_la_lista_muestra_asesores_con_sus_horas(admin_client, con_rol):
    turno(con_rol, ini=(8, 0), fin=(12, 0))
    html = admin_client.get(reverse("horarios:lista")).content.decode()
    assert con_rol.username in html
    assert '<td class="num">4,0</td>' in html  # 4 h; coma decimal de es-CO


def test_agregar_un_turno_a_varios_dias(admin_client, con_rol):
    r = admin_client.post(
        reverse("horarios:asesor", args=[con_rol.pk]),
        {"dias": ["0", "1", "2"], "hora_inicio": "08:00", "hora_fin": "12:00"},
    )
    assert r.status_code == 302
    assert HorarioAsesor.objects.filter(asesor=con_rol).count() == 3


def test_un_turno_que_se_cruza_se_rechaza_con_un_mensaje_claro(admin_client, con_rol):
    turno(con_rol, ini=(8, 0), fin=(12, 0))
    r = admin_client.post(
        reverse("horarios:asesor", args=[con_rol.pk]),
        {"dias": ["0"], "hora_inicio": "11:00", "hora_fin": "13:00"},
    )
    assert r.status_code == 200
    assert "se cruza con este" in r.content.decode()
    assert HorarioAsesor.objects.count() == 1


def test_turnos_contiguos_si_se_permiten(admin_client, con_rol):
    turno(con_rol, ini=(8, 0), fin=(12, 0))
    admin_client.post(
        reverse("horarios:asesor", args=[con_rol.pk]),
        {"dias": ["0"], "hora_inicio": "12:00", "hora_fin": "14:00"},
    )
    assert HorarioAsesor.objects.count() == 2


@pytest.mark.parametrize(
    "datos",
    [
        {"dias": ["0"], "hora_inicio": "12:00", "hora_fin": "08:00"},
        {"dias": ["0"], "hora_inicio": "10:00", "hora_fin": "10:00"},
        {"dias": [], "hora_inicio": "08:00", "hora_fin": "12:00"},
        {"dias": ["0"], "hora_inicio": "", "hora_fin": "12:00"},
        {"dias": ["0"], "hora_inicio": "no", "hora_fin": "12:00"},
    ],
)
def test_datos_invalidos_no_guardan(admin_client, con_rol, datos):
    r = admin_client.post(reverse("horarios:asesor", args=[con_rol.pk]), datos)
    assert r.status_code == 200 and not HorarioAsesor.objects.exists()


def test_quitar_un_turno(admin_client, con_rol):
    t = turno(con_rol)
    r = admin_client.post(reverse("horarios:borrar", args=[t.pk]))
    assert r.status_code == 302 and not HorarioAsesor.objects.exists()


def test_quitar_solo_acepta_post(admin_client, con_rol):
    t = turno(con_rol)
    assert admin_client.get(reverse("horarios:borrar", args=[t.pk])).status_code == 405


def test_un_asesor_no_puede_quitar_turnos(client, con_rol):
    t = turno(con_rol)
    client.force_login(con_rol)
    assert client.post(reverse("horarios:borrar", args=[t.pk])).status_code == 403
    assert HorarioAsesor.objects.count() == 1


def test_un_usuario_que_no_es_asesor_da_404(admin_client, jefe):
    assert admin_client.get(reverse("horarios:asesor", args=[jefe.pk])).status_code == 404


def test_la_pantalla_de_disponibilidad_muestra_las_franjas(
    admin_client, con_rol, solicitud, inmueble
):
    turno(con_rol, ini=(8, 0), fin=(10, 0))
    visita(solicitud, inmueble, con_rol, a(8), a(9))
    html = admin_client.get(reverse("horarios:disponibilidad"), {"fecha": LUNES.isoformat()}
                            ).content.decode()
    assert "08:00–09:00" in html and "09:00–10:00" in html
    assert "Promedio del día: 0,5" in html  # franjas con c = 0 y c = 1


def test_disponibilidad_sin_turnos_o_con_fecha_invalida(admin_client):
    html = admin_client.get(reverse("horarios:disponibilidad"), {"fecha": LUNES.isoformat()}
                            ).content.decode()
    assert "Nadie tiene turno ese día" in html
    assert admin_client.get(reverse("horarios:disponibilidad"), {"fecha": "x"}).status_code == 200


def test_la_lista_de_usuarios_enlaza_a_los_horarios(admin_client):
    html = admin_client.get(reverse("cuentas:usuarios")).content.decode()
    assert reverse("horarios:lista") in html


def test_una_franja_dura_una_hora_por_defecto(asesor):
    turno(asesor, ini=(8, 0), fin=(9, 0))
    (franja,) = disponibilidad.disponibilidad_del_dia(LUNES)
    assert franja.fin - franja.inicio == timedelta(hours=1)
