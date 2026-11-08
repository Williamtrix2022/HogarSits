"""Piezas de formulario compartidas."""


class AccesibleFormMixin:
    """Tras validar, enlaza cada campo con su error para los lectores de pantalla."""

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:  # los errores generales no pertenecen a un campo
                atributos = self.fields[nombre].widget.attrs
                atributos["aria-invalid"] = "true"
                atributos["aria-describedby"] = f"error-{nombre}"
