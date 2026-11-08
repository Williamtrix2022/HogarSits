from django.contrib import admin

from .models import FotoInmueble, HistorialEstadoInmueble, Inmueble


class FotoInline(admin.TabularInline):
    model = FotoInmueble
    extra = 0


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo_inmueble", "operacion", "precio", "estado", "activo")
    list_filter = ("estado", "operacion", "tipo_inmueble", "activo")
    search_fields = ("titulo", "direccion", "barrio")
    inlines = [FotoInline]


@admin.register(HistorialEstadoInmueble)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ("inmueble", "estado_anterior", "estado_nuevo", "cambiado_por", "fecha")
