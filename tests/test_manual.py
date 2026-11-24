"""El manual de usuario (docs/manual) no debe tener imagenes rotas ni prometer lo que no existe."""
import re
from pathlib import Path

from django.urls import reverse

RAIZ = Path(__file__).resolve().parent.parent
MANUAL_DIR = RAIZ / "docs" / "manual"
TEXTO = (MANUAL_DIR / "MANUAL_DE_USUARIO.md").read_text(encoding="utf-8")


def test_toda_imagen_del_manual_existe():
    rutas = re.findall(r"!\[[^\]]+\]\(([^)]+)\)", TEXTO)
    assert len(rutas) >= 15
    faltan = [r for r in rutas if not (MANUAL_DIR / r).is_file()]
    assert not faltan, faltan


def test_toda_imagen_tiene_texto_alternativo():
    assert not re.findall(r"!\[\s*\]\(", TEXTO)


def test_las_anclas_del_indice_existen():
    titulos = {
        re.sub(r"[^\w\s-]", "", t.lower()).strip().replace(" ", "-")
        for t in re.findall(r"^## (.+)$", TEXTO, flags=re.MULTILINE)
    }
    anclas = set(re.findall(r"\]\(#([^)]+)\)", TEXTO))
    assert anclas and anclas <= titulos, anclas - titulos


def test_avisa_que_las_capturas_son_simuladas_y_los_limites():
    assert "datos simulados" in TEXTO
    assert "orden de magnitud" in TEXTO
    assert "no se ha verificado" in TEXTO


def test_las_cifras_de_reglas_coinciden_con_el_codigo():
    from django.conf import settings

    from apps.cuentas import bloqueo

    assert f"**{bloqueo.MAX_FALLOS} intentos fallidos**" in TEXTO
    assert f"**{bloqueo.MINUTOS_BLOQUEO} minutos**" in TEXTO
    assert f"**más de {settings.DIAS_SIN_SEGUIMIENTO} días sin movimiento**" in TEXTO


def test_las_pantallas_citadas_existen(client, django_user_model):
    from apps.cuentas.roles import ROL_ADMIN, asignar_rol

    jefe = django_user_model.objects.create_user("jefe_manual", password="Clave-Larga-2026")
    asignar_rol(jefe, ROL_ADMIN)
    client.force_login(jefe)
    for nombre in ("cuentas:inicio", "inmuebles:lista", "clientes:lista", "seguimiento:cola",
                   "agenda:semana", "cuentas:usuarios", "horarios:lista", "horarios:disponibilidad",
                   "analitica:inicio", "analitica:asesores"):
        assert client.get(reverse(nombre)).status_code == 200, nombre
