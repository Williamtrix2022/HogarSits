from django import forms

from apps.comun.formularios import AccesibleFormMixin

from .models import HorarioAsesor


class TurnoForm(AccesibleFormMixin, forms.Form):
    """Agrega un turno a varios días de una vez (p. ej. Lun–Vie 08:00–12:00)."""

    dias = forms.TypedMultipleChoiceField(
        label="Días",
        choices=HorarioAsesor.Dia.choices,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": "Marque al menos un día."},
    )
    hora_inicio = forms.TimeField(
        label="Desde",
        input_formats=["%H:%M"],
        widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        error_messages={"required": "Indique la hora de inicio.", "invalid": "Hora no válida."},
    )
    hora_fin = forms.TimeField(
        label="Hasta",
        input_formats=["%H:%M"],
        widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        error_messages={"required": "Indique la hora de fin.", "invalid": "Hora no válida."},
    )

    def __init__(self, *args, asesor, **kwargs):
        super().__init__(*args, **kwargs)
        self.asesor = asesor

    def clean(self):
        datos = super().clean()
        inicio, fin, dias = datos.get("hora_inicio"), datos.get("hora_fin"), datos.get("dias")
        if inicio is None or fin is None or not dias:
            return datos
        if fin <= inicio:
            self.add_error("hora_fin", "La hora de fin debe ser posterior a la de inicio.")
            return datos
        existentes = HorarioAsesor.objects.filter(asesor=self.asesor, dia_semana__in=dias)
        for turno in existentes:
            if inicio < turno.hora_fin and turno.hora_inicio < fin:  # se solapan
                dia = HorarioAsesor.Dia(turno.dia_semana).label.lower()
                raise forms.ValidationError(
                    f"Ya tiene un turno el {dia} de {turno.hora_inicio:%H:%M} a "
                    f"{turno.hora_fin:%H:%M}, que se cruza con este. Edítelo o elija otra hora."
                )
        return datos

    def guardar(self) -> int:
        d = self.cleaned_data
        turnos = [
            HorarioAsesor(
                asesor=self.asesor,
                dia_semana=dia,
                hora_inicio=d["hora_inicio"],
                hora_fin=d["hora_fin"],
            )
            for dia in d["dias"]
        ]
        HorarioAsesor.objects.bulk_create(turnos)
        return len(turnos)


def horas_semana(turnos) -> float:
    """Horas semanales que suman los turnos de un asesor."""
    total = 0
    for t in turnos:
        minutos = (t.hora_fin.hour * 60 + t.hora_fin.minute) - (
            t.hora_inicio.hour * 60 + t.hora_inicio.minute
        )
        total += minutos
    return round(total / 60, 1)

