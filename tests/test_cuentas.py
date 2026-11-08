"""Autenticación y roles (HU-11, RF-01 a RF-03)."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol, es_admin, es_asesor, rol_de

User = get_user_model()
CLAVE = "Clave-Segura-2026"

pytestmark = pytest.mark.django_db


def crear(username, rol=None, **extra):
    u = User.objects.create_user(username, password=CLAVE, **extra)
    if rol:
        asignar_rol(u, rol)
    return u


@pytest.fixture
def admin_user():
    return crear("admin1", ROL_ADMIN, first_name="Ada")


@pytest.fixture
def asesor_user():
    return crear("asesor1", ROL_ASESOR, first_name="Aníbal")


def entrar(client, user):
    client.force_login(user)
    return client


# --- Roles --------------------------------------------------------------------------------
def test_los_roles_existen_tras_migrar():
    assert set(Group.objects.values_list("name", flat=True)) >= {ROL_ADMIN, ROL_ASESOR}


def test_un_usuario_tiene_un_solo_rol():
    u = crear("x", ROL_ASESOR)
    asignar_rol(u, ROL_ADMIN)
    assert list(u.groups.values_list("name", flat=True)) == [ROL_ADMIN]
    assert rol_de(u) == ROL_ADMIN


def test_superusuario_cuenta_como_administrador():
    u = User.objects.create_superuser("root", password=CLAVE)
    assert es_admin(u) and rol_de(u) == ROL_ADMIN


def test_usuario_sin_rol_no_pasa_ninguna_comprobacion():
    u = crear("sinrol")
    assert not es_admin(u) and not es_asesor(u) and rol_de(u) == ""


def test_usuario_inactivo_no_es_admin(admin_user):
    admin_user.is_active = False
    assert not es_admin(admin_user)


def test_rol_desconocido_se_rechaza():
    with pytest.raises(ValueError):
        asignar_rol(crear("y"), "Jefe")


# --- Sin sesión no se accede a nada (RF-01, HU-11 CA2) -----------------------------------
@pytest.mark.parametrize(
    "nombre", ["cuentas:inicio", "cuentas:usuarios", "cuentas:usuario_nuevo"]
)
def test_anonimo_es_enviado_al_login(client, nombre):
    r = client.get(reverse(nombre))
    assert r.status_code == 302
    assert r.url.startswith(reverse("cuentas:login"))


def test_login_y_el_admin_de_django_siguen_accesibles_sin_sesion(client):
    assert client.get(reverse("cuentas:login")).status_code == 200
    assert client.get(reverse("admin:login")).status_code == 200


# --- Inicio y cierre de sesión (RF-01) ---------------------------------------------------
def test_login_correcto_lleva_a_hogar(client, asesor_user):
    r = client.post(reverse("cuentas:login"), {"username": "asesor1", "password": CLAVE})
    assert r.status_code == 302 and r.url == reverse("cuentas:inicio")
    assert client.get(reverse("cuentas:inicio")).status_code == 200


def test_login_incorrecto_muestra_mensaje_sin_revelar_cual_dato_falla(client, asesor_user):
    mal_clave = client.post(reverse("cuentas:login"), {"username": "asesor1", "password": "no"})
    mal_user = client.post(reverse("cuentas:login"), {"username": "nadie", "password": CLAVE})
    for r in (mal_clave, mal_user):
        assert r.status_code == 200
        assert "Usuario o contraseña incorrectos. Revise e intente de nuevo." in r.content.decode()


def test_usuario_desactivado_no_puede_entrar_y_recibe_el_mismo_mensaje(client, asesor_user):
    asesor_user.is_active = False
    asesor_user.save()
    r = client.post(reverse("cuentas:login"), {"username": "asesor1", "password": CLAVE})
    assert r.status_code == 200
    assert "Usuario o contraseña incorrectos" in r.content.decode()


def test_logout_solo_por_post_y_cierra_la_sesion(client, asesor_user):
    entrar(client, asesor_user)
    assert client.get(reverse("cuentas:logout")).status_code == 405
    r = client.post(reverse("cuentas:logout"))
    assert r.status_code == 302 and r.url == reverse("cuentas:login")
    assert client.get(reverse("cuentas:inicio")).status_code == 302


def test_hogar_muestra_nombre_y_rol(client, asesor_user):
    html = entrar(client, asesor_user).get(reverse("cuentas:inicio")).content.decode()
    assert "Aníbal" in html and "Asesor" in html


# --- Permisos por rol (RF-03, HU-11 CA1) -------------------------------------------------
@pytest.mark.parametrize(
    "nombre", ["cuentas:usuarios", "cuentas:usuario_nuevo"]
)
def test_asesor_no_administra_usuarios(client, asesor_user, nombre):
    r = entrar(client, asesor_user).get(reverse(nombre))
    assert r.status_code == 403
    assert "solo para administradores" in r.content.decode()


def test_asesor_no_puede_cambiar_estado_ni_editar(client, asesor_user, admin_user):
    entrar(client, asesor_user)
    assert client.post(reverse("cuentas:usuario_estado", args=[admin_user.pk])).status_code == 403
    assert client.get(reverse("cuentas:usuario_editar", args=[admin_user.pk])).status_code == 403
    admin_user.refresh_from_db()
    assert admin_user.is_active


def test_el_menu_muestra_administracion_solo_al_admin(client, admin_user, asesor_user):
    assert "Administración" in entrar(client, admin_user).get("/").content.decode()
    assert "Administración" not in entrar(client, asesor_user).get("/").content.decode()


# --- Gestión de usuarios por el administrador (RF-02) ------------------------------------
def test_admin_ve_la_lista_con_roles(client, admin_user, asesor_user):
    html = entrar(client, admin_user).get(reverse("cuentas:usuarios")).content.decode()
    assert "asesor1" in html and "admin1" in html and "Administrador" in html


def test_admin_crea_un_asesor_con_su_rol(client, admin_user):
    r = entrar(client, admin_user).post(
        reverse("cuentas:usuario_nuevo"),
        {
            "username": "luis",
            "first_name": "Luis",
            "last_name": "Pérez",
            "email": "luis@example.com",
            "rol": ROL_ASESOR,
            "password1": CLAVE,
            "password2": CLAVE,
        },
    )
    assert r.status_code == 302
    nuevo = User.objects.get(username="luis")
    assert rol_de(nuevo) == ROL_ASESOR and nuevo.is_active


def test_el_usuario_creado_puede_iniciar_sesion(client, admin_user):
    entrar(client, admin_user).post(
        reverse("cuentas:usuario_nuevo"),
        {
            "username": "marta",
            "first_name": "Marta",
            "email": "marta@example.com",
            "rol": ROL_ASESOR,
            "password1": CLAVE,
            "password2": CLAVE,
        },
    )
    from django.test import Client

    otro = Client()
    r = otro.post(reverse("cuentas:login"), {"username": "marta", "password": CLAVE})
    assert r.status_code == 302 and r.url == reverse("cuentas:inicio")


def test_crear_usuario_valida_contrasena_y_datos(client, admin_user):
    r = entrar(client, admin_user).post(
        reverse("cuentas:usuario_nuevo"),
        {
            "username": "debil",
            "first_name": "",
            "email": "no-es-correo",
            "rol": ROL_ASESOR,
            "password1": "123",
            "password2": "456",
        },
    )
    assert r.status_code == 200
    assert not User.objects.filter(username="debil").exists()


def test_admin_edita_nombre_y_rol(client, admin_user, asesor_user):
    r = entrar(client, admin_user).post(
        reverse("cuentas:usuario_editar", args=[asesor_user.pk]),
        {
            "first_name": "Aníbal",
            "last_name": "Gómez",
            "email": "a@example.com",
            "is_active": "on",
            "rol": ROL_ADMIN,
        },
    )
    assert r.status_code == 302
    asesor_user.refresh_from_db()
    assert asesor_user.last_name == "Gómez" and rol_de(asesor_user) == ROL_ADMIN


def test_admin_desactiva_y_reactiva_un_asesor(client, admin_user, asesor_user):
    entrar(client, admin_user)
    client.post(reverse("cuentas:usuario_estado", args=[asesor_user.pk]))
    asesor_user.refresh_from_db()
    assert not asesor_user.is_active
    client.post(reverse("cuentas:usuario_estado", args=[asesor_user.pk]))
    asesor_user.refresh_from_db()
    assert asesor_user.is_active


def test_estado_solo_acepta_post(client, admin_user, asesor_user):
    r = entrar(client, admin_user).get(reverse("cuentas:usuario_estado", args=[asesor_user.pk]))
    assert r.status_code == 405


def test_no_se_puede_desactivar_la_propia_cuenta(client, admin_user):
    entrar(client, admin_user).post(reverse("cuentas:usuario_estado", args=[admin_user.pk]))
    admin_user.refresh_from_db()
    assert admin_user.is_active


def test_no_se_puede_quitar_a_si_mismo_el_rol_de_administrador(client, admin_user):
    r = entrar(client, admin_user).post(
        reverse("cuentas:usuario_editar", args=[admin_user.pk]),
        {"first_name": "Ada", "email": "ada@example.com", "is_active": "on", "rol": ROL_ASESOR},
    )
    assert r.status_code == 200
    assert "No puede quitarse a sí mismo" in r.content.decode()
    assert rol_de(admin_user) == ROL_ADMIN


def test_admin_puede_degradar_a_otro_admin_si_queda_alguno(client, admin_user):
    otro = crear("admin2", ROL_ADMIN, first_name="O", email="o@example.com")
    r = entrar(client, admin_user).post(
        reverse("cuentas:usuario_editar", args=[otro.pk]),
        {"first_name": "O", "email": "o@example.com", "is_active": "on", "rol": ROL_ASESOR},
    )
    assert r.status_code == 302 and rol_de(otro) == ROL_ASESOR


def test_el_formulario_protege_al_ultimo_administrador_activo():
    """Defensa en profundidad: aunque no haya editor, no se deja el sistema sin administradores."""
    from apps.cuentas.forms import UsuarioEditarForm

    ultimo = crear("ultimo", ROL_ADMIN, first_name="U", email="u@example.com")
    datos = {"first_name": "U", "email": "u@example.com", "is_active": "on", "rol": ROL_ASESOR}
    form = UsuarioEditarForm(datos, instance=ultimo)
    assert not form.is_valid()
    assert "al menos un administrador activo" in str(form.errors)
    form = UsuarioEditarForm({**datos, "is_active": ""}, instance=ultimo)
    assert not form.is_valid()
