from datetime import timedelta

from django import forms

from apps.comun.formularios import AccesibleFormMixin

MAX_DIAS = 366


class FiltroAnalisisForm(AccesibleFormMixin, forms.Form):
    """Rango de fechas y umbral de espera del panel de análisis (RF-56, RF-53)."""

    desde = forms.DateField(
        label="Desde",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"required": "Indique la fecha de inicio.", "invalid": "Fecha no válida."},
    )
    hasta = forms.DateField(
        label="Hasta",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"required": "Indique la fecha final.", "invalid": "Fecha no válida."},
    )
    espera_max = forms.IntegerField(
        label="Espera máxima aceptable (min)",
        min_value=1,
        max_value=240,
        initial=20,
        error_messages={
            "required": "Indique cuántos minutos de espera acepta.",
            "invalid": "Escriba un número de minutos.",
            "min_value": "La espera debe ser de al menos 1 minuto.",
            "max_value": "Use un valor de hasta 240 minutos.",
        },
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta:
            if desde > hasta:
                self.add_error("hasta", "La fecha final debe ser igual o posterior a la inicial.")
            elif hasta - desde > timedelta(days=MAX_DIAS - 1):
                self.add_error("hasta", f"Elija un rango de como máximo {MAX_DIAS} días.")
        return datos
