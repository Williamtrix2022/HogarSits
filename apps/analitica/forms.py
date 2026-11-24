from datetime import timedelta

from django import forms

from apps.comun.formularios import AccesibleFormMixin

MAX_DIAS = 366


class FiltroPeriodoForm(AccesibleFormMixin, forms.Form):
    """Rango de fechas del análisis y de los indicadores por asesor (RF-56, HU-13)."""

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

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta:
            if desde > hasta:
                self.add_error("hasta", "La fecha final debe ser igual o posterior a la inicial.")
            elif hasta - desde > timedelta(days=MAX_DIAS - 1):
                self.add_error("hasta", f"Elija un rango de como máximo {MAX_DIAS} días.")
        return datos


class FiltroAnalisisForm(FiltroPeriodoForm):
    """El rango y, además, el umbral de espera aceptable del panel de análisis (RF-53)."""

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
