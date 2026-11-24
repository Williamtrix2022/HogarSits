from django.urls import path

from . import views

app_name = "analitica"

urlpatterns = [
    path("", views.PanelView.as_view(), name="inicio"),
    path("asesores/", views.AsesoresView.as_view(), name="asesores"),
    path("exportar/", views.ExportarView.as_view(), name="exportar"),
]
