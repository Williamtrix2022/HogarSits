"""Menú principal de la aplicación.

Se declaran **todos** los destinos previstos; el menú solo muestra los que ya existen. Un destino
aparece solo en cuanto su URL se registra, sin tocar este archivo ni las plantillas, así que nunca
hay enlaces rotos y cada sprint «enciende» su sección. Los nombres de URL de los módulos futuros
(`inmuebles:lista`, …) son un contrato: el sprint que cree la sección debe usarlos.
"""

from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse


@dataclass(frozen=True)
class Destino:
    etiqueta: str
    url_name: str
    icono: str  # id en templates/componentes/iconos.svg.html (sin el prefijo «i-»)
    solo_admin: bool = False
    prefijo: str = ""  # si se indica, el ítem está activo en toda esa rama de URLs


MENU = (
    Destino("Hogar", "cuentas:inicio", "casa"),
    Destino("Inmuebles", "inmuebles:lista", "inmuebles"),  # #26
    Destino("Clientes", "clientes:lista", "clientes"),  # #28
    Destino("Solicitudes", "seguimiento:cola", "solicitudes"),  # #29
    Destino("Agenda", "agenda:semana", "agenda"),  # Sprint 4
    Destino("Análisis", "analitica:inicio", "analisis", solo_admin=True),  # Sprint 5
    Destino("Administración", "cuentas:usuarios", "administracion", True, "/administracion/"),
)


@dataclass(frozen=True)
class ItemMenu:
    etiqueta: str
    url: str
    icono: str
    activo: bool


def construir_menu(path: str, es_admin: bool, definicion=MENU) -> list[ItemMenu]:
    """Ítems visibles para el usuario, con el activo marcado. Omite destinos sin URL."""
    items = []
    for d in definicion:
        if d.solo_admin and not es_admin:
            continue
        try:
            url = reverse(d.url_name)
        except NoReverseMatch:
            continue
        if d.prefijo:
            activo = path.startswith(d.prefijo)
        elif url == "/":
            activo = path == "/"
        else:
            activo = path.startswith(url)
        items.append(ItemMenu(d.etiqueta, url, d.icono, activo))
    return items
