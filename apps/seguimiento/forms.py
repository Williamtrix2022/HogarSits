from django import forms

from apps.clientes.models import Cliente
from apps.comun.campos import PesosField
from apps.comun.formularios import AccesibleFormMixin
from apps.inmuebles import services as inmuebles_services
from apps.inmuebles.services import MENSAJE_NO_OFRECIBLE, inmuebles_ofrecibles

from . import services
from .models import Etapa, SolicitudAtencion


class SolicitudForm(AccesibleFormMixin, forms.ModelForm):
    """Alta de solicitud. La hora de llegada no se pide: la fija el sistema (RN-11)."""

    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.order_by("nombre"),
        label="Cliente",
        empty_label="Elija un cliente",
        error_messages={"required": "Elija el cliente que llegó."},
    )
    inmueble = forms.ModelChoiceField(
        queryset=inmuebles_ofrecibles().none(),
        label="Inmueble de interés",
        required=False,
        empty_label="Sin inmueble definido",
        error_messages={"invalid_choice": MENSAJE_NO_OFRECIBLE},  # RN-03
    )
    presupuesto = PesosField(
        label="Presupuesto (COP)", required=False, min_value=1, decimal_places=0,
        error_messages={"min_value": "El presupuesto debe ser mayor que 0."},
    )

    class Meta:
        model = SolicitudAtencion
        fields = ("cliente", "tipo_interes", "inmueble", "presupuesto")
        labels = {"tipo_interes": "Tipo de interés"}
        error_messages = {"tipo_interes": {"required": "Indique si busca comprar o alquilar."}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inmueble"].queryset = inmuebles_ofrecibles().order_by("titulo")
        self.fields["presupuesto"].widget.attrs.update({"placeholder": "Ej. 240.000.000"})


class FiltroSolicitudForm(forms.Form):
    """Por defecto la cola muestra lo abierto (en espera y en atención)."""

    ABIERTAS = "ABIERTAS"
    TODAS = "TODAS"

    estado = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[(ABIERTAS, "Abiertas"), (TODAS, "Todas")] + SolicitudAtencion.Estado.choices,
    )
    q = forms.CharField(label="Cliente", required=False, max_length=100)

    @property
    def hay_filtros(self) -> bool:
        d = getattr(self, "cleaned_data", {})
        estado_distinto = d.get("estado") not in (None, "", self.ABIERTAS)
        return self.is_bound and (bool(d.get("q")) or estado_distinto)

    def aplicar(self, queryset):
        d = getattr(self, "cleaned_data", {})
        estado = d.get("estado") or self.ABIERTAS
        if estado == self.ABIERTAS:
            abiertas = [SolicitudAtencion.Estado.EN_ESPERA, SolicitudAtencion.Estado.EN_ATENCION]
            queryset = queryset.filter(estado__in=abiertas)
        elif estado != self.TODAS:
            queryset = queryset.filter(estado=estado)
        if d.get("q"):
            queryset = queryset.filter(cliente__nombre__icontains=d["q"].strip())
        return queryset


class EtapaForm(AccesibleFormMixin, forms.Form):
    """Registrar un seguimiento: elegir a qué etapa pasa (o seguir en la misma) y una nota."""

    etapa = forms.TypedChoiceField(
        label="Resultado del seguimiento",
        coerce=int,
        error_messages={"required": "Elija a qué etapa pasa la solicitud."},
    )
    nota = forms.CharField(
        label="Nota de contacto", required=False, max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Ej. No contestó; se le escribe el lunes"}),
    )
    marcar_inmueble = forms.BooleanField(required=False)

    def __init__(self, *args, solicitud, **kwargs):
        super().__init__(*args, **kwargs)
        self.solicitud = solicitud
        actual = Etapa(solicitud.etapa_actual)
        opciones = []
        for destino in services.destinos_permitidos(solicitud):
            if destino == actual:
                opciones.append((destino.value, f"Seguir en {destino.label} (sin avance)"))
            elif destino == Etapa.ABANDONO:
                opciones.append((destino.value, "Marcar como Abandono"))
            else:
                opciones.append((destino.value, f"Pasar a {destino.label}"))
        self.fields["etapa"].choices = opciones
        inmueble = solicitud.inmueble
        if inmueble is not None:
            self.fields["marcar_inmueble"].label = (
                f"Al cerrar, marcar «{inmueble.titulo}» como "
                f"{inmuebles_services.estado_de_cierre(inmueble).label}"
            )
        else:
            del self.fields["marcar_inmueble"]
