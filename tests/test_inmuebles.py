"""CRUD de inmuebles con estados y filtros (#26, HU-01, RF-10, RF-11, RF-12, RF-14)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.comun.campos import PesosField
from apps.comun.templatetags.formato import pesos, pesos_entrada
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol
from apps.inmuebles.models import HistorialEstadoInmueble, Inmueble

User = get_user_model()
CLAVE = "Clave-Segura-2026"

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user():
    u = User.objects.create_user("admin1", password=CLAVE, first_name="Ada")
    asignar_rol(u, ROL_ADMIN)
    return u


@pytest.fixture
def asesor_user():
    u = User.objects.create_user("asesor1", password=CLAVE, first_name="Aníbal")
    asignar_rol(u, ROL_ASESOR)
    return u


@pytest.fixture
def sesion(client, asesor_user):
    client.force_login(asesor_user)
    return client


def crear(titulo="Casa 1", **extra):
    datos = dict(
        titulo=titulo,
        direccion="Calle 1 # 2-3",
        precio=200_000_000,
        operacion="VENTA",
        tipo_inmueble="CASA",
    )
    datos.update(extra)
    return Inmueble.objects.create(**datos)


def datos_validos(**extra):
    datos = {
        "titulo": "Casa 12",
        "tipo_inmueble": "CASA",
        "operacion": "VENTA",
        "direccion": "Calle 5",
        "barrio": "Cantaclaro",
        "precio": "240.000.000",
        "area_m2": "96,5",
        "habitaciones": "3",
        "estado": "DISPONIBLE",
        "descripcion": "Patio amplio",
    }
    datos.update(extra)
    return datos


def titulos(respuesta):
    return [i.titulo for i in respuesta.context["inmuebles"]]


# --- Acceso y menú -----------------------------------------------------------------------------
def test_la_lista_exige_sesion(client):
    r = client.get(reverse("inmuebles:lista"))
    assert r.status_code == 302 and r.url.startswith(reverse("cuentas:login"))


def test_inmuebles_aparece_en_el_menu_al_existir_la_url(sesion):
    html = sesion.get("/").content.decode()
    assert f'href="{reverse("inmuebles:lista")}"' in html and "Inmuebles" in html


@pytest.mark.parametrize("rol", [ROL_ADMIN, ROL_ASESOR])
def test_asesores_y_administradores_pueden_trabajar_con_inmuebles(client, rol):
    u = User.objects.create_user(f"u_{rol}", password=CLAVE)
    asignar_rol(u, rol)
    client.force_login(u)
    assert client.get(reverse("inmuebles:lista")).status_code == 200
    assert client.get(reverse("inmuebles:crear")).status_code == 200


# --- Lista y filtros (RF-14) -------------------------------------------------------------------
def test_la_lista_oculta_los_inactivos_salvo_que_se_pidan(sesion):
    crear("Casa activa")
    crear("Casa inactiva", activo=False)
    assert titulos(sesion.get(reverse("inmuebles:lista"))) == ["Casa activa"]
    r = sesion.get(reverse("inmuebles:lista"), {"incluir_inactivos": "on"})
    assert set(titulos(r)) == {"Casa activa", "Casa inactiva"}


def test_buscar_por_titulo_direccion_o_barrio(sesion):
    crear("Casa Mocarí", direccion="Calle 9", barrio="Mocarí")
    crear("Apartamento Centro", direccion="Carrera 3 # 30", barrio="Centro")
    crear("Casa Norte", direccion="Avenida 7", barrio="La Castellana")
    url = reverse("inmuebles:lista")
    assert titulos(sesion.get(url, {"q": "mocarí"})) == ["Casa Mocarí"]
    assert titulos(sesion.get(url, {"q": "carrera"})) == ["Apartamento Centro"]
    assert titulos(sesion.get(url, {"q": "castellana"})) == ["Casa Norte"]


def test_filtrar_por_estado_operacion_y_tipo(sesion):
    crear("A", estado="RESERVADO")
    crear("B", operacion="ALQUILER", precio=1_000_000)
    crear("C", tipo_inmueble="APARTAMENTO")
    url = reverse("inmuebles:lista")
    assert titulos(sesion.get(url, {"estado": "RESERVADO"})) == ["A"]
    assert titulos(sesion.get(url, {"operacion": "ALQUILER"})) == ["B"]
    assert titulos(sesion.get(url, {"tipo_inmueble": "APARTAMENTO"})) == ["C"]


def test_filtrar_por_rango_de_precio_acepta_puntos(sesion):
    crear("Barata", precio=100_000_000)
    crear("Media", precio=250_000_000)
    crear("Cara", precio=600_000_000)
    r = sesion.get(
        reverse("inmuebles:lista"), {"precio_min": "200.000.000", "precio_max": "300000000"}
    )
    assert titulos(r) == ["Media"]


def test_un_rango_de_precio_invertido_avisa_sin_romper_la_pagina(sesion):
    crear("X")
    r = sesion.get(reverse("inmuebles:lista"), {"precio_min": "500", "precio_max": "100"})
    assert r.status_code == 200
    assert "El precio máximo debe ser mayor o igual que el mínimo." in r.content.decode()


def test_los_filtros_se_combinan(sesion):
    crear("Venta casa", operacion="VENTA", tipo_inmueble="CASA")
    crear("Venta apto", operacion="VENTA", tipo_inmueble="APARTAMENTO")
    crear("Alquiler casa", operacion="ALQUILER", tipo_inmueble="CASA", precio=900_000)
    r = sesion.get(reverse("inmuebles:lista"), {"operacion": "VENTA", "tipo_inmueble": "CASA"})
    assert titulos(r) == ["Venta casa"]


def test_los_mas_recientes_van_primero(sesion):
    crear("Primero")
    crear("Segundo")
    assert titulos(sesion.get(reverse("inmuebles:lista"))) == ["Segundo", "Primero"]


# --- Paginación -----------------------------------------------------------------------------------
def test_paginacion_de_20_en_20_conservando_los_filtros(sesion):
    for n in range(45):
        crear(f"Casa {n:02d}")
    url = reverse("inmuebles:lista")
    assert len(titulos(sesion.get(url))) == 20
    assert len(titulos(sesion.get(url, {"page": 3}))) == 5
    html = sesion.get(url, {"operacion": "VENTA"}).content.decode()
    assert "Página 1 de 3" in html
    assert "?operacion=VENTA&amp;page=2" in html  # el filtro viaja en el enlace


# --- Estados vacíos ------------------------------------------------------------------------------
def test_sin_inmuebles_se_invita_a_crear_el_primero(sesion):
    html = sesion.get(reverse("inmuebles:lista")).content.decode()
    assert "Aún no hay inmuebles" in html and reverse("inmuebles:crear") in html


def test_sin_resultados_se_sugiere_quitar_filtros(sesion):
    crear("Casa")
    html = sesion.get(reverse("inmuebles:lista"), {"q": "inexistente"}).content.decode()
    assert "No hay inmuebles con esos filtros" in html and "Limpiar filtros" in html


# --- Crear (RF-10, RF-11) --------------------------------------------------------------------------
def test_crear_inmueble_valido_con_precio_y_area_en_formato_colombiano(sesion):
    r = sesion.post(reverse("inmuebles:crear"), datos_validos(), follow=True)
    assert r.status_code == 200
    i = Inmueble.objects.get(titulo="Casa 12")
    assert i.precio == Decimal("240000000") and i.area_m2 == Decimal("96.5")
    assert i.habitaciones == 3 and i.estado == "DISPONIBLE"
    assert i.activo is True  # un inmueble nuevo nace activo y aparece en la lista
    assert "Inmueble «Casa 12» creado." in r.content.decode()


def test_al_crear_queda_registrado_el_estado_inicial(sesion, asesor_user):
    sesion.post(reverse("inmuebles:crear"), datos_validos(estado="RESERVADO"))
    h = HistorialEstadoInmueble.objects.get()
    assert (h.estado_anterior, h.estado_nuevo, h.cambiado_por) == ("", "RESERVADO", asesor_user)


@pytest.mark.parametrize(
    ("campo", "valor", "mensaje"),
    [
        ("precio", "0", "El precio debe ser mayor que 0."),
        ("precio", "gratis", "Escriba solo números, por ejemplo 240.000.000."),
        ("area_m2", "0", "El área debe ser mayor que 0 m²."),
        ("titulo", "", "Este campo es obligatorio."),
    ],
)
def test_datos_invalidos_no_crean_nada_y_dicen_como_corregir(sesion, campo, valor, mensaje):
    r = sesion.post(reverse("inmuebles:crear"), datos_validos(**{campo: valor}))
    assert r.status_code == 200 and not Inmueble.objects.exists()
    assert mensaje in r.content.decode()


def test_una_venta_no_puede_quedar_arrendada_ni_un_alquiler_vendido(sesion):
    r = sesion.post(
        reverse("inmuebles:crear"), datos_validos(operacion="VENTA", estado="ARRENDADO")
    )
    assert "Una venta no puede quedar como Arrendada. Elija Vendido." in r.content.decode()
    r = sesion.post(
        reverse("inmuebles:crear"), datos_validos(operacion="ALQUILER", estado="VENDIDO")
    )
    assert "Un alquiler no puede quedar como Vendido. Elija Arrendado." in r.content.decode()
    assert not Inmueble.objects.exists()


def test_un_envio_fallido_muestra_resumen_con_enlaces_a_cada_campo(sesion):
    r = sesion.post(reverse("inmuebles:crear"), datos_validos(precio="0", titulo=""))
    html = r.content.decode()
    assert "data-resumen-errores" in html and "Revise 2 puntos antes de guardar" in html
    assert 'href="#id_precio"' in html and 'href="#id_titulo"' in html
    assert 'aria-invalid="true"' in html and 'id="error-precio"' in html


def test_los_campos_opcionales_se_marcan_y_los_obligatorios_no(sesion):
    html = sesion.get(reverse("inmuebles:crear")).content.decode()
    assert html.count("(opcional)") >= 4  # barrio, área, habitaciones, descripción
    assert 'for="id_titulo">Título</label>' in html


# --- Editar y cambio de estado (RF-12) --------------------------------------------------------------
def test_editar_guarda_los_cambios(sesion):
    i = crear("Casa vieja")
    sesion.post(
        reverse("inmuebles:editar", args=[i.pk]), datos_validos(titulo="Casa nueva", activo="on")
    )
    i.refresh_from_db()
    assert i.titulo == "Casa nueva" and i.precio == Decimal("240000000")


def test_el_formulario_de_edicion_precarga_el_precio_con_puntos(sesion):
    i = crear(precio=240_000_000)
    html = sesion.get(reverse("inmuebles:editar", args=[i.pk])).content.decode()
    assert 'value="240.000.000"' in html


def test_cambiar_el_estado_deja_historial_con_usuario_y_sin_cambio_no_deja_nada(
    sesion, asesor_user
):
    i = crear("Casa", estado="DISPONIBLE")
    url = reverse("inmuebles:editar", args=[i.pk])
    sesion.post(url, datos_validos(titulo="Casa", estado="DISPONIBLE", activo="on"))
    assert not HistorialEstadoInmueble.objects.exists()  # no cambió el estado
    sesion.post(url, datos_validos(titulo="Casa", estado="RESERVADO", activo="on"))
    sesion.post(url, datos_validos(titulo="Casa", estado="VENDIDO", activo="on"))
    cambios = list(
        HistorialEstadoInmueble.objects.order_by("id").values_list(
            "estado_anterior", "estado_nuevo", "cambiado_por"
        )
    )
    assert cambios == [
        ("DISPONIBLE", "RESERVADO", asesor_user.pk),
        ("RESERVADO", "VENDIDO", asesor_user.pk),
    ]
    html = sesion.get(url).content.decode()
    assert "De Disponible a Reservado" in html and "De Reservado a Vendido" in html


def test_cambiar_la_operacion_a_alquiler_con_el_inmueble_vendido_se_rechaza(sesion):
    i = crear("Casa", estado="VENDIDO")
    r = sesion.post(
        reverse("inmuebles:editar", args=[i.pk]),
        datos_validos(titulo="Casa", operacion="ALQUILER", estado="VENDIDO", activo="on"),
    )
    assert r.status_code == 200
    i.refresh_from_db()
    assert i.operacion == "VENTA"


def test_editar_un_inmueble_inexistente_da_404(sesion):
    assert sesion.get(reverse("inmuebles:editar", args=[999])).status_code == 404


# --- Desactivar en lugar de borrar (RF-10) -----------------------------------------------------------
def test_desactivar_y_reactivar_conserva_el_registro(sesion):
    i = crear("Casa")
    url = reverse("inmuebles:activo", args=[i.pk])
    r = sesion.post(url, follow=True)
    i.refresh_from_db()
    assert i.activo is False and "desactivado" in r.content.decode()
    sesion.post(url)
    i.refresh_from_db()
    assert i.activo is True and Inmueble.objects.count() == 1


def test_activo_solo_acepta_post(sesion):
    i = crear("Casa")
    assert sesion.get(reverse("inmuebles:activo", args=[i.pk])).status_code == 405


def test_desactivar_vuelve_a_la_lista_con_los_mismos_filtros(sesion):
    i = crear("Casa")
    r = sesion.post(
        reverse("inmuebles:activo", args=[i.pk]), {"next": "/inmuebles/?operacion=VENTA"}
    )
    assert r.url == "/inmuebles/?operacion=VENTA"


@pytest.mark.parametrize(
    "malicioso", ["https://malo.example/robar", "//malo.example", "javascript:alert(1)"]
)
def test_no_se_redirige_fuera_del_sitio(sesion, malicioso):
    i = crear("Casa")
    r = sesion.post(reverse("inmuebles:activo", args=[i.pk]), {"next": malicioso})
    assert r.url == reverse("inmuebles:lista")


# --- Accesibilidad de la lista ----------------------------------------------------------------------
def test_la_lista_es_accesible(sesion):
    crear("Casa")
    html = sesion.get(reverse("inmuebles:lista")).content.decode()
    assert 'role="search"' in html and 'aria-label="Filtrar inmuebles"' in html
    assert '<caption class="solo-lectores">Lista de inmuebles</caption>' in html
    assert html.count('scope="col"') == 5
    assert 'for="id_q"' in html and 'role="status"' in html


def test_la_lista_no_hace_consultas_por_fila(sesion, django_assert_max_num_queries):
    for n in range(20):
        crear(f"Casa {n}")
    with django_assert_max_num_queries(8):
        sesion.get(reverse("inmuebles:lista"))


# --- Utilidades compartidas -------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("escrito", "esperado"),
    [
        ("240000000", Decimal("240000000")),
        ("240.000.000", Decimal("240000000")),
        ("$ 240.000.000", Decimal("240000000")),
        ("1.300.000", Decimal("1300000")),
        ("1.300.000,50", Decimal("1300000.50")),
        ("1.5", Decimal("1.5")),
        ("", None),
    ],
)
def test_pesos_field_entiende_como_escribe_la_gente(escrito, esperado):
    assert PesosField(required=False).clean(escrito) == esperado


def test_formato_de_pesos():
    assert pesos(240000000) == "$ 240.000.000"
    assert pesos(Decimal("1300000.00")) == "$ 1.300.000"
    assert pesos(None) == "—"
    assert pesos_entrada(Decimal("240000000.00")) == "240.000.000"
