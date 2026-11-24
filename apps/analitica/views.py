from urllib.parse import urlencode

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.generic import TemplateView

from apps.analitica.services.markov import NOMBRES
from apps.cuentas.views import AdminRequeridoMixin

from . import analisis, exportar, graficas, textos
from .analisis import UMBRAL_ESPERA_MIN
from .forms import FiltroAnalisisForm


def parametros_del_filtro(request):
    """El filtro de la URL, o el rango por defecto. Devuelve (form, desde, hasta, umbral)."""
    desde, hasta = analisis.rango_por_defecto()
    inicial = {"desde": desde, "hasta": hasta, "espera_max": UMBRAL_ESPERA_MIN}
    form = FiltroAnalisisForm(request.GET) if request.GET else FiltroAnalisisForm(initial=inicial)
    if request.GET and form.is_valid():
        d = form.cleaned_data
        return form, d["desde"], d["hasta"], d["espera_max"]
    # Sin filtro, o con uno inválido, se muestra el rango por defecto (y los errores del filtro).
    return form, desde, hasta, UMBRAL_ESPERA_MIN


class PanelView(AdminRequeridoMixin, TemplateView):
    """Análisis (solo administrador): demanda, asesores y esperas, y probabilidad de cierre."""

    template_name = "analitica/panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form, desde, hasta, umbral = parametros_del_filtro(self.request)
        r = analisis.analizar_periodo(desde, hasta, umbral)
        absorcion = r.markov.absorcion
        ctx.update(
            form=form,
            r=r,
            frase_demanda=textos.frase_demanda(r.franja_pico, r.franja_valle),
            frase_ajuste=textos.frase_ajuste(r.ajuste_pico),
            frase_colas=textos.frase_colas(r.cola, r.c_usado),
            frase_colas_pico=textos.frase_colas(r.cola_pico, r.c_pico),
            frase_recomendacion=textos.frase_recomendacion(
                r.c_recomendado, r.umbral_min, r.c_pico or r.c_usado
            ),
            frase_cierre=textos.frase_cierre(absorcion),
            frases_etapas=textos.frases_por_etapa(absorcion),
            graficas=graficas.construir(r),
            matriz=_filas_matriz(r),
            ajuste_filas=_filas_ajuste(r),
            absorcion_filas=_filas_absorcion(r),
            tabla_c=_filas_colas(r),
            espera_min=r.cola.Wq * 60 if r.cola and r.cola.estable else None,
            ocupacion=r.cola.rho * 100 if r.cola else None,
            qs_exportar=urlencode(
                {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "espera_max": umbral}
            ),
        )
        return ctx


def _filas_matriz(r):
    """Filas de la matriz P para la tabla técnica: (etapa, valores o None, n observaciones)."""
    est = r.markov.estimacion
    return [
        (NOMBRES[i + 1], est.matriz[i], est.n_por_origen[i], est.conteos[i]) for i in range(5)
    ]


def _filas_ajuste(r):
    """(k, % observado, % esperado por Poisson) de la hora pico."""
    a = r.ajuste_pico
    if a is None:
        return []
    return [(k, o * 100, e * 100) for k, o, e in zip(a.ks, a.observada, a.esperada, strict=True)]


def _filas_absorcion(r):
    a = r.markov.absorcion
    if a is None:
        return []
    return [
        (NOMBRES[etapa], a.p_cierre[i] * 100, a.p_abandono[i] * 100, a.pasos[i])
        for i, etapa in enumerate((1, 2, 3))
    ]


def _filas_colas(r):
    """La tabla M/M/c de la hora pico, con los tiempos ya en minutos."""
    return [
        {
            "c": q.c,
            "rho": q.rho,
            "estable": q.estable,
            "p_espera": q.p_espera,
            "lq": q.Lq,
            "wq_min": q.Wq * 60 if q.estable else None,
            "w_min": q.W * 60 if q.estable else None,
        }
        for q in r.tabla_c
    ]


class ExportarView(AdminRequeridoMixin, View):
    """Descarga una tabla del análisis como CSV (RF-58). Mismo filtro que el panel."""

    http_method_names = ["get"]

    def get(self, request):
        nombre = request.GET.get("tabla", "")
        if nombre not in exportar.TABLAS:
            raise Http404("Tabla desconocida.")
        form, desde, hasta, umbral = parametros_del_filtro(request)
        if request.GET.get("desde") or request.GET.get("hasta") or request.GET.get("espera_max"):
            if not form.is_valid():  # un filtro inválido no debe exportar datos de otro periodo
                errores = "; ".join(e for lista in form.errors.values() for e in lista)
                return HttpResponseBadRequest(f"Filtro no válido: {errores}")
        resumen = analisis.analizar_periodo(desde, hasta, umbral)
        encabezados, filas = exportar.tabla(resumen, nombre)
        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = (
            f'attachment; filename="{exportar.nombre_de_archivo(nombre, desde, hasta)}"'
        )
        exportar.escribir(respuesta, encabezados, filas)
        return respuesta
