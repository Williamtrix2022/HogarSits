from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "cuentas"

urlpatterns = [
    path("", views.InicioView.as_view(), name="inicio"),
    path(
        "ingresar/",
        auth_views.LoginView.as_view(
            template_name="cuentas/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("administracion/usuarios/", views.UsuarioListView.as_view(), name="usuarios"),
    path("administracion/componentes/", views.GuiaComponentesView.as_view(), name="componentes"),
    path("administracion/usuarios/nuevo/", views.UsuarioCrearView.as_view(), name="usuario_nuevo"),
    path(
        "administracion/usuarios/<int:pk>/editar/",
        views.UsuarioEditarView.as_view(),
        name="usuario_editar",
    ),
    path(
        "administracion/usuarios/<int:pk>/estado/",
        views.UsuarioCambiarEstadoView.as_view(),
        name="usuario_estado",
    ),
]
