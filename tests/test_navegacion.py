"""Plantilla base y navegación (#25): menú, accesibilidad, componentes y reglas de movimiento."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.urls import reverse

from apps.cuentas.navegacion import MENU, Destino, construir_menu
from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol

User = get_user_model()
CLAVE = "Clave-Segura-2026"
BASE = Path(settings.BASE_DIR)

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


# --- El menú muestra solo lo que existe -------------------------------------------------------
def test_destinos_sin_url_se_omiten_y_los_existentes_aparecen():
    definicion = (
        Destino("Hogar", "cuentas:inicio", "casa"),
        Destino("Fantasma", "no_existe:lista", "casa"),
    )
    assert [i.etiqueta for i in construir_menu("/", True, definicion)] == ["Hogar"]


def test_un_destino_aparece_en_cuanto_su_url_existe():
    antes = (Destino("Usuarios", "inexistente:lista", "clientes"),)
    despues = (Destino("Usuarios", "cuentas:usuarios", "clientes"),)
    assert construir_menu("/", True, antes) == []
    assert [i.etiqueta for i in construir_menu("/", True, despues)] == ["Usuarios"]


def test_destinos_solo_admin_se_filtran_por_rol():
    definicion = (Destino("Panel", "cuentas:usuarios", "administracion", solo_admin=True),)
    assert construir_menu("/", False, definicion) == []
    assert len(construir_menu("/", True, definicion)) == 1


def test_el_item_activo_sigue_la_ruta_y_las_ramas():
    inicio = {i.etiqueta: i.activo for i in construir_menu("/", True)}
    assert inicio["Hogar"] and not inicio.get("Administración", False)
    rama = {i.etiqueta: i.activo for i in construir_menu("/administracion/usuarios/nuevo/", True)}
    assert rama["Administración"] and not rama["Hogar"]


def test_el_menu_declarado_apunta_a_iconos_que_existen():
    sprite = (BASE / "templates/componentes/iconos.svg.html").read_text(encoding="utf-8")
    for d in MENU:
        assert f'id="i-{d.icono}"' in sprite, f"falta el icono {d.icono}"


def test_todo_icono_usado_en_plantillas_existe_en_el_sprite():
    sprite = (BASE / "templates/componentes/iconos.svg.html").read_text(encoding="utf-8")
    usados = set()
    for plantilla in (BASE / "templates").rglob("*.html"):
        texto = plantilla.read_text(encoding="utf-8")
        usados |= set(re.findall(r'(?:nombre|icono)="([a-z]+)"', texto))
    faltan = {n for n in usados if f'id="i-{n}"' not in sprite}
    assert not faltan, f"iconos sin definir: {faltan}"


# --- Estructura accesible de la página ---------------------------------------------------------
def test_la_pagina_tiene_puntos_de_referencia_y_enlace_para_saltar(client, admin_user):
    client.force_login(admin_user)
    html = client.get("/").content.decode()
    assert '<html lang="es-CO">' in html
    assert html.index('class="saltar"') < html.index("<header")  # primer elemento enfocable
    assert 'href="#contenido"' in html and '<main id="contenido"' in html
    assert '<nav class="menu" id="menu-principal" aria-label="Principal">' in html
    assert 'aria-controls="menu-principal"' in html and 'aria-expanded="false"' in html
    assert 'aria-label="Cerrar menú"' in html  # el panel móvil se puede cerrar con un botón


def test_solo_un_elemento_se_marca_como_pagina_actual(client, admin_user):
    client.force_login(admin_user)
    html = client.get(reverse("cuentas:usuarios")).content.decode()
    assert html.count('aria-current="page"') == 1


def test_los_iconos_decorativos_se_ocultan_a_lectores_de_pantalla(client, admin_user):
    client.force_login(admin_user)
    html = client.get("/").content.decode()
    assert 'class="icono" aria-hidden="true" focusable="false"' in html
    assert 'alt="HogarSits, ir a Hogar"' in html


def test_el_asesor_no_ve_administracion_en_el_menu(client, asesor_user):
    client.force_login(asesor_user)
    html = client.get("/").content.decode()
    assert "Administración" not in html


# --- Avisos: éxito sin interrumpir, error anunciado ---------------------------------------------
def test_un_exito_se_anuncia_con_status_y_se_puede_cerrar(client, admin_user):
    client.force_login(admin_user)
    r = client.post(
        reverse("cuentas:usuario_nuevo"),
        {
            "username": "luis", "first_name": "Luis", "email": "l@example.com",
            "rol": ROL_ASESOR, "password1": CLAVE, "password2": CLAVE,
        },
        follow=True,
    )
    html = r.content.decode()
    assert 'class="aviso aviso-exito" role="status"' in html
    assert 'aria-label="Cerrar aviso"' in html and "Usuario luis creado." in html


def test_un_error_se_anuncia_con_alert(client, admin_user):
    client.force_login(admin_user)
    r = client.post(reverse("cuentas:usuario_estado", args=[admin_user.pk]), follow=True)
    html = r.content.decode()
    assert 'class="aviso aviso-error" role="alert"' in html
    assert "No puede desactivar su propia cuenta." in html


def test_los_errores_de_formulario_se_enlazan_con_su_campo(client, admin_user):
    client.force_login(admin_user)
    r = client.post(
        reverse("cuentas:usuario_nuevo"),
        {"username": "x", "first_name": "X", "email": "x@example.com", "rol": ROL_ASESOR,
         "password1": "123", "password2": "456"},
    )
    html = r.content.decode()
    assert 'aria-invalid="true"' in html
    assert 'aria-describedby="error-password2"' in html and 'id="error-password2"' in html


# --- Guía de componentes -------------------------------------------------------------------------
def test_la_guia_de_componentes_es_solo_para_administradores(client, admin_user, asesor_user):
    url = reverse("cuentas:componentes")
    assert client.get(url).status_code == 302  # anónimo, al login
    client.force_login(asesor_user)
    assert client.get(url).status_code == 403
    client.force_login(admin_user)
    r = client.get(url)
    assert r.status_code == 200
    html = r.content.decode()
    for seccion in ("Paleta", "Botones", "Avisos", "Formulario", "Tabla", "Estado vacío"):
        assert seccion in html


# --- Recursos y reglas de movimiento (docs/diseno/MOVIMIENTO.md) ---------------------------------
RECURSOS = ["css/tokens.css", "css/app.css", "css/login.css", "js/nav.js", "img/logo-hogarsits.png"]


@pytest.mark.parametrize("ruta", RECURSOS)
def test_los_recursos_estaticos_existen(ruta):
    assert finders.find(ruta), f"falta static/{ruta}"


@pytest.mark.parametrize("hoja", ["app.css", "login.css"])
def test_las_transiciones_no_animan_propiedades_de_layout_ni_usan_all(hoja):
    css = (BASE / "static/css" / hoja).read_text(encoding="utf-8")
    for declaracion in re.findall(r"transition(?:-property)?\s*:[^;]+;", css):
        prohibidas = r"\b(all|width|height|top|left|margin|padding)\b"
        assert not re.search(prohibidas, declaracion), declaracion


def test_el_movimiento_respeta_las_preferencias_del_usuario():
    app = (BASE / "static/css/app.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in app
    assert "(hover: hover) and (pointer: fine)" in app  # el hover no se repite al tocar
    assert "transition-duration: 0ms" in app  # la pulsación responde al instante
    login = (BASE / "static/css/login.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: no-preference" in login


def test_el_plano_del_login_solo_se_anima_la_primera_vez(client):
    html = client.get(reverse("cuentas:login")).content.decode()
    assert "hs-plano-visto" in html and "plano-visto" in html
    css = (BASE / "static/css/login.css").read_text(encoding="utf-8")
    assert "html:not(.plano-visto)" in css
