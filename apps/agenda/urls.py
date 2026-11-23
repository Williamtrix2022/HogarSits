from django.urls import path

from . import views

app_name = "agenda"

urlpatterns = [
    path("", views.AgendaSemanaView.as_view(), name="semana"),
    path("nueva/", views.VisitaCrearView.as_view(), name="crear"),
    path("<int:pk>/reprogramar/", views.VisitaReprogramarView.as_view(), name="reprogramar"),
    path("<int:pk>/cancelar/", views.CancelarVisitaView.as_view(), name="cancelar"),
    path("<int:pk>/realizada/", views.RealizarVisitaView.as_view(), name="realizar"),
]
