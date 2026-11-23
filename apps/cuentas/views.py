from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView, TemplateView, UpdateView

from apps.agenda import services as agenda_services
from apps.seguimiento import services as seguimiento_services
from apps.seguimiento.models import SolicitudAtencion

from . import bloqueo
from .forms import (
    CambiarClaveForm,
    RestablecerClaveForm,
    UsuarioCrearForm,
    UsuarioEditarForm,
)
from .roles import administradores_activos, es_admin, rol_de

User = get_user_model()


class AdminRequeridoMixin(UserPassesTestMixin):
    """Solo administradores. Un asesor autenticado recibe 403; un anónimo va al login."""

    def test_func(self):
        return es_admin(self.request.user)


class InicioView(TemplateView):
    """Pantalla «Hogar»: a quién contactar hoy y mis visitas (HU-12, RF-25, RF-26, RF-35).

    El asesor ve lo suyo. El administrador ve el total del equipo y puede filtrar por asesor.
    """

    template_name = "cuentas/inicio.html"
    MAX_EN_PANEL = 5

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario = self.request.user
        admin = es_admin(usuario)
        elegido = None
        if admin:
            pedido = self.request.GET.get("asesor", "")
            elegido = User.objects.filter(pk=int(pedido)).first() if pedido.isdigit() else None
            ctx["asesores"] = User.objects.filter(is_active=True).order_by("first_name", "username")
            ctx["asesor_elegido"] = elegido
        responsable = elegido if admin else usuario
        pendientes = seguimiento_services.pendientes_de_seguimiento(asesor=responsable)
        ctx.update(
            pendientes=pendientes[: self.MAX_EN_PANEL],
            total_pendientes=len(pendientes),
            total_sin_seguimiento=sum(p.sin_seguimiento for p in pendientes),
            dias_umbral=seguimiento_services.dias_sin_seguimiento(),
            en_espera=SolicitudAtencion.objects.filter(
                estado=SolicitudAtencion.Estado.EN_ESPERA
            ).count(),
            ver_equipo=admin and elegido is None,
        )
        visitas = agenda_services.visitas_proximas(responsable or usuario)
        ctx["visitas"] = visitas
        ctx["visitas_hoy"] = sum(v.es_hoy for v in visitas)
        return ctx


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


class CambiarClaveView(PasswordChangeView):
    """Cualquier usuario autenticado cambia su propia contraseña (la sesión se conserva)."""

    form_class = CambiarClaveForm
    template_name = "cuentas/clave_form.html"
    success_url = reverse_lazy("cuentas:inicio")
    extra_context = {"titulo": "Cambiar mi contraseña", "volver": reverse_lazy("cuentas:inicio")}

    def form_valid(self, form):
        messages.success(self.request, "Su contraseña se actualizó.")
        return super().form_valid(form)


class UsuarioRestablecerClaveView(AdminRequeridoMixin, FormView):
    """El administrador fija una contraseña nueva; también levanta un bloqueo por intentos."""

    form_class = RestablecerClaveForm
    template_name = "cuentas/clave_form.html"
    success_url = reverse_lazy("cuentas:usuarios")

    def dispatch(self, request, *args, **kwargs):
        self.usuario = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.usuario
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Restablecer contraseña: {self.usuario.username}"
        ctx["volver"] = reverse_lazy("cuentas:usuarios")
        return ctx

    def form_valid(self, form):
        form.save()
        bloqueo.limpiar_usuario(self.usuario.username)
        messages.success(self.request, f"Contraseña de {self.usuario.username} restablecida.")
        return super().form_valid(form)


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
