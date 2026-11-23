from django.urls import path

from . import views_horario as views

app_name = "horarios"

urlpatterns = [
    path("", views.HorariosListaView.as_view(), name="lista"),
    path("disponibilidad/", views.DisponibilidadView.as_view(), name="disponibilidad"),
    path("<int:pk>/", views.HorarioAsesorView.as_view(), name="asesor"),
    path("turno/<int:pk>/borrar/", views.TurnoBorrarView.as_view(), name="borrar"),
]
