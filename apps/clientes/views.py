from django.contrib import messages
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ClienteForm, FiltroClienteForm
from .models import Cliente


def _avisar_telefono_repetido(request, form):
    otros = form.clientes_con_mismo_telefono()
    if otros:
        nombres = ", ".join(c.nombre for c in otros[:3])
        messages.warning(
            request,
            f"Guardado, pero el teléfono {form.instance.telefono} ya lo usa: {nombres}. "
            "Verifique que no sea la misma persona.",
        )


class ClienteListView(ListView):
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        self.filtro = FiltroClienteForm(self.request.GET or None)
        self.filtro.is_valid()
        base = Cliente.objects.annotate(n_solicitudes=Count("solicitudes")).order_by("nombre", "id")
        return self.filtro.aplicar(base)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filtro"] = self.filtro
        ctx["hay_filtros"] = self.filtro.hay_filtros
        ctx["querystring"] = params.urlencode()
        return ctx


class ClienteCrearView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/formulario.html"
    success_url = reverse_lazy("clientes:lista")
    extra_context = {"titulo": "Nuevo cliente"}

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f"Cliente «{self.object.nombre}» registrado.")
        _avisar_telefono_repetido(self.request, form)
        return respuesta


class ClienteEditarView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/formulario.html"

    def get_success_url(self):
        return reverse("clientes:lista")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Cliente: {self.object.nombre}"
        ctx["solicitudes"] = self.object.solicitudes.select_related("inmueble").order_by(
            "-timestamp_llegada"
        )[:10]
        return ctx

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f"Cliente «{self.object.nombre}» actualizado.")
        _avisar_telefono_repetido(self.request, form)
        return respuesta
