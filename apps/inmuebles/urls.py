from django.urls import path

from . import views

app_name = "inmuebles"

urlpatterns = [
    path("", views.InmuebleListView.as_view(), name="lista"),
    path("nuevo/", views.InmuebleCrearView.as_view(), name="crear"),
    path("<int:pk>/", views.InmuebleEditarView.as_view(), name="editar"),
    path("<int:pk>/activo/", views.InmuebleActivoView.as_view(), name="activo"),
]
