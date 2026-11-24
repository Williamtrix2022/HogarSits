"""Correcciones de la revisión independiente del panel (#42; hallazgos E1 a E3, R1 a R6, O1 a O3).

Cada prueba fija un hallazgo que el agente revisor señaló y que se verificó en el código.
"""

from datetime import datetime, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.agenda.models import HorarioAsesor, Visita
from apps.analitica import analisis, datos, textos
from apps.analitica.analisis import _redondear_c
from apps.analitica.services import colas, poisson
from apps.analitica.services.markov import Absorcion
from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ADMIN, asignar_rol
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion

User = get_user_model()

pytestmark = pytest.mark.django_db


def a(dia, hora, minuto=0):
    return timezone.make_aware(datetime.combine(dia, time(hora, minuto)))


@pytest.fixture
def admin_client(client):
    u = User.objects.create_user("jefe", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ADMIN)
    client.force_login(u)
    return client


_n = {"i": 0}


def cliente(correo=None):
    _n["i"] += 1
    return Cliente.objects.create(
        nombre=f"C{_n['i']}", correo=correo or f"rev{_n['i']}@example.com", telefono="3001234567"
    )


def atencion(dia, hora, minutos=30, asesor=None):
    """Una solicitud finalizada que llegó ese día a esa hora y duró `minutos`."""
    llegada = a(dia, hora)
    return SolicitudAtencion.objects.create(
        cliente=cliente(), asesor=asesor, tipo_interes="COMPRA", estado="FINALIZADO",
        timestamp_llegada=llegada, timestamp_inicio_atencion=llegada,
        timestamp_fin_atencion=llegada + timedelta(minutes=minutos),
    )


def lunes(n=0):
    """El lunes de hace `n` semanas contando desde la semana pasada (siempre en el pasado)."""
    hoy = timezone.localdate()
    return hoy - timedelta(days=hoy.weekday() + 7 * (n + 1))


# --- E1: la última clase es «k o más», no «= k» ----------------------------------------------
def test_la_ultima_clase_del_ajuste_se_rotula_k_o_mas():
    ajuste = poisson.ajuste_poisson([0, 1, 2, 2, 1, 0, 3, 5, 1, 2])
    assert ajuste.etiquetas == ("0", "1", "2", "3", "4", "5 o más")
    assert len(ajuste.etiquetas) == len(ajuste.ks)


def test_la_ultima_clase_es_la_cola_no_la_probabilidad_puntual():
    """Lo que el revisor midió: la esperada de la última clase es P(X ≥ k), mayor que P(X = k)."""
    ajuste = poisson.ajuste_poisson([0, 1, 2, 2, 1, 0, 3, 5, 1, 2])
    k = ajuste.ks[-1]
    assert ajuste.esperada[-1] > poisson.poisson_pmf(k, ajuste.lam)
    assert ajuste.esperada[-1] == pytest.approx(
        1 - sum(poisson.poisson_pmf(i, ajuste.lam) for i in range(k))
    )


def test_con_todo_en_cero_la_unica_clase_es_cero_o_mas():
    assert poisson.ajuste_poisson([0, 0, 0]).etiquetas == ("0 o más",)


def test_el_panel_la_grafica_y_el_csv_rotulan_la_cola(admin_client):
    for semana in range(8):  # suficientes lunes para tener ajuste
        for _ in range(3):
            atencion(lunes(semana), 10)
    HorarioAsesor.objects.create(asesor=User.objects.create_user("x", password="x"), dia_semana=0,
                                 hora_inicio=time(8), hora_fin=time(18))
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert " o más</td>" in html and "Poisson P(X = k)" not in html
    csv = admin_client.get(reverse("analitica:exportar"), {"tabla": "poisson"}).content.decode()
    assert " o más;" in csv


# --- E2: el redondeo de c no fuerza 1 y usa mitades hacia arriba ------------------------------
@pytest.mark.parametrize(
    ("promedio", "esperado"),
    [(None, None), (0.0, None), (0.2, None), (0.49, None), (0.5, 1), (0.99, 1),
     (1.49, 1), (1.5, 2), (1.8, 2), (2.5, 3), (3.5, 4)],
)
def test_redondear_c(promedio, esperado):
    assert _redondear_c(promedio) == esperado


def _asesor_con_turno(dia_semana=0, ini=8, fin=10):
    u = User.objects.create_user(f"as{_n['i']}", password="x")
    _n["i"] += 1
    HorarioAsesor.objects.create(asesor=u, dia_semana=dia_semana, hora_inicio=time(ini),
                                 hora_fin=time(fin))
    return u


def _inmueble_y_solicitud():
    from apps.inmuebles.models import Inmueble

    casa = Inmueble.objects.create(titulo="Casa", tipo_inmueble="CASA", operacion="VENTA",
                                   direccion="Cll 1", precio=100)
    return casa, atencion(lunes(0), 8)


def test_si_casi_nunca_hay_un_asesor_libre_no_se_inventan_esperas():
    """Un asesor que está en visita todas las horas de su turno: c̄ = 0 < 0,5."""
    asesor = _asesor_con_turno(0, 8, 10)
    casa, sol = _inmueble_y_solicitud()
    for semana in range(3):
        d = lunes(semana)
        Visita.objects.create(solicitud=sol, inmueble=casa, asesor=asesor, inicio=a(d, 8),
                              fin=a(d, 10), estado="REALIZADA")
        for _ in range(4):
            atencion(d, 8, asesor=asesor)
    r = analisis.analizar_periodo(lunes(2), lunes(0))
    assert r.c_promedio == 0 and r.c_usado is None and r.cola is None  # no finge que hay uno
    assert any("menos de medio asesor libre" in w for w in r.advertencias)


def test_entre_medio_y_un_asesor_se_calcula_como_uno_y_se_avisa_que_es_optimista():
    asesor = _asesor_con_turno(0, 8, 10)
    casa, sol = _inmueble_y_solicitud()
    for semana in range(3):
        d = lunes(semana)  # visita de 8 a 9: la hora 8 queda con c = 0 y la 9 con c = 1 → c̄ = 0,5
        Visita.objects.create(solicitud=sol, inmueble=casa, asesor=asesor, inicio=a(d, 8),
                              fin=a(d, 9), estado="REALIZADA")
        for _ in range(4):
            atencion(d, 9, asesor=asesor)
    r = analisis.analizar_periodo(lunes(2), lunes(0))
    assert r.c_promedio == pytest.approx(0.5) and r.c_usado == 1
    assert any("optimistas" in w for w in r.advertencias)


# --- E3: «Hoy hay N» era un promedio histórico ---------------------------------------------------
def test_la_recomendacion_no_dice_hoy_hay():
    texto = textos.frase_recomendacion(4, 20, 2)
    assert "Hoy hay" not in texto and "En la hora pico suele haber 2 asesores libres" in texto


def test_la_recomendacion_no_menciona_los_habituales_si_ya_alcanzan():
    assert "suele haber" not in textos.frase_recomendacion(2, 20, 3)


# --- R3: la hora pico con pocos datos no se presenta como firme ----------------------------------
def test_la_frase_de_demanda_avisa_si_la_hora_pico_tiene_pocos_datos():
    pico = poisson.Franja(None, 10, 5, 8, 1.6, suficiente=False)
    assert "pocos datos en esa hora" in textos.frase_demanda(pico, None)
    firme = poisson.Franja(None, 10, 50, 80, 1.6, suficiente=True)
    assert "pocos datos" not in textos.frase_demanda(firme, None)


def test_una_lambda_minuscula_no_sale_como_cero_coma_cero():
    pico = poisson.Franja(None, 10, 50, 1, 0.02, suficiente=True)
    assert "menos de 0,1 por hora" in textos.frase_demanda(pico, None)
    assert "0,0 por hora" not in textos.frase_demanda(pico, None)


# --- R4: la frase del χ² no dice más de lo que prueba ---------------------------------------------
def ajuste(rechaza, dispersion, probado=True):
    base = poisson.ajuste_poisson([1, 2, 1, 2, 3, 0, 1, 2, 1, 1, 2, 3, 1, 0, 2])
    from dataclasses import replace

    return replace(base, rechaza=rechaza, indice_dispersion=dispersion,
                   chi2=1.0 if probado else None)


def test_rechazo_con_dispersion_alta_habla_de_grupos():
    assert "en grupos" in textos.frase_ajuste(ajuste(True, 2.0))


def test_rechazo_con_dispersion_baja_no_habla_de_grupos():
    f = textos.frase_ajuste(ajuste(True, 0.5))
    assert "en grupos" not in f and "más regulares" in f


def test_no_rechazar_no_se_presenta_como_prueba_de_ajuste():
    f = textos.frase_ajuste(ajuste(False, 1.0))
    assert "No hay evidencia en contra" in f and "se comportan como llegadas al azar" not in f


def test_sin_prueba_se_dice_que_faltan_datos():
    assert "Faltan datos" in textos.frase_ajuste(ajuste(None, 1.0, probado=False))


# --- R5: los datos simulados también se detectan por las transiciones -----------------------------
def test_un_cliente_simulado_que_avanza_dentro_del_periodo_activa_el_aviso():
    sim = cliente("c1@sim.hogarsits.test")
    antes = a(lunes(5), 10)
    sol = SolicitudAtencion.objects.create(cliente=sim, tipo_interes="COMPRA", timestamp_llegada=antes)
    t = SeguimientoEtapa.objects.create(solicitud=sol, estado_origen=1, estado_destino=2)
    SeguimientoEtapa.objects.filter(pk=t.pk).update(fecha_transicion=a(lunes(0), 10))
    # el periodo no incluye la llegada, solo la transición
    assert datos.hay_simulados(lunes(1), lunes(0)) is True
    assert datos.hay_simulados(lunes(9), lunes(8)) is False


def test_los_clientes_reales_no_activan_el_aviso():
    sol = atencion(lunes(0), 10)
    SeguimientoEtapa.objects.create(solicitud=sol, estado_origen=1, estado_destino=2)
    assert datos.hay_simulados(lunes(1), timezone.localdate()) is False


# --- R6: la media de los indicadores y la de μ usan el mismo criterio ------------------------------
def test_una_atencion_de_duracion_cero_no_entra_en_ninguna_media():
    from apps.analitica import indicadores

    u = User.objects.create_user("asesor_r6", password="x")
    atencion(lunes(0), 9, minutos=40, asesor=u)
    atencion(lunes(0), 10, minutos=0, asesor=u)  # fin == inicio: permitido por la BD, pero inútil
    (fila,) = indicadores.indicadores_por_asesor(lunes(1), timezone.localdate(), asesor=u)
    assert fila.atendidas == 2  # sigue contando como atendida
    assert fila.atencion_media_min == pytest.approx(40) and fila.n_finalizadas == 1
    assert datos.duraciones_de_servicio_en_horas(lunes(1), timezone.localdate()) == [
        pytest.approx(40 / 60)
    ]


# --- O1: redondeos y extremos de las frases --------------------------------------------------------
@pytest.mark.parametrize(
    ("horas", "esperado"),
    [(1.008 / 60, "alrededor de 1 minuto"), (0.9999, "1 h"), (59.6 / 60, "1 h"),
     (1.5 / 60, "unos 2 minutos"), (2.5 / 60, "unos 3 minutos"), (1.0, "1 h"),
     (1 + 5 / 60, "1 h 5 min")],
)
def test_duraciones(horas, esperado):
    assert textos.duracion(horas) == esperado


@pytest.mark.parametrize(
    ("p", "esperado"),
    [(0.25, "unos 3 terminan cerrando y 7 abandonan"), (0.35, "unos 4 terminan cerrando y 6"),
     (0.97, "casi todos terminan cerrando"), (0.03, "casi ninguno termina cerrando")],
)
def test_frase_de_cierre_con_mitades_y_extremos(p, esperado):
    absorcion = Absorcion(N=((1, 0, 0),) * 3, p_cierre=(p, 0.5, 0.5), p_abandono=(1 - p, 0.5, 0.5),
                          pasos=(2.4, 1, 1))
    frase = textos.frase_cierre(absorcion)
    assert esperado in frase
    assert "unos 10" not in frase and "unos 0" not in frase  # los extremos no dicen «unos 0»


def test_de_cada_10_usa_mitades_hacia_arriba():
    assert textos._de_cada_10(0.25) == "alrededor de 3 de cada 10 clientes"
    assert textos._de_cada_10(0.45) == "alrededor de 5 de cada 10 clientes"


def test_frase_de_esperas_con_un_asesor_va_en_singular_tambien_cuando_es_inestable():
    assert "Con 1 asesor disponible la carga" in textos.frase_colas(colas.mmc(3, 1, 1), 1)


# --- O2: el CSV de colas se puede reproducir -------------------------------------------------------
def test_el_csv_de_colas_lleva_sus_parametros(admin_client):
    for semana in range(6):
        for _ in range(4):
            atencion(lunes(semana), 10)
    _asesor_con_turno(0, 8, 18)
    import csv
    import io

    r = admin_client.get(reverse("analitica:exportar"), {"tabla": "colas"})
    filas = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig")), delimiter=";"))
    enc = filas[0]
    for col in ("lambda_pico_clientes_hora", "mu_clientes_hora_por_asesor", "hora_pico",
                "umbral_espera_min"):
        assert col in enc
    assert filas[1][enc.index("hora_pico")] == "10:00" and filas[1][enc.index("umbral_espera_min")] == "20"


# --- O3: presentación ----------------------------------------------------------------------------
def test_sin_horarios_el_panel_igual_da_la_recomendacion_de_asesores(admin_client):
    """La recomendación solo necesita λ y μ: no debe ocultarse porque falten los horarios."""
    for semana in range(6):
        for _ in range(6):
            atencion(lunes(semana), 10, minutos=45)
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert "No hay horarios de asesores cargados" in html
    assert "se necesitan" in html and "graf-colas" in html


def test_las_horas_se_muestran_con_dos_digitos(admin_client):
    atencion(lunes(0), 8)
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert "<td>08:00</td>" in html and "<td>8:00</td>" not in html


def test_el_panel_dice_que_las_esperas_son_de_orden_de_magnitud(admin_client):
    for semana in range(6):
        for _ in range(6):
            atencion(lunes(semana), 10, minutos=45)
    html = admin_client.get(reverse("analitica:inicio")).content.decode()
    assert "orden de magnitud" in html and "VALIDACION_MODELOS" in html
    assert "promedio del periodo" in html or "No hay horarios" in html
