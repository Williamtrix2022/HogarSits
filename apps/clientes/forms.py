import re

from django import forms
from django.db.models import F, Q, Value
from django.db.models.functions import Replace

from apps.comun.formularios import AccesibleFormMixin

from .models import Cliente

PATRON_TELEFONO = re.compile(r"^\+?[0-9 ()\-]+$")


def solo_digitos(telefono: str) -> str:
    return re.sub(r"\D", "", telefono or "")


class ClienteForm(AccesibleFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ("nombre", "correo", "telefono")
        labels = {"nombre": "Nombre completo", "correo": "Correo", "telefono": "Teléfono"}
        error_messages = {
            "nombre": {"required": "Escriba el nombre del cliente."},
            "correo": {
                "required": "Escriba el correo del cliente.",
                "invalid": "Escriba un correo válido, por ejemplo ana@correo.com.",
            },
            "telefono": {"required": "Escriba un teléfono de contacto."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefono"].widget.attrs.update(
            {"inputmode": "tel", "placeholder": "300 123 4567"}
        )
        self.fields["correo"].widget.attrs.update({"autocomplete": "off"})

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 letras.")
        return nombre

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()
        existente = (
            Cliente.objects.filter(correo__iexact=correo).exclude(pk=self.instance.pk).first()
        )
        if existente:  # RN-10: un correo identifica a un cliente
            raise forms.ValidationError(
                f"Ya existe un cliente con este correo: {existente.nombre}. "
                "Búsquelo en la lista en lugar de crear otro."
            )
        return correo

    def clean_telefono(self):
        telefono = " ".join(self.cleaned_data["telefono"].split())
        if not PATRON_TELEFONO.match(telefono) or not 7 <= len(solo_digitos(telefono)) <= 15:
            raise forms.ValidationError(
                "Escriba un teléfono válido de 7 a 15 dígitos (puede llevar +, espacios o guiones)."
            )
        return telefono

    def clientes_con_mismo_telefono(self):
        """RN-10 deja el teléfono como aviso, no como bloqueo: dos personas pueden compartirlo."""
        digitos = solo_digitos(self.cleaned_data.get("telefono", ""))
        if not digitos:
            return []
        otros = Cliente.objects.exclude(pk=self.instance.pk)
        return [c for c in otros if solo_digitos(c.telefono) == digitos]


class FiltroClienteForm(forms.Form):
    q = forms.CharField(
        label="Buscar por nombre, correo o teléfono", required=False, max_length=100
    )

    @property
    def hay_filtros(self) -> bool:
        return self.is_bound and bool(self.cleaned_data.get("q"))

    def aplicar(self, queryset):
        q = (getattr(self, "cleaned_data", {}).get("q") or "").strip()
        if not q:
            return queryset
        filtro = Q(nombre__icontains=q) | Q(correo__icontains=q) | Q(telefono__icontains=q)
        digitos = solo_digitos(q)
        if digitos:  # «3110000000» debe encontrar «311 000 0000»
            sin_separadores = F("telefono")
            for separador in (" ", "-", "(", ")", "+"):
                sin_separadores = Replace(sin_separadores, Value(separador), Value(""))
            queryset = queryset.annotate(telefono_digitos=sin_separadores)
            filtro |= Q(telefono_digitos__contains=digitos)
        return queryset.filter(filtro)
