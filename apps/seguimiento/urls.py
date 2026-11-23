from django.urls import path

from . import views

app_name = "seguimiento"

urlpatterns = [
    path("", views.ColaListView.as_view(), name="cola"),
    path("pendientes/", views.PendientesView.as_view(), name="pendientes"),
    path("nueva/", views.SolicitudCrearView.as_view(), name="crear"),
    path("<int:pk>/", views.SolicitudDetalleView.as_view(), name="detalle"),
    path("<int:pk>/etapa/", views.RegistrarEtapaView.as_view(), name="etapa"),
    path("<int:pk>/tomar/", views.TomarView.as_view(), name="tomar"),
    path("<int:pk>/finalizar/", views.FinalizarView.as_view(), name="finalizar"),
    path("<int:pk>/cancelar/", views.CancelarView.as_view(), name="cancelar"),
]
