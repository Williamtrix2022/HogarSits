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
def duracion(valor):
    """timedelta -> «45 s», «12 min», «1 h 05 min». Vacío -> «—»."""
    if valor is None:
        return "—"
    segundos = max(0, int(valor.total_seconds()))
    if segundos < 60:
        return f"{segundos} s"
    minutos = segundos // 60
    if minutos < 60:
        return f"{minutos} min"
    horas, resto = divmod(minutos, 60)
    return f"{horas} h {resto:02d} min"


@register.filter
def pesos_entrada(valor):
    """Valor para precargar un campo de dinero: 240000000.00 -> «240.000.000»."""
    if valor in (None, ""):
        return ""
    entero = int(Decimal(valor).quantize(Decimal(1)))
    return f"{entero:,}".replace(",", ".")
