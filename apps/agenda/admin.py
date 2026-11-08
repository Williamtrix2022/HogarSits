from django.contrib import admin

from .models import HorarioAsesor, Visita


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ("id", "inmueble", "asesor", "inicio", "fin", "estado")
    list_filter = ("estado", "asesor")


@admin.register(HorarioAsesor)
class HorarioAsesorAdmin(admin.ModelAdmin):
    list_display = ("asesor", "dia_semana", "hora_inicio", "hora_fin")
