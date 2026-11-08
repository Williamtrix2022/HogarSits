from django.contrib import admin

from .models import SeguimientoEtapa, SolicitudAtencion


class SeguimientoInline(admin.TabularInline):
    model = SeguimientoEtapa
    extra = 0


@admin.register(SolicitudAtencion)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "id", "cliente", "tipo_interes", "estado", "etapa_actual", "asesor", "timestamp_llegada",
    )
    list_filter = ("estado", "etapa_actual", "tipo_interes")
    inlines = [SeguimientoInline]


admin.site.register(SeguimientoEtapa)
