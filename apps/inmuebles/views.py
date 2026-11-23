from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import FiltroInmuebleForm, InmuebleForm
from .fotos import MAX_FOTOS, FotosForm, agregar_fotos, borrar_foto
from .models import FotoInmueble, Inmueble
from .services import ESTADOS_CERRADOS, cambiar_activo, guardar_inmueble, solicitudes_abiertas


class InmuebleListView(ListView):
    model = Inmueble
    template_name = "inmuebles/lista.html"
    context_object_name = "inmuebles"
    paginate_by = 20

    def get_queryset(self):
        self.filtro = FiltroInmuebleForm(self.request.GET or None)
        self.filtro.is_valid()  # deja cleaned_data con los filtros válidos
        return self.filtro.aplicar(Inmueble.objects.order_by("-creado_en", "-id"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filtro"] = self.filtro
        ctx["hay_filtros"] = self.filtro.hay_filtros
        ctx["querystring"] = params.urlencode()
        return ctx


class InmuebleCrearView(CreateView):
    model = Inmueble
    form_class = InmuebleForm
    template_name = "inmuebles/formulario.html"
    success_url = reverse_lazy("inmuebles:lista")
    extra_context = {"titulo": "Nuevo inmueble"}

    def form_valid(self, form):
        self.object = guardar_inmueble(form, self.request.user)
        messages.success(self.request, f"Inmueble «{self.object.titulo}» creado.")
        return redirect(self.get_success_url())


class InmuebleEditarView(UpdateView):
    model = Inmueble
    form_class = InmuebleForm
    template_name = "inmuebles/formulario.html"

    def get_success_url(self):
        return reverse("inmuebles:lista")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Inmueble: {self.object.titulo}"
        ctx["historial"] = self.object.historial_estados.select_related("cambiado_por")[:20]
        fotos = list(self.object.fotos.all())
        ctx["fotos"] = fotos
        ctx["foto_form"] = FotosForm(inmueble=self.object)
        ctx["caben_fotos"] = max(MAX_FOTOS - len(fotos), 0)
        ctx["max_fotos"] = MAX_FOTOS
        return ctx

    def form_valid(self, form):
        self.object = guardar_inmueble(form, self.request.user)
        messages.success(self.request, f"Inmueble «{self.object.titulo}» actualizado.")
        abiertas = solicitudes_abiertas(self.object)
        if self.object.estado in ESTADOS_CERRADOS and abiertas:  # RF-15
            messages.warning(
                self.request,
                f"Este inmueble ya está {self.object.get_estado_display().lower()} y tiene "
                f"{abiertas} solicitud(es) abierta(s). Conviene avisar a esos clientes.",
            )
        return redirect(self.get_success_url())


class InmuebleActivoView(View):
    """Desactiva o reactiva un inmueble. Se desactiva en lugar de borrar (RF-10)."""

    http_method_names = ["post"]

    def post(self, request, pk):
        inmueble = get_object_or_404(Inmueble, pk=pk)
        cambiar_activo(inmueble, not inmueble.activo)
        if inmueble.activo:
            messages.success(request, f"Inmueble «{inmueble.titulo}» activado.")
        else:
            messages.success(
                request,
                f"Inmueble «{inmueble.titulo}» desactivado. "
                "Lo verá de nuevo con «Incluir inactivos».",
            )
        destino = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
            destino = reverse("inmuebles:lista")  # nunca se redirige fuera del sitio
        return redirect(destino)


class FotoSubirView(View):
    """Agrega una o varias fotos al inmueble (RF-13)."""

    http_method_names = ["post"]

    def post(self, request, pk):
        inmueble = get_object_or_404(Inmueble, pk=pk)
        form = FotosForm(request.POST, request.FILES, inmueble=inmueble)
        if form.is_valid():
            cantidad = len(agregar_fotos(inmueble, form.cleaned_data["imagenes"]))
            messages.success(request, f"{cantidad} foto(s) agregada(s) a «{inmueble.titulo}».")
        else:
            for error in form.errors["imagenes"]:
                messages.error(request, error)
        return redirect("inmuebles:editar", pk=pk)


class FotoBorrarView(View):
    http_method_names = ["post"]

    def post(self, request, pk):
        foto = get_object_or_404(FotoInmueble.objects.select_related("inmueble"), pk=pk)
        inmueble_pk = foto.inmueble_id
        if borrar_foto(foto):
            messages.success(request, "Foto eliminada.")
        else:
            messages.warning(
                request,
                "La foto se quitó del inmueble, pero el archivo no pudo borrarse del "
                "almacenamiento. Avise al administrador.",
            )
        return redirect("inmuebles:editar", pk=inmueble_pk)
