from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import UsuarioCrearForm, UsuarioEditarForm
from .roles import administradores_activos, es_admin, rol_de

User = get_user_model()


class AdminRequeridoMixin(UserPassesTestMixin):
    """Solo administradores. Un asesor autenticado recibe 403; un anónimo va al login."""

    def test_func(self):
        return es_admin(self.request.user)


class InicioView(TemplateView):
    """Pantalla «Hogar». El panel «a quién contactar hoy» llega en el Sprint 4 (#33)."""

    template_name = "cuentas/inicio.html"


class GuiaComponentesView(AdminRequeridoMixin, TemplateView):
    """Catálogo vivo de la interfaz: sirve de referencia y de banco de pruebas visual."""

    template_name = "cuentas/guia_componentes.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["iconos"] = [
            "casa", "inmuebles", "clientes", "solicitudes", "agenda", "analisis",
            "administracion", "salir", "menu", "cerrar", "exito", "error", "info", "aviso",
        ]
        return ctx


class UsuarioListView(AdminRequeridoMixin, ListView):
    model = User
    template_name = "cuentas/usuarios_lista.html"
    context_object_name = "usuarios"
    ordering = ("-is_active", "username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filas"] = [(u, rol_de(u)) for u in ctx["usuarios"]]
        return ctx


class UsuarioCrearView(AdminRequeridoMixin, CreateView):
    form_class = UsuarioCrearForm
    template_name = "cuentas/usuario_form.html"
    success_url = reverse_lazy("cuentas:usuarios")
    extra_context = {"titulo": "Nuevo usuario"}

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f"Usuario {self.object.username} creado.")
        return respuesta


class UsuarioEditarView(AdminRequeridoMixin, UpdateView):
    model = User
    form_class = UsuarioEditarForm
    template_name = "cuentas/usuario_form.html"
    success_url = reverse_lazy("cuentas:usuarios")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["editor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Editar usuario: {self.object.username}"
        return ctx

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f"Usuario {self.object.username} actualizado.")
        return respuesta


class UsuarioCambiarEstadoView(AdminRequeridoMixin, View):
    """Activa o desactiva un usuario (los usuarios no se borran: tienen historial)."""

    http_method_names = ["post"]

    def post(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        if usuario.pk == request.user.pk:
            messages.error(request, "No puede desactivar su propia cuenta.")
        elif (
            usuario.is_active
            and es_admin(usuario)
            and not administradores_activos().exclude(pk=usuario.pk).exists()
        ):
            messages.error(request, "Debe quedar al menos un administrador activo.")
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=["is_active"])
            accion = "activado" if usuario.is_active else "desactivado"
            messages.success(request, f"Usuario {usuario.username} {accion}.")
        return redirect("cuentas:usuarios")
