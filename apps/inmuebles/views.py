from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import FiltroInmuebleForm, InmuebleForm
from .models import Inmueble
from .services import cambiar_activo, guardar_inmueble


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
        return ctx

    def form_valid(self, form):
        self.object = guardar_inmueble(form, self.request.user)
        messages.success(self.request, f"Inmueble «{self.object.titulo}» actualizado.")
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
