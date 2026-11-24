"""Indicadores por asesor (#54, HU-13, RF-62)."""

import csv
import io
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.agenda.models import Visita
from apps.analitica import indicadores
from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion

User = get_user_model()
Estado = SolicitudAtencion.Estado

pytestmark = pytest.mark.django_db


@pytest.fixture
def hoy():
    return timezone.localdate()


@pytest.fixture
def periodo(hoy):
    return hoy - timedelta(days=10), hoy


def dia(hoy, atras, hora=10):
    """Un instante de hace `atras` días a la hora local indicada."""
    base = timezone.localtime(timezone.now()).replace(hour=hora, minute=0, second=0, microsecond=0)
    return base - timedelta(days=atras)


_n = {"c": 0}


def cliente():
    _n["c"] += 1
    return Cliente.objects.create(
        nombre=f"Cliente {_n['c']}", correo=f"c{_n['c']}-{timezone.now().timestamp()}@example.com",
        telefono="3001234567",
    )


def atencion(asesor, hoy, atras, minutos=None, estado=None, hora=10):
    """Una solicitud que el asesor empezó a atender; con `minutos`, terminada."""
    inicio = dia(hoy, atras, hora)
    campos = {"timestamp_llegada": inicio - timedelta(minutes=5), "timestamp_inicio_atencion": inicio}
    if minutos is not None:
        campos |= {"timestamp_fin_atencion": inicio + timedelta(minutes=minutos),
                   "estado": estado or Estado.FINALIZADO}
    else:
        campos["estado"] = estado or Estado.EN_ATENCION
    return SolicitudAtencion.objects.create(
        cliente=cliente(), asesor=asesor, tipo_interes="COMPRA", **campos
    )


def visita(solicitud, inmueble, asesor, hoy, atras, hora, estado="REALIZADA"):
    ini = dia(hoy, atras, hora)
    return Visita.objects.create(solicitud=solicitud, inmueble=inmueble, asesor=asesor,
                                 inicio=ini, fin=ini + timedelta(minutes=45), estado=estado)


def cierre(solicitud, hoy, atras):
    t = SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=3, estado_destino=4)
    SeguimientoEtapa.objects.filter(pk=t.pk).update(fecha_transicion=dia(hoy, atras))


@pytest.fixture
def escenario(hoy, asesor, otro_asesor, inmueble, otro_inmueble):
    """asesor1: 3 atendidas (20 y 40 min terminadas + 1 en curso), 2 visitas realizadas, 1 cierre.
    asesor2: 1 atendida (60 min). Y ruido que NO debe contar."""
    s1 = atencion(asesor, hoy, 3, 20)
    atencion(asesor, hoy, 4, 40)
    atencion(asesor, hoy, 2)  # en atención: cuenta como atendida, no para la media
    s4 = atencion(otro_asesor, hoy, 3, 60, hora=11)
    visita(s1, inmueble, asesor, hoy, 3, 12)
    visita(s1, otro_inmueble, asesor, hoy, 4, 12)
    cierre(s1, hoy, 2)
    # ruido
    visita(s1, inmueble, asesor, hoy, 5, 12, estado="CANCELADA")  # cancelada
    visita(s1, inmueble, asesor, hoy, 6, 12, estado="PROGRAMADA")  # no realizada
    visita(s1, inmueble, asesor, hoy, 40, 12)  # fuera del periodo
    atencion(asesor, hoy, 40, 15)  # fuera del periodo
    cierre(s4, hoy, 45)  # cierre fuera del periodo
    SolicitudAtencion.objects.create(  # sin asesor: no es de nadie
        cliente=cliente(), tipo_interes="COMPRA", estado=Estado.EN_ESPERA,
        timestamp_llegada=dia(hoy, 3))
    return asesor, otro_asesor


def fila(lista, usuario):
    return next(i for i in lista if i.asesor.pk == usuario.pk)


# --- Cálculo ------------------------------------------------------------------------------
def test_cuenta_atendidas_visitas_cierres_y_media(escenario, periodo):
    a1, a2 = escenario
    lista = indicadores.indicadores_por_asesor(*periodo)
    i1 = fila(lista, a1)
    assert (i1.atendidas, i1.visitas_realizadas, i1.cierres) == (3, 2, 1)
    assert i1.atencion_media_min == pytest.approx(30)  # (20 + 40) / 2; la que sigue en curso no cuenta
    assert i1.n_finalizadas == 2
    i2 = fila(lista, a2)
    assert (i2.atendidas, i2.visitas_realizadas, i2.cierres) == (1, 0, 0)
    assert i2.atencion_media_min == pytest.approx(60)


def test_las_visitas_canceladas_programadas_y_fuera_del_periodo_no_cuentan(escenario, periodo):
    a1, _ = escenario
    assert fila(indicadores.indicadores_por_asesor(*periodo), a1).visitas_realizadas == 2


def test_lo_de_fuera_del_periodo_no_entra(escenario, hoy):
    a1, _ = escenario
    antiguo = indicadores.indicadores_por_asesor(hoy - timedelta(days=50), hoy - timedelta(days=30))
    i1 = fila(antiguo, a1)
    assert (i1.atendidas, i1.visitas_realizadas, i1.cierres) == (1, 1, 0)
    assert i1.atencion_media_min == pytest.approx(15)


def test_una_solicitud_sin_asesor_no_se_atribuye_a_nadie(escenario, periodo):
    total = indicadores.totales(indicadores.indicadores_por_asesor(*periodo))
    assert total["atendidas"] == 4  # 3 de asesor1 + 1 de asesor2; la huérfana no suma


def test_con_un_asesor_solo_se_devuelve_el_suyo(escenario, periodo):
    a1, a2 = escenario
    lista = indicadores.indicadores_por_asesor(*periodo, asesor=a2)
    assert [i.asesor.pk for i in lista] == [a2.pk]


def test_un_asesor_sin_actividad_sale_con_ceros_y_media_vacia(db, periodo, asesor):
    (i,) = indicadores.indicadores_por_asesor(*periodo, asesor=asesor)
    assert (i.atendidas, i.visitas_realizadas, i.cierres, i.atencion_media_min) == (0, 0, 0, None)


def test_el_total_pondera_la_atencion_media_por_numero_de_atenciones(escenario, periodo):
    """asesor1: media 30 con 2 atenciones; asesor2: 60 con 1 → (30·2 + 60·1) / 3 = 40."""
    total = indicadores.totales(indicadores.indicadores_por_asesor(*periodo))
    assert total["atencion_media_min"] == pytest.approx(40)
    assert (total["visitas_realizadas"], total["cierres"]) == (2, 1)


def test_el_total_sin_atenciones_terminadas_no_inventa_media():
    assert indicadores.totales([])["atencion_media_min"] is None


def test_cada_cierre_cuenta_una_vez_por_solicitud(hoy, periodo, asesor):
    s = atencion(asesor, hoy, 2, 10)
    cierre(s, hoy, 2)
    cierre(s, hoy, 1)  # un registro duplicado no suma dos veces
    assert fila(indicadores.indicadores_por_asesor(*periodo), asesor).cierres == 1


# --- Pantalla y permisos (CA2: el asesor solo ve lo suyo) ----------------------------------
@pytest.fixture
def admin_client(client):
    u = User.objects.create_user("jefe", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ADMIN)
    client.force_login(u)
    return client


def entrar_como(client, usuario):
    asignar_rol(usuario, ROL_ASESOR)
    client.force_login(usuario)
    return client


def test_un_anonimo_va_al_login(client):
    r = client.get(reverse("analitica:asesores"))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_el_administrador_ve_a_todo_el_equipo_y_el_total(admin_client, escenario):
    a1, a2 = escenario
    html = admin_client.get(reverse("analitica:asesores")).content.decode()
    assert a1.username in html and a2.username in html
    assert "Equipo" in html and "Exportar CSV" in html and "Indicadores por asesor" in html


def test_un_asesor_ve_solo_su_fila(client, escenario):
    a1, a2 = escenario
    html = entrar_como(client, a1).get(reverse("analitica:asesores")).content.decode()
    assert a1.username in html and a2.username not in html
    assert "Mis indicadores" in html and "Solo usted ve estas cifras" in html
    assert "Exportar CSV" not in html and "Equipo" not in html


def test_un_asesor_no_puede_ver_a_otro_cambiando_la_url(client, escenario):
    a1, a2 = escenario
    html = entrar_como(client, a1).get(
        reverse("analitica:asesores"), {"asesor": a2.pk, "usuario": a2.pk}
    ).content.decode()
    assert a2.username not in html


def test_las_cifras_en_pantalla_coinciden_con_el_calculo(admin_client, escenario, periodo):
    html = admin_client.get(reverse("analitica:asesores"), {
        "desde": periodo[0].isoformat(), "hasta": periodo[1].isoformat()}).content.decode()
    assert "30 min" in html and "60 min" in html and "40 min" in html  # asesor1, asesor2 y equipo


def test_la_atencion_media_sin_terminadas_se_muestra_como_raya(client, hoy, periodo, asesor):
    atencion(asesor, hoy, 2)  # solo una en curso
    html = entrar_como(client, asesor).get(reverse("analitica:asesores")).content.decode()
    assert "—" in html and " min</td>" not in html


def test_un_filtro_invalido_muestra_el_error_y_no_rompe(admin_client, escenario):
    r = admin_client.get(reverse("analitica:asesores"), {"desde": "2026-03-10", "hasta": "2026-03-01"})
    assert r.status_code == 200 and "posterior" in r.content.decode()


def test_sin_actividad_la_pantalla_lo_dice(admin_client):
    html = admin_client.get(reverse("analitica:asesores")).content.decode()
    assert "No hay asesores con actividad" in html


def test_avisa_si_hay_datos_simulados(admin_client, hoy, asesor):
    sim = Cliente.objects.create(nombre="S", correo="s@sim.hogarsits.test", telefono="3")
    SolicitudAtencion.objects.create(cliente=sim, asesor=asesor, tipo_interes="COMPRA",
                                     timestamp_llegada=dia(hoy, 2))
    assert "incluye datos simulados" in admin_client.get(reverse("analitica:asesores")).content.decode()


def test_el_inicio_enlaza_a_los_indicadores_segun_el_rol(client, admin_client, asesor):
    assert "Indicadores por asesor" in admin_client.get(reverse("cuentas:inicio")).content.decode()
    html = entrar_como(client, asesor).get(reverse("cuentas:inicio")).content.decode()
    assert "Mis indicadores" in html


def test_el_panel_de_analisis_enlaza_a_los_indicadores(admin_client):
    assert reverse("analitica:asesores") in admin_client.get(reverse("analitica:inicio")).content.decode()


# --- Exportar CSV (solo administrador) ----------------------------------------------------
def leer(r):
    return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig")), delimiter=";"))


def test_exporta_los_indicadores_a_csv(admin_client, escenario, periodo):
    r = admin_client.get(reverse("analitica:exportar"), {
        "tabla": "asesores", "desde": periodo[0].isoformat(), "hasta": periodo[1].isoformat()})
    assert r.status_code == 200 and "hogarsits_asesores_" in r["Content-Disposition"]
    filas = leer(r)
    assert filas[0] == ["asesor", "solicitudes_atendidas", "visitas_realizadas", "cierres",
                        "atencion_media_min", "atenciones_finalizadas", "datos_simulados"]
    por_nombre = {f[0]: f for f in filas[1:]}
    f1 = next(f for n, f in por_nombre.items() if "asesor1" in n)
    assert f1[1:4] == ["3", "2", "1"] and f1[4] == "30" and f1[5] == "2"


def test_la_media_vacia_se_exporta_como_celda_vacia(admin_client, hoy, asesor):
    atencion(asesor, hoy, 2)
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "asesores"}))
    assert filas[1][4] == ""


def test_un_nombre_que_parece_formula_se_neutraliza_en_el_csv(admin_client, hoy):
    u = User.objects.create_user("x", password="x", first_name="=HYPERLINK(\"http://malo\")")
    atencion(u, hoy, 2, 10)
    filas = leer(admin_client.get(reverse("analitica:exportar"), {"tabla": "asesores"}))
    assert any(f[0].startswith("'=") for f in filas[1:])
    assert not any(f[0].startswith("=") for f in filas[1:])


def test_un_asesor_no_puede_exportar(client, escenario):
    a1, _ = escenario
    r = entrar_como(client, a1).get(reverse("analitica:exportar"), {"tabla": "asesores"})
    assert r.status_code == 403
