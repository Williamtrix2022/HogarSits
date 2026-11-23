from django import forms

from apps.clientes.models import Cliente
from apps.comun.campos import PesosField
from apps.comun.formularios import AccesibleFormMixin
from apps.inmuebles.services import MENSAJE_NO_OFRECIBLE, inmuebles_ofrecibles

from .models import SolicitudAtencion


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
