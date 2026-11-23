from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.comun.formularios import AccesibleFormMixin
from apps.inmuebles.services import MENSAJE_NO_OFRECIBLE, inmuebles_ofrecibles
from apps.seguimiento.models import SolicitudAtencion

from . import services

User = get_user_model()

DURACIONES = [(30, "30 minutos"), (45, "45 minutos"), (60, "1 hora"), (90, "1 hora 30 min"),
              (120, "2 horas")]
FORMATOS_FECHA_HORA = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]


class _HorarioMixin(forms.Form):
    inicio = forms.DateTimeField(
        label="Fecha y hora de inicio",
        input_formats=FORMATOS_FECHA_HORA,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        error_messages={
            "required": "Indique cuándo empieza la visita.",
            "invalid": "Escriba una fecha y hora válidas.",
        },
    )
    duracion = forms.TypedChoiceField(
        label="Duración", choices=DURACIONES, coerce=int, initial=60
    )


class VisitaForm(AccesibleFormMixin, _HorarioMixin):
    solicitud = forms.ModelChoiceField(
        queryset=SolicitudAtencion.objects.none(),
        label="Solicitud",
        empty_label="Elija la solicitud del cliente",
        error_messages={
            "required": "Elija la solicitud para la que se agenda.",
            "invalid_choice": "Solo se agendan visitas para solicitudes abiertas.",
        },
    )
    inmueble = forms.ModelChoiceField(
        queryset=inmuebles_ofrecibles().none(),
        label="Inmueble",
        empty_label="Elija el inmueble",
        error_messages={"required": "Elija el inmueble a visitar.",
                        "invalid_choice": MENSAJE_NO_OFRECIBLE},
    )
    asesor = forms.ModelChoiceField(
        queryset=User.objects.none(), label="Asesor",
        error_messages={"required": "Elija el asesor que hará la visita."},
    )
    notas = forms.CharField(label="Notas", required=False, max_length=255)

    field_order = ["solicitud", "inmueble", "asesor", "inicio", "duracion", "notas"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["solicitud"].queryset = SolicitudAtencion.objects.filter(
            estado__in=services.SOLICITUD_ABIERTA
        ).select_related("cliente").order_by("timestamp_llegada")
        self.fields["solicitud"].label_from_instance = (
            lambda s: f"{s.cliente.nombre} · {s.get_tipo_interes_display()} "
                      f"({timezone.localtime(s.timestamp_llegada):%d/%m %H:%M})"
        )
        self.fields["inmueble"].queryset = inmuebles_ofrecibles().order_by("titulo")
        self.fields["asesor"].queryset = User.objects.filter(is_active=True).order_by(
            "first_name", "username"
        )
        self.fields["asesor"].label_from_instance = lambda u: u.get_full_name() or u.username

    def clean(self):
        datos = super().clean()
        campos = ("solicitud", "inmueble", "asesor", "inicio", "duracion")
        if all(datos.get(c) is not None for c in campos):
            fin = datos["inicio"] + timedelta(minutes=datos["duracion"])
            try:
                services.verificar_visita(
                    datos["solicitud"], datos["inmueble"], datos["asesor"], datos["inicio"], fin
                )
            except services.AgendaError as error:
                raise forms.ValidationError(str(error)) from error
        return datos


class ReprogramarForm(AccesibleFormMixin, _HorarioMixin):
    """Solo cambia el horario; el resto de la visita se conserva."""

    def __init__(self, *args, visita, **kwargs):
        super().__init__(*args, **kwargs)
        self.visita = visita
        actual = int((visita.fin - visita.inicio).total_seconds() // 60)
        self.initial.setdefault("duracion", actual)
        if actual not in dict(DURACIONES):  # una duración fuera de la lista sigue siendo elegible
            self.fields["duracion"].choices = [*DURACIONES, (actual, f"{actual} minutos (actual)")]

    def clean(self):
        datos = super().clean()
        if datos.get("inicio") and datos.get("duracion"):
            v = self.visita
            fin = datos["inicio"] + timedelta(minutes=datos["duracion"])
            try:
                # La original se cancela al reprogramar, así que no cuenta como cruce.
                services.verificar_visita(v.solicitud, v.inmueble, v.asesor, datos["inicio"],
                                          fin, excluir_pk=v.pk)
            except services.AgendaError as error:
                raise forms.ValidationError(str(error)) from error
        return datos
