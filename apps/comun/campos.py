"""Campos de formulario compartidos."""

import re

from django import forms

# 1.300.000 o 240.000.000 (puntos como separador de miles)
_MILES = re.compile(r"\d{1,3}(\.\d{3})+")


class PesosField(forms.DecimalField):
    """Dinero en pesos colombianos, escrito como lo escribe la gente.

    Acepta ``240000000``, ``240.000.000``, ``$ 240.000.000`` y ``1.300.000,50`` (coma decimal).
    Un punto solo se toma como separador de miles cuando agrupa de a tres dígitos
    (``1.300.000``); en cualquier otro caso se respeta como decimal (``1.5``).
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("min_value", 0)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("widget", forms.TextInput(attrs={"inputmode": "numeric"}))
        mensajes = {
            "invalid": "Escriba solo números, por ejemplo 240.000.000.",
            "min_value": "El valor debe ser mayor o igual que %(limit_value)s.",
        }
        mensajes.update(kwargs.pop("error_messages", {}))
        kwargs["error_messages"] = mensajes
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            texto = value.strip().replace("$", "").replace(" ", "")
            if "," in texto:
                texto = texto.replace(".", "").replace(",", ".")
            elif _MILES.fullmatch(texto):
                texto = texto.replace(".", "")
            value = texto
        return super().to_python(value)
