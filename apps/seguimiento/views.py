from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from apps.cuentas.roles import es_admin
from apps.inmuebles import services as inmuebles_services

from . import services
from .forms import EtapaForm, FiltroSolicitudForm, SolicitudForm
from .models import Etapa, SolicitudAtencion


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


class SolicitudDetalleView(DetailView):
    """W9: etapa actual, historial de transiciones, visitas y registro de un seguimiento."""

    model = SolicitudAtencion
    template_name = "seguimiento/detalle.html"
    context_object_name = "solicitud"

    def get_queryset(self):
        return SolicitudAtencion.objects.select_related("cliente", "inmueble", "asesor")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        s = self.object
        ctx["form"] = kwargs.get("form") or EtapaForm(solicitud=s)
        ctx["puede_registrar"] = bool(services.destinos_permitidos(s))
        ctx["etapas"] = [
            {
                "etapa": e,
                "hecha": e.value < s.etapa_actual and s.etapa_actual != Etapa.ABANDONO,
                "actual": e.value == s.etapa_actual,
            }
            for e in (Etapa.CONSULTA, Etapa.VISITA, Etapa.NEGOCIACION, Etapa.CIERRE)
        ]
        ctx["abandonada"] = s.etapa_actual == Etapa.ABANDONO
        historial = list(
            s.seguimientos.select_related("registrado_por").order_by("-fecha_transicion", "-id")
        )
        for t in historial:
            t.sin_avance = services.es_autotransicion(t)
        ctx["historial"] = historial
        ctx["visitas"] = s.visitas.select_related("inmueble", "asesor").order_by("-inicio")
        return ctx


class RegistrarEtapaView(View):
    """Registra el seguimiento. Si falla la validación, vuelve a mostrar el detalle con errores."""

    http_method_names = ["post"]

    def post(self, request, pk):
        solicitud = get_object_or_404(
            SolicitudAtencion.objects.select_related("cliente", "inmueble"), pk=pk
        )
        form = EtapaForm(request.POST, solicitud=solicitud)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                transicion = services.registrar_etapa(
                    solicitud, datos["etapa"], request.user, datos["nota"]
                )
            except services.TransicionInvalida as error:
                messages.error(request, str(error))
            else:
                self._avisar(request, solicitud, transicion, datos.get("marcar_inmueble"))
            return redirect("seguimiento:detalle", pk=pk)
        vista = SolicitudDetalleView()
        vista.setup(request, pk=pk)
        vista.object = solicitud
        return vista.render_to_response(vista.get_context_data(form=form), status=200)

    def _avisar(self, request, solicitud, transicion, marcar_inmueble):
        destino = Etapa(transicion.estado_destino)
        if services.es_autotransicion(transicion):
            messages.success(request, f"Seguimiento registrado: sigue en {destino.label}.")
        else:
            messages.success(request, f"{solicitud.cliente.nombre}: ahora en {destino.label}.")
        inmueble = solicitud.inmueble
        if destino != Etapa.CIERRE or inmueble is None:
            return
        nuevo = inmuebles_services.estado_de_cierre(inmueble)
        if marcar_inmueble:  # RN-05 / RF-43
            inmuebles_services.cambiar_estado(inmueble, nuevo, request.user)
            messages.success(request, f"«{inmueble.titulo}» quedó como {nuevo.label}.")
        else:
            messages.warning(
                request,
                f"Cierre registrado. Recuerde actualizar «{inmueble.titulo}» a {nuevo.label}.",
            )


class PendientesView(TemplateView):
    """Todas las solicitudes con seguimiento pendiente. El administrador ve todo el equipo."""

    template_name = "seguimiento/pendientes.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        User = get_user_model()
        usuario = self.request.user
        admin = es_admin(usuario)
        elegido = None
        if admin:
            pedido = self.request.GET.get("asesor", "")
            elegido = User.objects.filter(pk=int(pedido)).first() if pedido.isdigit() else None
            ctx["asesores"] = User.objects.filter(is_active=True).order_by("first_name", "username")
            ctx["asesor_elegido"] = elegido
        pendientes = services.pendientes_de_seguimiento(asesor=elegido if admin else usuario)
        ctx.update(
            pendientes=pendientes,
            dias_umbral=services.dias_sin_seguimiento(),
            total_sin_seguimiento=sum(p.sin_seguimiento for p in pendientes),
        )
        return ctx
