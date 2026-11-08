from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def pesos(valor):
    """240000000 -> «$ 240.000.000». Vacío -> «—»."""
    if valor in (None, ""):
        return "—"
    entero = int(Decimal(valor).quantize(Decimal(1)))
    return "$ " + f"{entero:,}".replace(",", ".")


@register.filter
def pesos_entrada(valor):
    """Valor para precargar un campo de dinero: 240000000.00 -> «240.000.000»."""
    if valor in (None, ""):
        return ""
    entero = int(Decimal(valor).quantize(Decimal(1)))
    return f"{entero:,}".replace(",", ".")
