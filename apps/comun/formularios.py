"""Piezas de formulario compartidas."""

from django.db.models.fields import BLANK_CHOICE_LABEL

OPCION_VACIA = "Elija una opción"


class AccesibleFormMixin:
    """Enlaza cada campo con su error para lectores de pantalla y traduce la opción vacía.

    Django no trae en español el texto «- Select an option -» que usa para los campos con
    opciones; se reemplaza aquí para que ninguna pantalla muestre inglés.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ingles = str(BLANK_CHOICE_LABEL)
        for campo in self.fields.values():
            if not hasattr(campo, "choices"):
                continue
            opciones = list(campo.choices)  # Django usa un iterador (BlankChoiceIterator)
            if any(valor == "" and str(etiqueta) == ingles for valor, etiqueta in opciones):
                campo.choices = [
                    (valor, OPCION_VACIA if valor == "" and str(etiqueta) == ingles else etiqueta)
                    for valor, etiqueta in opciones
                ]

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:  # los errores generales no pertenecen a un campo
                atributos = self.fields[nombre].widget.attrs
                atributos["aria-invalid"] = "true"
                atributos["aria-describedby"] = f"error-{nombre}"
