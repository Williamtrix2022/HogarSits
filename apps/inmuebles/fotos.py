"""Fotos de inmuebles: validación, alta y baja (#27, RF-13)."""

import logging
import os

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from apps.comun.formularios import AccesibleFormMixin

from .models import FotoInmueble

logger = logging.getLogger(__name__)

MAX_FOTOS = 10
MAX_BYTES = 5 * 1024 * 1024  # 5 MB por foto
EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp")
FORMATOS = ("JPEG", "PNG", "WEBP")  # el formato real, no el que dice la extensión


def validar_imagen(archivo):
    """Rechaza lo que no sea una foto JPG, PNG o WebP de hasta 5 MB. Devuelve el archivo."""
    nombre = os.path.basename(archivo.name or "")
    if os.path.splitext(nombre)[1].lower() not in EXTENSIONES:
        raise ValidationError(f"«{nombre}»: use una foto JPG, PNG o WebP.")
    if archivo.size > MAX_BYTES:  # antes de abrirla: no se procesa un archivo enorme
        mb = archivo.size / (1024 * 1024)
        raise ValidationError(f"«{nombre}» pesa {mb:.1f} MB; el máximo es 5 MB.")
    try:
        verificado = forms.ImageField().to_python(archivo)  # Pillow comprueba que sea imagen
    except ValidationError:
        raise ValidationError(f"«{nombre}» no es una imagen válida.") from None
    if verificado.image.format not in FORMATOS:
        raise ValidationError(f"«{nombre}»: el formato real no es JPG, PNG ni WebP.")
    return verificado


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        archivos = [a for a in (data if isinstance(data, (list, tuple)) else [data]) if a]
        if not archivos:
            raise ValidationError("Elija al menos una foto.", code="required")
        return [validar_imagen(a) for a in archivos]


class FotosForm(AccesibleFormMixin, forms.Form):
    imagenes = MultipleImageField(
        label="Agregar fotos",
        widget=MultipleFileInput(attrs={"accept": ",".join(EXTENSIONES)}),
        help_text=f"JPG, PNG o WebP, hasta 5 MB cada una. Máximo {MAX_FOTOS} fotos por inmueble.",
    )

    def __init__(self, *args, inmueble, **kwargs):
        super().__init__(*args, **kwargs)
        self.inmueble = inmueble

    def clean_imagenes(self):
        archivos = self.cleaned_data["imagenes"]
        caben = MAX_FOTOS - self.inmueble.fotos.count()
        if len(archivos) > caben:
            raise ValidationError(
                f"Solo caben {max(caben, 0)} foto(s) más: el máximo es {MAX_FOTOS} por inmueble."
            )
        return archivos


@transaction.atomic
def agregar_fotos(inmueble, archivos) -> list[FotoInmueble]:
    """Guarda las fotos al final del orden actual."""
    ultimo = inmueble.fotos.aggregate(m=Max("orden"))["m"]
    siguiente = 0 if ultimo is None else ultimo + 1
    return [
        FotoInmueble.objects.create(inmueble=inmueble, imagen=archivo, orden=siguiente + i)
        for i, archivo in enumerate(archivos)
    ]


def borrar_foto(foto: FotoInmueble) -> bool:
    """Borra la fila y el archivo. Devuelve False si el archivo no se pudo quitar del almacén."""
    almacen, nombre = foto.imagen.storage, foto.imagen.name
    foto.delete()
    try:
        almacen.delete(nombre)
    except Exception:  # p. ej. permisos de S3: la foto ya no se muestra, pero queda un huérfano
        logger.warning("No se pudo borrar el archivo %s del almacenamiento", nombre, exc_info=True)
        return False
    return True
