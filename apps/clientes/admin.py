from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "correo", "telefono", "fecha_registro")
    search_fields = ("nombre", "correo", "telefono")
