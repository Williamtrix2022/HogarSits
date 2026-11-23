"""Fotos de inmuebles con almacenamiento local o S3 (#27, RF-13)."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.cuentas.roles import ROL_ASESOR, asignar_rol
from apps.inmuebles import fotos as servicio
from apps.inmuebles.models import FotoInmueble, Inmueble
from config.storage import construir_storages

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def almacen_en_memoria(settings):
    """Las pruebas no escriben archivos reales ni llaman a AWS."""
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def sesion(client):
    u = User.objects.create_user("asesor1", password="Clave-Segura-2026")
    asignar_rol(u, ROL_ASESOR)
    client.force_login(u)
    return client


@pytest.fixture
def casa():
    return Inmueble.objects.create(
        titulo="Casa 12", tipo_inmueble="CASA", operacion="VENTA", direccion="Cll 1", precio=100
    )


def imagen(nombre="foto.png", formato="PNG", tam=(20, 10)):
    buffer = io.BytesIO()
    Image.new("RGB", tam, "navy").save(buffer, formato)
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


def subir(client, casa, *archivos):
    return client.post(
        reverse("inmuebles:foto_subir", args=[casa.pk]), {"imagenes": list(archivos)}, follow=True
    )


# --- Subida -------------------------------------------------------------------------------
def test_sube_una_foto(sesion, casa):
    r = subir(sesion, casa, imagen())
    assert casa.fotos.count() == 1 and "1 foto(s) agregada(s)" in r.content.decode()


def test_sube_varias_fotos_y_guarda_el_orden(sesion, casa):
    subir(sesion, casa, imagen("a.png"), imagen("b.jpg", "JPEG"), imagen("c.webp", "WEBP"))
    assert [f.orden for f in casa.fotos.all()] == [0, 1, 2]


def test_las_nuevas_van_al_final(sesion, casa):
    subir(sesion, casa, imagen("a.png"), imagen("b.png"))
    subir(sesion, casa, imagen("c.png"))
    assert [f.orden for f in casa.fotos.all()] == [0, 1, 2]


@pytest.mark.parametrize("nombre", ["doc.txt", "anim.gif", "foto.bmp", "sin_extension"])
def test_rechaza_extensiones_no_permitidas(sesion, casa, nombre):
    r = subir(sesion, casa, imagen(nombre))
    assert not casa.fotos.exists() and "JPG, PNG o WebP" in r.content.decode()


def test_rechaza_un_archivo_que_no_es_imagen_aunque_diga_jpg(sesion, casa):
    falso = SimpleUploadedFile("virus.jpg", b"esto no es una imagen", content_type="image/jpeg")
    r = subir(sesion, casa, falso)
    assert not casa.fotos.exists() and "no es una imagen válida" in r.content.decode()


def test_rechaza_el_formato_real_aunque_la_extension_mienta(sesion, casa):
    r = subir(sesion, casa, imagen("foto.jpg", "GIF"))  # un GIF disfrazado de .jpg
    assert not casa.fotos.exists() and "formato real" in r.content.decode()


def test_rechaza_fotos_de_mas_de_5_mb(sesion, casa):
    grande = SimpleUploadedFile("grande.png", b"\x89PNG" + b"0" * (5 * 1024 * 1024 + 1))
    r = subir(sesion, casa, grande)
    assert not casa.fotos.exists() and "el máximo es 5 MB" in r.content.decode()


def test_una_foto_mala_no_deja_pasar_a_las_buenas(sesion, casa):
    subir(sesion, casa, imagen("buena.png"), imagen("mala.txt"))
    assert not casa.fotos.exists()  # todo o nada: no queda una subida a medias


def test_respeta_el_maximo_por_inmueble(sesion, casa):
    subir(sesion, casa, *[imagen(f"{i}.png") for i in range(servicio.MAX_FOTOS)])
    assert casa.fotos.count() == servicio.MAX_FOTOS
    r = subir(sesion, casa, imagen("extra.png"))
    assert casa.fotos.count() == servicio.MAX_FOTOS
    assert "Solo caben 0 foto(s) más" in r.content.decode()


def test_no_caben_mas_de_las_que_quedan(sesion, casa):
    subir(sesion, casa, *[imagen(f"{i}.png") for i in range(8)])
    r = subir(sesion, casa, imagen("a.png"), imagen("b.png"), imagen("c.png"))
    assert casa.fotos.count() == 8 and "Solo caben 2 foto(s) más" in r.content.decode()


def test_sin_elegir_archivos_pide_elegir(sesion, casa):
    r = sesion.post(reverse("inmuebles:foto_subir", args=[casa.pk]), {}, follow=True)
    assert "Elija al menos una foto" in r.content.decode()


def test_inmueble_inexistente_da_404(sesion):
    assert sesion.post(reverse("inmuebles:foto_subir", args=[9999])).status_code == 404


def test_requiere_sesion(client, casa):
    r = client.post(reverse("inmuebles:foto_subir", args=[casa.pk]))
    assert r.status_code == 302 and "ingresar" in r["Location"]


def test_subir_solo_acepta_post(sesion, casa):
    assert sesion.get(reverse("inmuebles:foto_subir", args=[casa.pk])).status_code == 405


# --- Galería y borrado --------------------------------------------------------------------
def test_la_ficha_muestra_la_galeria_con_texto_alternativo(sesion, casa):
    subir(sesion, casa, imagen())
    html = sesion.get(reverse("inmuebles:editar", args=[casa.pk])).content.decode()
    assert 'alt="Foto 1 de Casa 12"' in html and "(1 de 10)" in html


def test_la_ficha_sin_fotos_lo_dice(sesion, casa):
    html = sesion.get(reverse("inmuebles:editar", args=[casa.pk])).content.decode()
    assert "aún no tiene fotos" in html


def test_la_ficha_avisa_cuando_se_llego_al_maximo(sesion, casa):
    subir(sesion, casa, *[imagen(f"{i}.png") for i in range(servicio.MAX_FOTOS)])
    html = sesion.get(reverse("inmuebles:editar", args=[casa.pk])).content.decode()
    assert "Llegó al máximo" in html and "Subir fotos" not in html


def test_borrar_quita_la_fila_y_el_archivo(sesion, casa):
    subir(sesion, casa, imagen())
    foto = casa.fotos.get()
    almacen, nombre = foto.imagen.storage, foto.imagen.name
    assert almacen.exists(nombre)
    r = sesion.post(reverse("inmuebles:foto_borrar", args=[foto.pk]), follow=True)
    assert not FotoInmueble.objects.exists() and not almacen.exists(nombre)
    assert "Foto eliminada" in r.content.decode()


def test_borrar_avisa_si_el_archivo_no_se_pudo_quitar(sesion, casa, monkeypatch):
    subir(sesion, casa, imagen())
    foto = casa.fotos.get()

    def falla(self, name):
        raise PermissionError("AccessDenied")

    monkeypatch.setattr("django.core.files.storage.memory.InMemoryStorage.delete", falla)
    r = sesion.post(reverse("inmuebles:foto_borrar", args=[foto.pk]), follow=True)
    assert not FotoInmueble.objects.exists()  # la foto ya no se muestra
    assert "no pudo borrarse del almacenamiento" in r.content.decode()


def test_borrar_solo_acepta_post(sesion, casa):
    foto = FotoInmueble.objects.create(inmueble=casa, imagen=ContentFile(b"x", name="x.png"))
    assert sesion.get(reverse("inmuebles:foto_borrar", args=[foto.pk])).status_code == 405


def test_borrar_requiere_sesion(client, casa):
    foto = FotoInmueble.objects.create(inmueble=casa, imagen=ContentFile(b"x", name="x.png"))
    assert client.post(reverse("inmuebles:foto_borrar", args=[foto.pk])).status_code == 302
    assert FotoInmueble.objects.count() == 1


# --- Configuración del almacenamiento -----------------------------------------------------
def test_sin_bucket_se_usa_el_disco_local():
    cfg = construir_storages("")
    assert cfg["default"]["BACKEND"] == "django.core.files.storage.FileSystemStorage"


def test_con_bucket_se_usa_s3_privado_con_enlaces_firmados():
    cfg = construir_storages("hogarsits-fotos-dev", "us-east-2")
    assert cfg["default"]["BACKEND"] == "storages.backends.s3.S3Storage"
    opciones = cfg["default"]["OPTIONS"]
    assert opciones["bucket_name"] == "hogarsits-fotos-dev" and opciones["region_name"] == "us-east-2"
    assert opciones["querystring_auth"] is True  # bucket privado, enlaces que caducan
    assert opciones["file_overwrite"] is False
    assert "access_key" not in opciones and "secret_key" not in opciones  # nada de claves en código


def test_la_configuracion_s3_genera_enlaces_firmados_sin_red(settings, monkeypatch):
    """Comprueba el cableado (backend, bucket, firma) sin llamar a AWS: la firma es local."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAFAKEFAKEFAKEFAKE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake-secret-fake-secret-fake-secret-1234")
    settings.STORAGES = construir_storages("hogarsits-fotos-dev", "us-east-1")
    from django.core.files.storage import storages

    url = storages["default"].url("inmuebles/2026/11/casa.png")
    assert "hogarsits-fotos-dev" in url and "X-Amz-Signature" in url and "X-Amz-Expires=3600" in url


# --- Comando probar_almacenamiento --------------------------------------------------------
def test_el_comando_comprueba_el_almacenamiento_de_punta_a_punta(capsys):
    from django.core.management import call_command

    call_command("probar_almacenamiento")
    salida = capsys.readouterr().out
    assert "Todo correcto" in salida and "Guardar el archivo" in salida
    assert "disco local" in salida  # sin bucket configurado en las pruebas


def test_el_comando_dice_en_que_paso_fallo(monkeypatch):
    from django.core.management import CommandError, call_command

    def falla(self, name, content, max_length=None):
        raise PermissionError("AccessDenied")

    monkeypatch.setattr("django.core.files.storage.memory.InMemoryStorage.save", falla)
    with pytest.raises(CommandError, match="Falló «Guardar el archivo».*AccessDenied"):
        call_command("probar_almacenamiento")
