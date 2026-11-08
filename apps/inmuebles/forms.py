from django import forms
from django.db.models import Q

from apps.comun.campos import PesosField
from apps.comun.formularios import AccesibleFormMixin

from .models import Inmueble

ESTADO_INCOHERENTE = {
    # (operación, estado): mensaje que dice qué hacer
    (Inmueble.Operacion.VENTA, Inmueble.Estado.ARRENDADO): (
        "Una venta no puede quedar como Arrendada. Elija Vendido."
    ),
    (Inmueble.Operacion.ALQUILER, Inmueble.Estado.VENDIDO): (
        "Un alquiler no puede quedar como Vendido. Elija Arrendado."
    ),
}


class InmuebleForm(AccesibleFormMixin, forms.ModelForm):
    precio = PesosField(
        label="Precio (COP)",
        min_value=1,
        decimal_places=0,
        error_messages={
            "required": "Escriba el precio del inmueble.",
            "min_value": "El precio debe ser mayor que 0.",
        },
    )
    area_m2 = forms.DecimalField(
        label="Área (m²)", required=False, min_value=0, decimal_places=2, localize=True
    )

    class Meta:
        model = Inmueble
        fields = (
            "titulo", "tipo_inmueble", "operacion", "direccion", "barrio",
            "precio", "area_m2", "habitaciones", "estado", "descripcion", "activo",
        )
        labels = {
            "titulo": "Título",
            "tipo_inmueble": "Tipo de inmueble",
            "operacion": "Operación",
            "direccion": "Dirección",
            "barrio": "Barrio",
            "habitaciones": "Habitaciones",
            "estado": "Estado",
            "descripcion": "Descripción",
            "activo": "Activo (visible en las listas)",
        }
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["precio"].widget.attrs.update({"placeholder": "Ej. 240.000.000"})
        self.fields["habitaciones"].widget.attrs.update({"min": 0, "max": 50})
        if self.instance.pk:
            self.initial["precio"] = f"{int(self.instance.precio):,}".replace(",", ".")
        else:
            del self.fields["activo"]  # un inmueble nuevo siempre nace activo (default del modelo)

    def clean_area_m2(self):
        area = self.cleaned_data.get("area_m2")
        if area is not None and area <= 0:
            raise forms.ValidationError("El área debe ser mayor que 0 m².")
        return area

    def clean(self):
        datos = super().clean()
        mensaje = ESTADO_INCOHERENTE.get((datos.get("operacion"), datos.get("estado")))
        if mensaje:
            self.add_error("estado", mensaje)
        return datos


class FiltroInmuebleForm(forms.Form):
    """Filtros de la lista (se envían por GET, así el resultado se puede compartir como enlace)."""

    q = forms.CharField(label="Buscar", required=False, max_length=100)
    estado = forms.ChoiceField(
        label="Estado", required=False, choices=[("", "Todos")] + Inmueble.Estado.choices
    )
    operacion = forms.ChoiceField(
        label="Operación", required=False, choices=[("", "Todas")] + Inmueble.Operacion.choices
    )
    tipo_inmueble = forms.ChoiceField(
        label="Tipo", required=False, choices=[("", "Todos")] + Inmueble.TipoInmueble.choices
    )
    precio_min = PesosField(label="Precio desde", required=False, decimal_places=0)
    precio_max = PesosField(label="Precio hasta", required=False, decimal_places=0)
    incluir_inactivos = forms.BooleanField(label="Incluir inactivos", required=False)

    def clean(self):
        datos = super().clean()
        minimo, maximo = datos.get("precio_min"), datos.get("precio_max")
        if minimo is not None and maximo is not None and minimo > maximo:
            self.add_error("precio_max", "El precio máximo debe ser mayor o igual que el mínimo.")
        return datos

    @property
    def hay_filtros(self) -> bool:
        return self.is_bound and any(self.cleaned_data.get(c) for c in self.fields)

    def aplicar(self, queryset):
        """Devuelve el queryset filtrado. Con filtros inválidos no filtra por los inválidos."""
        d = getattr(self, "cleaned_data", {})
        if not d.get("incluir_inactivos"):
            queryset = queryset.filter(activo=True)
        if d.get("q"):
            q = d["q"].strip()
            queryset = queryset.filter(
                Q(titulo__icontains=q) | Q(direccion__icontains=q) | Q(barrio__icontains=q)
            )
        for campo in ("estado", "operacion", "tipo_inmueble"):
            if d.get(campo):
                queryset = queryset.filter(**{campo: d[campo]})
        if d.get("precio_min") is not None:
            queryset = queryset.filter(precio__gte=d["precio_min"])
        if d.get("precio_max") is not None:
            queryset = queryset.filter(precio__lte=d["precio_max"])
        return queryset
