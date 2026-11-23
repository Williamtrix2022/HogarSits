from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import FormView, TemplateView

from . import services
from .forms import ReprogramarForm, VisitaForm
from .models import Visita

User = get_user_model()
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _lunes(dia: date) -> date:
    return dia - timedelta(days=dia.weekday())


class AgendaSemanaView(TemplateView):
    """Agenda por semana, agrupada por día; se puede filtrar por asesor (RF-34)."""

    template_name = "agenda/semana.html"

    def _semana(self):
        try:
            base = date.fromisoformat(self.request.GET.get("fecha", ""))
        except ValueError:
            base = timezone.localdate()
        return _lunes(base)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lunes = self._semana()
        zona = timezone.get_current_timezone()
        desde = datetime.combine(lunes, time.min, tzinfo=zona)
        hasta = desde + timedelta(days=7)
        visitas = Visita.objects.filter(inicio__gte=desde, inicio__lt=hasta).select_related(
            "inmueble", "asesor", "solicitud__cliente"
        ).order_by("inicio")
        asesor = self.request.GET.get("asesor", "")
        if asesor.isdigit():
            visitas = visitas.filter(asesor_id=int(asesor))
        por_dia = {lunes + timedelta(days=i): [] for i in range(7)}
        for v in visitas:
            por_dia[timezone.localtime(v.inicio).date()].append(v)
        hoy = timezone.localdate()
        ctx.update(
            dias=[
                {"fecha": d, "nombre": DIAS[d.weekday()], "es_hoy": d == hoy, "visitas": vs}
                for d, vs in por_dia.items()
            ],
            lunes=lunes,
            domingo=lunes + timedelta(days=6),
            anterior=(lunes - timedelta(days=7)).isoformat(),
            siguiente=(lunes + timedelta(days=7)).isoformat(),
            asesores=User.objects.filter(is_active=True).order_by("first_name", "username"),
            asesor_elegido=asesor,
            total=len(visitas),
            ahora=timezone.now(),
        )
        return ctx


class VisitaCrearView(FormView):
    form_class = VisitaForm
    template_name = "agenda/formulario.html"
    success_url = reverse_lazy("agenda:semana")
    extra_context = {"titulo": "Agendar visita"}

    def get_initial(self):
        inicial = {"asesor": self.request.user.pk, "duracion": 60}
        if self.request.GET.get("solicitud", "").isdigit():
            inicial["solicitud"] = int(self.request.GET["solicitud"])
        return inicial

    def form_valid(self, form):
        d = form.cleaned_data
        try:
            visita = services.programar(
                d["solicitud"], d["inmueble"], d["asesor"], d["inicio"], d["duracion"], d["notas"]
            )
        except services.AgendaError as error:  # carrera: se ocupó entre validar y guardar
            form.add_error(None, str(error))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Visita agendada para {d['solicitud'].cliente.nombre} en «{visita.inmueble.titulo}».",
        )
        return super().form_valid(form)


class VisitaReprogramarView(FormView):
    form_class = ReprogramarForm
    template_name = "agenda/formulario.html"
    success_url = reverse_lazy("agenda:semana")

    def dispatch(self, request, *args, **kwargs):
        self.visita = get_object_or_404(
            Visita.objects.select_related("inmueble", "asesor", "solicitud__cliente"),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["visita"] = self.visita
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Reprogramar visita a «{self.visita.inmueble.titulo}»"
        return ctx

    def form_valid(self, form):
        try:
            services.reprogramar(self.visita, form.cleaned_data["inicio"],
                                 form.cleaned_data["duracion"])
        except services.AgendaError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        messages.success(self.request, "Visita reprogramada; la anterior quedó cancelada.")
        return super().form_valid(form)


class AccionVisitaView(View):
    """Cancelar o marcar como realizada (solo POST)."""

    http_method_names = ["post"]
    mensaje_ok = ""
    accion = None

    def post(self, request, pk):
        visita = get_object_or_404(Visita, pk=pk)
        try:
            self.accion(visita)
        except services.AgendaError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, self.mensaje_ok)
        destino = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
            destino = reverse("agenda:semana")
        return redirect(destino)


class CancelarVisitaView(AccionVisitaView):
    mensaje_ok = "Visita cancelada; el horario quedó libre."
    accion = staticmethod(services.cancelar)


class RealizarVisitaView(AccionVisitaView):
    mensaje_ok = "Visita marcada como realizada."
    accion = staticmethod(services.realizar)
