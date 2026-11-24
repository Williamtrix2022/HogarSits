"""Panel de análisis: datos, textos y pantalla (#38; HU-07 a HU-09, RF-50 a RF-57, RF-59)."""

import json
import re
from datetime import date, datetime, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.agenda import disponibilidad
from apps.agenda.models import HorarioAsesor, Visita
from apps.analitica import analisis, datos, graficas, textos
from apps.analitica.services import colas, markov, poisson
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol
from apps.seguimiento.models import SeguimientoEtapa

User = get_user_model()

pytestmark = pytest.mark.django_db

LUNES = date(2026, 3, 2)
README_P = (
    (0.20, 0.50, 0.00, 0.00, 0.30),
    (0.00, 0.15, 0.45, 0.00, 0.40),
    (0.00, 0.00, 0.20, 0.55, 0.25),
    (0.00, 0.00, 0.00, 1.00, 0.00),
    (0.00, 0.00, 0.00, 0.00, 1.00),
)


def a(hora, minuto=0, dia=LUNES):
    return timezone.make_aware(datetime.combine(dia, time(hora, minuto)))


@pytest.fixture
def jefe():
    u = User.objects.create_user("jefe", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ADMIN)
    return u


@pytest.fixture
def admin_client(client, jefe):
    client.force_login(jefe)
    return client


@pytest.fixture
def simulados(db):
    """60 días de datos simulados con parámetros conocidos: 12 clientes/día, servicio 25 min."""
    call_command(
        "seed_datos_simulados", "--dias", "60", "--semilla", "7", "--clientes-por-dia", "12",
        "--servicio-min", "25", "--asesores", "3",
    )


# --- Textos en lenguaje de negocio (RF-59), sin BD ----------------------------------------
@pytest.mark.parametrize(
    ("valor", "dec", "esperado"), [(2.3989, 1, "2,4"), (0.2275, 2, "0,23"), (20, 0, "20"), (1.0, 1, "1,0")]
)
def test_numeros_con_coma_decimal(valor, dec, esperado):
    assert textos.num(valor, dec) == esperado


@pytest.mark.parametrize(
    ("horas", "esperado"),
    [(0.001, "menos de 1 minuto"), (1 / 60, "unos 1 minuto"), (29 / 60, "unos 29 minutos"),
     (1.0, "1 h"), (1.5, "1 h 30 min")],
)
def test_duraciones_dichas_como_una_persona(horas, esperado):
    assert textos.duracion(horas) == esperado


def test_frase_de_cierre_con_la_matriz_del_readme():
    frase = textos.frase_cierre(markov.analizar_absorcion(README_P))
    assert "De cada 10 clientes que consultan, unos 2 terminan cerrando y 8 abandonan" in frase
    assert "unos 2,4 seguimientos" in frase  # «pasos» = seguimientos (ADR-002)


def test_frases_por_etapa_coinciden_con_el_wireframe_w12():
    absorcion = markov.analizar_absorcion(README_P)
    assert textos.frases_por_etapa(absorcion) == [
        "Consulta → cierre: 23 %", "Visita → cierre: 36 %", "Negociación → cierre: 69 %",
    ]


def test_frase_de_esperas_como_en_el_wireframe_w11():
    lam, mu = 20 / 12, 60 / 45
    dos = textos.frase_colas(colas.mmc(lam, mu, 2), 2)
    tres = textos.frase_colas(colas.mmc(lam, mu, 3), 3)
    assert "Con 2 asesores disponibles" in dos and "unos 29 minutos" in dos
    assert "alrededor de 5 de cada 10 clientes" in dos
    assert "unos 4 minutos" in tres
    rec = textos.frase_recomendacion(3, 20, 2)
    assert "al menos 3 asesores" in rec and "Hoy hay 2 asesores." in rec
    assert "Hoy hay 1 asesor." in textos.frase_recomendacion(3, 20, 1)


def test_frase_de_inestabilidad_no_da_cifras():
    frase = textos.frase_colas(colas.mmc(3, 1, 2), 2)
    assert "crecería sin límite" in frase and "minutos" not in frase


def test_las_frases_sin_datos_lo_dicen():
    assert "Todavía no hay llegadas" in textos.frase_demanda(None, None)
    assert "No hay datos suficientes" in textos.frase_colas(None, None)
    assert "Todavía no hay datos suficientes" in textos.frase_cierre(None)
    assert textos.frases_por_etapa(None) == []


def test_las_frases_de_negocio_no_usan_jerga_suelta():
    absorcion = markov.analizar_absorcion(README_P)
    frases = [textos.frase_cierre(absorcion), textos.frase_colas(colas.mmc(1, 2, 1), 1)]
    for f in frases:
        assert not re.search(r"[λμρ]|P\(|Wq|Lq", f), f


# --- c efectivo en bloque = c efectivo por franja ------------------------------------------
def test_el_calculo_en_bloque_coincide_con_el_de_una_franja(db, asesor, otro_asesor, solicitud,
                                                            inmueble, otro_inmueble):
    for u in (asesor, otro_asesor):
        for dia in range(6):
            HorarioAsesor.objects.create(asesor=u, dia_semana=dia, hora_inicio=time(8), hora_fin=time(18))
    HorarioAsesor.objects.filter(asesor=otro_asesor, dia_semana=0).delete()
    HorarioAsesor.objects.create(asesor=otro_asesor, dia_semana=0, hora_inicio=time(8), hora_fin=time(12))
    HorarioAsesor.objects.create(asesor=otro_asesor, dia_semana=0, hora_inicio=time(14), hora_fin=time(18))
    Visita.objects.create(solicitud=solicitud, inmueble=inmueble, asesor=asesor,
                          inicio=a(9, 30), fin=a(10, 30))
    Visita.objects.create(solicitud=solicitud, inmueble=otro_inmueble, asesor=otro_asesor,
                          inicio=a(14), fin=a(16), estado="REALIZADA")
    Visita.objects.create(solicitud=solicitud, inmueble=inmueble, asesor=asesor,
                          inicio=a(11), fin=a(12), estado="CANCELADA")
    franjas = [(LUNES, h) for h in range(7, 19)] + [(LUNES + timedelta(days=1), h) for h in range(8, 18)]
    en_bloque = disponibilidad.c_efectivo_por_hora(franjas)
    for dia, hora in franjas:
        una = disponibilidad.disponibilidad(a(hora, dia=dia), a(hora, dia=dia) + timedelta(hours=1))
        assert en_bloque[(dia, hora)] == una.c, (dia, hora)


def test_c_efectivo_en_bloque_sin_franjas():
    assert disponibilidad.c_efectivo_por_hora([]) == {}


# --- Capa de datos: qué dato cuenta -------------------------------------------------------
def test_las_llegadas_incluyen_las_canceladas(db, solicitud):
    solicitud.estado = "CANCELADO"
    solicitud.save(update_fields=["estado"])
    hoy = timezone.localdate()
    assert len(datos.llegadas(hoy - timedelta(days=1), hoy + timedelta(days=1))) == 1


def test_mu_solo_usa_finalizadas_con_inicio_y_fin(db, solicitud, cliente):
    """RN-22: las canceladas y las que siguen en curso no aportan a μ."""
    from apps.clientes.models import Cliente
    from apps.seguimiento.models import SolicitudAtencion

    base = timezone.now() - timedelta(hours=3)
    SolicitudAtencion.objects.filter(pk=solicitud.pk).update(
        timestamp_llegada=base, timestamp_inicio_atencion=base + timedelta(minutes=10),
        timestamp_fin_atencion=base + timedelta(minutes=40), estado="FINALIZADO",
    )
    otra = Cliente.objects.create(nombre="B", correo="b@example.com", telefono="3002")
    SolicitudAtencion.objects.create(cliente=otra, tipo_interes="COMPRA", estado="CANCELADO",
                                     timestamp_llegada=base)
    ahora = timezone.localdate()
    duraciones = datos.duraciones_de_servicio_en_horas(ahora - timedelta(days=1), ahora + timedelta(days=1))
    assert duraciones == [pytest.approx(0.5)]  # solo la finalizada: 30 min


def test_las_transiciones_incluyen_las_autotransiciones(db, solicitud):
    SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=1, estado_destino=1)
    SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=1, estado_destino=2)
    hoy = timezone.localdate()
    assert sorted(datos.transiciones(hoy, hoy)) == [(1, 1), (1, 2)]


def test_periodo_con_datos_y_rango_por_defecto(db, solicitud):
    primero, ultimo = datos.periodo_con_datos()
    assert primero == ultimo == timezone.localdate()
    desde, hasta = analisis.rango_por_defecto(30)
    assert hasta == ultimo and desde == ultimo - timedelta(days=0)  # un solo día de datos


def test_rango_por_defecto_sin_datos_es_el_mes_actual(db):
    desde, hasta = analisis.rango_por_defecto(30)
    assert hasta == date.today() and (hasta - desde).days == 29


def test_horario_de_atencion_por_defecto_y_desde_los_turnos(db, asesor):
    assert datos.horario_de_atencion()[:2] == (8, 18)
    HorarioAsesor.objects.create(asesor=asesor, dia_semana=1, hora_inicio=time(7), hora_fin=time(19, 30))
    assert datos.horario_de_atencion() == (7, 20, (1,))  # 19:30 → la hora 19 cuenta: cierre 20


# --- De los datos simulados al análisis: se recuperan los parámetros ----------------------
def test_el_analisis_recupera_los_parametros_de_la_simulacion(simulados):
    desde, hasta = analisis.rango_por_defecto(60)
    r = analisis.analizar_periodo(desde, hasta)
    assert r.hay_simulados and any("simulados" in w for w in r.advertencias)
    # λ ≈ 12 clientes por día laboral repartidos en 10 horas (lunes a sábado)
    assert r.lam_hora == pytest.approx(1.2, rel=0.2)
    assert r.servicio_medio_min == pytest.approx(25, rel=0.15)  # se simuló servicio medio de 25 min
    assert r.mu_hora == pytest.approx(60 / 25, rel=0.15)
    assert r.c_promedio is not None and 1 <= r.c_promedio <= 3  # 3 asesores menos los de visita
    assert r.franja_pico.hora in (9, 10, 11, 15, 16, 17)  # picos de mañana y tarde
    assert r.cola is not None and r.cola.estable and r.cola_pico is not None
    assert r.c_recomendado is not None and r.tabla_c
    absorcion = r.markov.absorcion
    assert absorcion is not None
    assert absorcion.p_cierre[0] == pytest.approx(0.2275, abs=0.06)  # la matriz del README
    assert absorcion.pasos[0] == pytest.approx(2.4, abs=0.5)


def test_el_resumen_coincide_con_llamar_directo_a_los_servicios(simulados):
    """El ensamblado no debe alterar los números de los servicios."""
    desde, hasta = analisis.rango_por_defecto(60)
    r = analisis.analizar_periodo(desde, hasta)
    esperado = markov.analizar(datos.transiciones(desde, hasta)).absorcion
    assert r.markov.absorcion.p_cierre == esperado.p_cierre
    llegadas = datos.llegadas(desde, hasta)
    conteos = poisson.conteos_por_hora(llegadas, desde, hasta, r.apertura, r.cierre, r.dias_laborales)
    assert r.n_llegadas == sum(conteos.values())
    assert r.lam_hora == pytest.approx(sum(conteos.values()) / len(conteos))


def test_un_umbral_mas_estricto_pide_mas_asesores(simulados):
    desde, hasta = analisis.rango_por_defecto(60)
    laxo = analisis.analizar_periodo(desde, hasta, umbral_min=60)
    estricto = analisis.analizar_periodo(desde, hasta, umbral_min=1)
    assert estricto.c_recomendado >= laxo.c_recomendado


def test_sin_horarios_no_se_inventa_el_numero_de_asesores(db, solicitud):
    r = analisis.analizar_periodo(*analisis.rango_por_defecto())
    assert r.c_promedio is None and r.cola is None
    assert any("No hay horarios de asesores cargados" in w for w in r.advertencias)


def test_desde_posterior_a_hasta_es_un_error(db):
    with pytest.raises(ValueError):
        analisis.analizar_periodo(date(2026, 3, 5), date(2026, 3, 1))


def test_sin_datos_no_hay_nada_que_mostrar(db):
    r = analisis.analizar_periodo(date(2026, 1, 1), date(2026, 1, 31))
    assert not r.hay_datos and r.cola is None and r.markov.absorcion is None


# --- Datos para las gráficas ---------------------------------------------------------------
def test_las_graficas_tienen_la_forma_que_espera_el_javascript(simulados):
    r = analisis.analizar_periodo(*analisis.rango_por_defecto(60))
    g = graficas.construir(r)
    assert set(g) == {"demanda", "ajuste", "colas", "cierre"}
    assert len(g["demanda"]["horas"]) == len(g["demanda"]["lam"]) == len(g["demanda"]["suficiente"])
    assert len(g["ajuste"]["ks"]) == len(g["ajuste"]["observada"]) == len(g["ajuste"]["esperada"])
    assert g["cierre"]["etapas"] == ["Consulta", "Visita", "Negociación"]
    for c, w in zip(g["cierre"]["cierre"], g["cierre"]["abandono"], strict=True):
        assert c + w == pytest.approx(100, abs=0.2)
    json.dumps(g)  # tiene que ser serializable


def test_las_graficas_con_carga_inestable_dejan_huecos_no_numeros(simulados):
    r = analisis.analizar_periodo(*analisis.rango_por_defecto(60))
    g = graficas.construir(r)
    inestables = [q for q in r.tabla_c if not q.estable]
    huecos = [w for w in g["colas"]["wq_min"] if w is None]
    assert len(huecos) == len(inestables)


# --- Pantalla -----------------------------------------------------------------------------
def test_un_anonimo_va_al_login(client):
    r = client.get(reverse("analitica:inicio"))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_un_asesor_no_entra_al_analisis(client, db):
    u = User.objects.create_user("asesor9", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    client.force_login(u)
    assert client.get(reverse("analitica:inicio")).status_code == 403


def test_el_menu_del_administrador_muestra_analisis(admin_client):
    assert reverse("analitica:inicio") in admin_client.get(reverse("cuentas:inicio")).content.decode()


def test_sin_datos_la_pantalla_invita_a_generar_datos(admin_client):
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert "No hay datos en este periodo" in html and "datos-graficas" in html


def test_la_pantalla_muestra_las_tres_secciones_con_frases_de_negocio(admin_client, simulados):
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    for texto in ("¿Cuándo llegan los clientes?", "Asesores y esperas", "Probabilidad de cierre",
                  "De cada 10 clientes que consultan", "disponibles, un cliente espera",
                  "Los clientes llegan sobre todo entre las"):
        assert texto in html, texto
    for canvas in ("graf-demanda", "graf-ajuste", "graf-colas", "graf-cierre"):
        assert f'id="{canvas}"' in html
    assert 'role="img"' in html and "chart.umd.min.js" in html and "analisis.js" in html


def test_la_pantalla_avisa_que_hay_datos_simulados(admin_client, simulados):
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert "incluye datos simulados" in html


def test_los_datos_de_las_graficas_son_json_valido(admin_client, simulados):
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    m = re.search(r'<script id="datos-graficas" type="application/json">(.*?)</script>', html, re.S)
    assert m and set(json.loads(m.group(1))) == {"demanda", "ajuste", "colas", "cierre"}


def test_el_detalle_tecnico_trae_las_tablas_equivalentes(admin_client, simulados):
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert html.count("<details") == 3 and "Matriz de transición P estimada" in html
    assert "λ por hora del día" in html


def test_el_filtro_de_fechas_cambia_el_periodo(admin_client, simulados):
    desde, hasta = analisis.rango_por_defecto(60)
    a_ = admin_client.get(reverse("analitica:inicio"), {
        "desde": desde.isoformat(), "hasta": hasta.isoformat(), "espera_max": 20}).content.decode()
    b_ = admin_client.get(reverse("analitica:inicio"), {
        "desde": desde.isoformat(), "hasta": (desde + timedelta(days=6)).isoformat(),
        "espera_max": 20}).content.decode()
    n_a = int(re.search(r"(\d+) llegadas dentro", a_).group(1))
    n_b = int(re.search(r"(\d+) llegadas dentro", b_).group(1))
    assert n_b < n_a


@pytest.mark.parametrize(
    "params",
    [{"desde": "2026-03-10", "hasta": "2026-03-01", "espera_max": 20},   # desde > hasta
     {"desde": "2025-01-01", "hasta": "2026-12-31", "espera_max": 20},   # más de un año
     {"desde": "no", "hasta": "2026-03-01", "espera_max": 20},           # fecha inválida
     {"desde": "2026-03-01", "hasta": "2026-03-10", "espera_max": 0},    # espera < 1
     {"desde": "2026-03-01", "hasta": "2026-03-10", "espera_max": 999}], # espera > 240
)
def test_un_filtro_invalido_muestra_el_error_y_no_rompe(admin_client, simulados, params):
    r = admin_client.get(reverse("analitica:inicio"), params)
    assert r.status_code == 200 and "error" in r.content.decode().lower()


def test_el_umbral_de_espera_se_refleja_en_la_recomendacion(admin_client, simulados):
    desde, hasta = analisis.rango_por_defecto(60)
    html = admin_client.get(reverse("analitica:inicio"), {
        "desde": desde.isoformat(), "hasta": hasta.isoformat(), "espera_max": 5}).content.decode()
    assert "no pase de 5 minutos" in html


@pytest.mark.parametrize(
    ("p_espera", "esperado"),
    [(0.04, "casi ningún cliente"), (0.1, "alrededor de 1 de cada 10 clientes"),
     (0.5, "alrededor de 5 de cada 10 clientes"), (0.97, "casi todos los clientes")],
)
def test_de_cada_10_no_dice_unos_1_ni_numeros_raros(p_espera, esperado):
    assert textos._de_cada_10(p_espera) == esperado


def test_la_frase_con_un_solo_asesor_va_en_singular():
    frase = textos.frase_colas(colas.mmc(1, 2, 1), 1)
    assert "Con 1 asesor disponible," in frase and "unos 1" not in frase
