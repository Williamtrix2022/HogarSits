from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, ListView

from apps.cuentas.roles import es_admin

from . import services
from .forms import FiltroSolicitudForm, SolicitudForm
from .models import SolicitudAtencion


class ColaListView(ListView):
    """La cola de atención: lo que espera primero, arriba (orden de llegada)."""

    model = SolicitudAtencion
    template_name = "seguimiento/cola.html"
    context_object_name = "solicitudes"
    paginate_by = 20

    def get_queryset(self):
        self.filtro = FiltroSolicitudForm(self.request.GET or None)
        self.filtro.is_valid()
        base = SolicitudAtencion.objects.select_related("cliente", "inmueble", "asesor")
        return self.filtro.aplicar(base).order_by("timestamp_llegada", "id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filtro"] = self.filtro
        ctx["hay_filtros"] = self.filtro.hay_filtros
        ctx["querystring"] = params.urlencode()
        for s in ctx["solicitudes"]:  # RN-21, calculado una vez por fila
            s.espera = services.tiempo_espera(s)
            s.servicio = services.tiempo_servicio(s)
        return ctx


class SolicitudCrearView(CreateView):
    model = SolicitudAtencion
    form_class = SolicitudForm
    template_name = "seguimiento/formulario.html"
    success_url = reverse_lazy("seguimiento:cola")
    extra_context = {"titulo": "Nueva solicitud de atención"}

    def get_initial(self):
        inicial = super().get_initial()
        if self.request.GET.get("cliente", "").isdigit():
            inicial["cliente"] = int(self.request.GET["cliente"])
        return inicial

    def form_valid(self, form):
        respuesta = super().form_valid(form)  # la llegada la pone el modelo (RN-11)
        messages.success(
            self.request, f"Solicitud de {self.object.cliente.nombre} registrada: en espera."
        )
        return respuesta


class TransicionView(View):
    """Base de las acciones sobre una solicitud (solo POST)."""

    http_method_names = ["post"]
    mensaje_ok = ""

    def ejecutar(self, request, solicitud):
        raise NotImplementedError

    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudAtencion.objects.select_related("cliente"), pk=pk)
        try:
            self.ejecutar(request, solicitud)
        except services.TransicionInvalida as error:
            messages.error(request, str(error))
        else:
            messages.success(request, self.mensaje_ok.format(cliente=solicitud.cliente.nombre))
        destino = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
            destino = reverse("seguimiento:cola")  # nunca se redirige fuera del sitio
        return redirect(destino)


class TomarView(TransicionView):
    mensaje_ok = "Atiende a {cliente}: la solicitud quedó en atención."

    def ejecutar(self, request, solicitud):
        services.tomar(solicitud, request.user)


class FinalizarView(TransicionView):
    mensaje_ok = "Atención de {cliente} finalizada."

    def ejecutar(self, request, solicitud):
        services.finalizar(solicitud, request.user, es_admin=es_admin(request.user))


class CancelarView(TransicionView):
    mensaje_ok = "Solicitud de {cliente} cancelada."

    def ejecutar(self, request, solicitud):
        services.cancelar(solicitud)
