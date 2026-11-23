"""Horarios semanales de los asesores y asesores disponibles (RF-36, #53). Solo administrador."""

from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.cuentas.views import AdminRequeridoMixin

from . import disponibilidad
from .forms_horario import TurnoForm, horas_semana
from .models import HorarioAsesor


class HorariosListaView(AdminRequeridoMixin, TemplateView):
    template_name = "agenda/horarios_lista.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filas = []
        for asesor in disponibilidad.asesores_programables():
            turnos = list(asesor.horarios.all())
            filas.append({"asesor": asesor, "turnos": len(turnos), "horas": horas_semana(turnos)})
        ctx["filas"] = filas
        return ctx


class HorarioAsesorView(AdminRequeridoMixin, TemplateView):
    """Los turnos de un asesor, por día, y el formulario para agregar más."""

    template_name = "agenda/horario_asesor.html"

    def dispatch(self, request, *args, **kwargs):
        self.asesor = get_object_or_404(disponibilidad.asesores_programables(), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        turnos = list(self.asesor.horarios.all())
        ctx.update(
            asesor=self.asesor,
            form=kwargs.get("form") or TurnoForm(asesor=self.asesor),
            dias=[
                {"nombre": etiqueta, "turnos": [t for t in turnos if t.dia_semana == valor]}
                for valor, etiqueta in HorarioAsesor.Dia.choices
            ],
            horas=horas_semana(turnos),
        )
        return ctx

    def post(self, request, pk):
        form = TurnoForm(request.POST, asesor=self.asesor)
        if form.is_valid():
            cantidad = form.guardar()
            nombre = self.asesor.get_full_name() or self.asesor.username
            messages.success(request, f"Turno agregado a {cantidad} día(s) de {nombre}.")
            return redirect("horarios:asesor", pk=pk)
        return self.render_to_response(self.get_context_data(form=form))


class TurnoBorrarView(AdminRequeridoMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        turno = get_object_or_404(HorarioAsesor.objects.select_related("asesor"), pk=pk)
        asesor_pk = turno.asesor_id
        turno.delete()
        messages.success(request, "Turno eliminado.")
        return redirect("horarios:asesor", pk=asesor_pk)


class DisponibilidadView(AdminRequeridoMixin, TemplateView):
    """Asesores disponibles por franja de una hora en una fecha (el c efectivo)."""

    template_name = "agenda/disponibilidad.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            dia = date.fromisoformat(self.request.GET.get("fecha", ""))
        except ValueError:
            dia = timezone.localdate()
        franjas = disponibilidad.disponibilidad_del_dia(dia)
        ctx.update(
            fecha=dia,
            franjas=franjas,
            promedio=round(sum(f.c for f in franjas) / len(franjas), 1) if franjas else None,
            url_horarios=reverse("horarios:lista"),
        )
        return ctx
