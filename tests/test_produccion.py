"""Imagen y configuración de producción (#45, RNF-04, RNF-09).

Comprueba lo que se puede comprobar sin Docker: la vista de salud, los ajustes de producción y
que el Dockerfile y `.dockerignore` no hagan lo que no deben. La imagen en sí se construye y se
prueba de verdad en el CI (job `imagen`) y a mano (docs/aws/IMAGEN_DOCKER.md).
"""

import importlib
import json
import re
from pathlib import Path
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.urls import reverse

RAIZ = Path(__file__).resolve().parent.parent
DOCKERFILE = (RAIZ / "Dockerfile.prod").read_text(encoding="utf-8")
# Solo las instrucciones: los comentarios explican y pueden nombrar lo que NO se hace.
INSTRUCCIONES = "\n".join(
    linea for linea in DOCKERFILE.splitlines() if not linea.lstrip().startswith("#")
)


# --- Salud: pública y sin filtrar nada ---------------------------------------------------------
@pytest.mark.django_db
def test_la_salud_es_publica_aunque_toda_vista_exija_sesion(client):
    r = client.get(reverse("comun:salud"))
    assert r.status_code == 200 and json.loads(r.content) == {"estado": "ok"}


@pytest.mark.django_db
def test_la_salud_con_base_de_datos_responde_ok(client):
    r = client.get(reverse("comun:salud_db"))
    assert r.status_code == 200 and json.loads(r.content) == {"estado": "ok"}


def test_si_la_base_de_datos_cae_responde_503_sin_filtrar_el_error(client):
    with mock.patch(
        "apps.comun.views.connection.cursor", side_effect=OperationalError("password=secreta")
    ):
        r = client.get(reverse("comun:salud_db"))
    assert r.status_code == 503
    assert json.loads(r.content) == {"estado": "sin_base_de_datos"}
    assert "secreta" not in r.content.decode()  # no se filtra el detalle de la infraestructura


def test_la_salud_simple_no_toca_la_base_de_datos(client):
    """Sin la marca django_db, cualquier consulta lanzaría RuntimeError."""
    assert client.get(reverse("comun:salud")).status_code == 200


@pytest.mark.parametrize("nombre", ["comun:salud", "comun:salud_db"])
@pytest.mark.django_db
def test_la_salud_solo_acepta_lectura_y_no_se_guarda_en_cache(client, nombre):
    assert client.post(reverse(nombre)).status_code == 405
    assert "max-age=0" in client.get(reverse(nombre))["Cache-Control"]


def test_las_rutas_de_salud_estan_donde_las_espera_el_balanceador():
    assert reverse("comun:salud") == "/salud/" and reverse("comun:salud_db") == "/salud/db/"


# --- Ajustes de producción -----------------------------------------------------------------------
@pytest.fixture
def prod(monkeypatch):
    monkeypatch.setenv("ALLOWED_HOSTS", "hogarsits.example.com,otro.example.com")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "https://hogarsits.example.com")
    from config.settings import prod as modulo

    return importlib.reload(modulo)


def test_los_hosts_y_origenes_vienen_del_entorno(prod):
    assert prod.ALLOWED_HOSTS == ["hogarsits.example.com", "otro.example.com"]
    assert prod.CSRF_TRUSTED_ORIGINS == ["https://hogarsits.example.com"]


def test_sin_allowed_hosts_la_produccion_no_arranca(monkeypatch):
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    from config.settings import prod as modulo

    with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
        importlib.reload(modulo)


def test_whitenoise_va_antes_del_login_para_que_el_css_del_acceso_sea_publico(prod):
    mw = prod.MIDDLEWARE
    assert mw[0] == "django.middleware.security.SecurityMiddleware"
    assert mw[1] == "whitenoise.middleware.WhiteNoiseMiddleware"
    assert mw.index("whitenoise.middleware.WhiteNoiseMiddleware") < mw.index(
        "django.contrib.auth.middleware.LoginRequiredMiddleware"
    )
    assert len(mw) == len(set(mw))  # nada duplicado


def test_los_estaticos_van_con_whitenoise_y_las_fotos_conservan_su_almacenamiento(prod):
    assert prod.STORAGES["staticfiles"]["BACKEND"].startswith("whitenoise.storage.")
    assert prod.STORAGES["default"]["BACKEND"] == "django.core.files.storage.FileSystemStorage"


def test_con_bucket_las_fotos_van_a_s3_tambien_en_produccion(monkeypatch):
    monkeypatch.setenv("ALLOWED_HOSTS", "hogarsits.example.com")
    monkeypatch.setenv("AWS_STORAGE_BUCKET_NAME", "hogarsits-fotos")
    from config.settings import base
    from config.settings import prod as modulo

    importlib.reload(base)
    modulo = importlib.reload(modulo)
    try:
        assert modulo.STORAGES["default"]["BACKEND"] == "storages.backends.s3.S3Storage"
        assert modulo.STORAGES["staticfiles"]["BACKEND"].startswith("whitenoise.")
    finally:  # no dejar el módulo base con el bucket para las pruebas siguientes
        monkeypatch.delenv("AWS_STORAGE_BUCKET_NAME")
        importlib.reload(base)


def test_la_comprobacion_de_salud_no_se_redirige_a_https(prod):
    exentas = [re.compile(p) for p in prod.SECURE_REDIRECT_EXEMPT]
    assert any(p.match("salud/") for p in exentas) and any(p.match("salud/db/") for p in exentas)
    assert not any(p.match("analisis/") for p in exentas)  # lo demás sí redirige


def test_los_registros_van_a_la_salida_estandar(prod):
    assert prod.LOGGING["handlers"]["consola"]["class"] == "logging.StreamHandler"


# --- Dockerfile.prod ------------------------------------------------------------------------------
def test_la_imagen_no_corre_como_root():
    assert re.search(r"^USER app$", DOCKERFILE, re.M)
    assert "useradd" in DOCKERFILE and "nologin" in DOCKERFILE


def test_la_imagen_instala_solo_dependencias_de_ejecucion():
    assert "requirements/base.txt" in DOCKERFILE
    assert "requirements/dev.txt" not in DOCKERFILE  # ni pytest, ni ruff, ni coverage


def test_la_imagen_no_copia_ni_define_secretos():
    assert not re.search(r"^(COPY|ADD)\b.*\.env\b", INSTRUCCIONES, re.M)  # no copia el .env
    assert "AKIA" not in DOCKERFILE and "AWS_SECRET" not in DOCKERFILE
    # las variables de relleno del build están acotadas a un solo RUN (no son ENV)
    assert not re.search(r"^ENV .*SECRET_KEY", DOCKERFILE, re.M)


def test_la_imagen_recoge_estaticos_tiene_healthcheck_y_arranca_con_gunicorn():
    assert "collectstatic --noinput" in DOCKERFILE
    assert "HEALTHCHECK" in DOCKERFILE and "/salud/" in DOCKERFILE
    assert "gunicorn config.wsgi:application" in DOCKERFILE
    assert "runserver" not in INSTRUCCIONES  # nada del servidor de desarrollo en producción
    assert "DJANGO_SETTINGS_MODULE=config.settings.prod" in DOCKERFILE


def test_el_entrypoint_es_posix_con_saltos_de_linea_unix():
    contenido = (RAIZ / "scripts" / "entrypoint.sh").read_bytes()
    assert contenido.startswith(b"#!/bin/sh") and b"\r" not in contenido
    assert b'exec "$@"' in contenido and b"RUN_MIGRATIONS" in contenido


def test_gitattributes_fuerza_saltos_unix_en_scripts_y_dockerfile():
    lineas = (RAIZ / ".gitattributes").read_text().splitlines()
    assert "*.sh text eol=lf" in lineas and "Dockerfile* text eol=lf" in lineas


def test_dockerignore_deja_fuera_secretos_datos_y_peso_inutil():
    lineas = {x.strip() for x in (RAIZ / ".dockerignore").read_text().splitlines()}
    for excluido in (".env", "venv/", "media/", "db.sqlite3", ".git", "tests/", "docs/"):
        assert excluido in lineas, excluido
    assert "!.env.example" in lineas  # el ejemplo sí puede ir


# --- Dependencias -----------------------------------------------------------------------------------
def test_las_dependencias_de_ejecucion_incluyen_lo_que_pide_produccion():
    base = (RAIZ / "requirements" / "base.txt").read_text().lower()
    for paquete in ("gunicorn", "whitenoise", "psycopg", "django-storages", "boto3"):
        assert paquete in base, paquete


def test_no_se_instalan_librerias_que_el_codigo_no_usa():
    """pandas y matplotlib estaban en los requisitos sin que nada las importara (~100 MB)."""
    base = (RAIZ / "requirements" / "base.txt").read_text().lower()
    assert "pandas" not in base and "matplotlib" not in base
    for archivo in list((RAIZ / "apps").rglob("*.py")) + list((RAIZ / "config").rglob("*.py")):
        texto = archivo.read_text(encoding="utf-8")
        assert not re.search(r"^\s*(import|from)\s+(pandas|matplotlib)\b", texto, re.M), archivo


def test_los_requisitos_de_desarrollo_incluyen_los_de_ejecucion():
    dev = (RAIZ / "requirements" / "dev.txt").read_text()
    assert dev.splitlines()[0].strip() == "-r base.txt"


# --- Archivos estáticos: lo que rompió el primer build de la imagen -------------------------------
def test_collectstatic_funciona_con_el_almacenamiento_de_produccion(settings, tmp_path):
    """El `runserver` de desarrollo no hace este paso: el primer build real de la imagen falló
    porque un JS de terceros referenciaba un mapa (.map) que no existe. Esta prueba lo atrapa en
    el CI normal, sin Docker."""
    from django.core.management import call_command

    settings.STATIC_ROOT = tmp_path
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    call_command("collectstatic", "--noinput", verbosity=0)
    assert (tmp_path / "staticfiles.json").exists()
    manifiesto = json.loads((tmp_path / "staticfiles.json").read_text(encoding="utf-8"))
    for archivo in ("css/tokens.css", "css/app.css", "js/analisis.js", "js/vendor/chart.umd.min.js"):
        assert archivo in manifiesto["paths"], archivo  # y cada uno con su nombre con hash


def test_ningun_estatico_referencia_mapas_de_depuracion_inexistentes():
    for archivo in (RAIZ / "static").rglob("*"):
        if archivo.suffix in {".js", ".css"}:
            texto = archivo.read_text(encoding="utf-8", errors="ignore")
            for ref in re.findall(r"sourceMappingURL=(\S+)", texto):
                assert (archivo.parent / ref).exists(), f"{archivo.name} referencia {ref}"


def test_la_biblioteca_copiada_coincide_con_su_huella_documentada():
    import hashlib

    contenido = (RAIZ / "static" / "js" / "vendor" / "chart.umd.min.js").read_bytes()
    readme = (RAIZ / "static" / "js" / "vendor" / "README.md").read_text(encoding="utf-8")
    huellas = re.findall(r"`([0-9a-f]{64})`", readme)
    assert len(huellas) == 2  # la del original y la de la copia modificada
    copia = re.search(r"Copia en este repositorio[^`]*`([0-9a-f]{64})`", readme).group(1)
    # Debe ser la de la COPIA, no la del original: el original (con el mapa de depuración)
    # rompe `collectstatic` en producción.
    assert hashlib.sha256(contenido).hexdigest() == copia


# --- Script de subida a ECR (no se puede ejecutar sin AWS: solo se revisa lo estático) -------------
ECR = (RAIZ / "scripts" / "subir_a_ecr.sh").read_text(encoding="utf-8")


def test_el_script_de_ecr_falla_rapido_y_crea_un_repositorio_seguro():
    assert ECR.startswith("#!/usr/bin/env bash") and "set -euo pipefail" in ECR
    assert "scanOnPush=true" in ECR  # análisis de vulnerabilidades al subir
    assert "IMMUTABLE" in ECR  # las etiquetas no se pisan
    assert "AES256" in ECR and "put-lifecycle-policy" in ECR  # cifrado y límite de imágenes


def test_el_script_de_ecr_no_lleva_credenciales_ni_pide_latest():
    assert not re.search(r"AKIA[0-9A-Z]{16}", ECR)
    assert "aws_secret_access_key" not in ECR.lower()
    assert ":latest" not in ECR  # con etiquetas inmutables no se puede volver a subir latest
    assert "get-login-password" in ECR and "--password-stdin" in ECR  # sin la clave en el comando


def test_el_script_de_ecr_tiene_saltos_de_linea_unix():
    assert b"\r" not in (RAIZ / "scripts" / "subir_a_ecr.sh").read_bytes()


def test_el_ci_construye_y_prueba_la_imagen():
    ci = (RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "docker build -f Dockerfile.prod" in ci and "/salud/" in ci
    assert "docker exec web id -u" in ci  # comprueba que no corre como root
