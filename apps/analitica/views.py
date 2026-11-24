from urllib.parse import urlencode

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.generic import TemplateView

from apps.analitica.services.markov import NOMBRES
from apps.cuentas.roles import es_admin
from apps.cuentas.views import AdminRequeridoMixin

from . import analisis, datos, exportar, graficas, indicadores, textos
from .analisis import UMBRAL_ESPERA_MIN
from .forms import FiltroAnalisisForm, FiltroPeriodoForm


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
    return [
        (etiqueta, o * 100, e * 100)
        for etiqueta, o, e in zip(a.etiquetas, a.observada, a.esperada, strict=True)
    ]


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
        if nombre not in exportar.TABLAS and nombre != "asesores":
            raise Http404("Tabla desconocida.")
        if nombre == "asesores":  # solo necesita el periodo, no el umbral de espera
            form, desde, hasta = _periodo_del_filtro(request)
            umbral = UMBRAL_ESPERA_MIN
        else:
            form, desde, hasta, umbral = parametros_del_filtro(request)
        if request.GET.get("desde") or request.GET.get("hasta") or request.GET.get("espera_max"):
            if not form.is_valid():  # un filtro inválido no debe exportar datos de otro periodo
                errores = "; ".join(e for lista in form.errors.values() for e in lista)
                return HttpResponseBadRequest(f"Filtro no válido: {errores}")
        if nombre == "asesores":
            encabezados, filas = exportar.tabla_asesores(
                indicadores.indicadores_por_asesor(desde, hasta), datos.hay_simulados(desde, hasta)
            )
        else:
            resumen = analisis.analizar_periodo(desde, hasta, umbral)
            encabezados, filas = exportar.tabla(resumen, nombre)
        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = (
            f'attachment; filename="{exportar.nombre_de_archivo(nombre, desde, hasta)}"'
        )
        exportar.escribir(respuesta, encabezados, filas)
        return respuesta


def _periodo_del_filtro(request):
    """El filtro de fechas de la URL, o el rango por defecto. Devuelve (form, desde, hasta)."""
    desde, hasta = analisis.rango_por_defecto()
    if request.GET:
        form = FiltroPeriodoForm(request.GET)
        if form.is_valid():
            return form, form.cleaned_data["desde"], form.cleaned_data["hasta"]
        return form, desde, hasta
    return FiltroPeriodoForm(initial={"desde": desde, "hasta": hasta}), desde, hasta


class AsesoresView(TemplateView):
    """Indicadores por asesor (HU-13, W13).

    El administrador ve a todo el equipo. Un asesor **solo ve su propia fila** (CA2): no hay
    parámetro de la URL que le permita ver la de otro.
    """

    template_name = "analitica/asesores.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario = self.request.user
        admin = es_admin(usuario)
        form, desde, hasta = _periodo_del_filtro(self.request)
        lista = indicadores.indicadores_por_asesor(desde, hasta, asesor=None if admin else usuario)
        ctx.update(
            form=form,
            desde=desde,
            hasta=hasta,
            filas=lista,
            total=indicadores.totales(lista) if admin else None,
            solo_propios=not admin,
            hay_simulados=datos.hay_simulados(desde, hasta),
            qs_exportar=urlencode({"desde": desde.isoformat(), "hasta": hasta.isoformat()}),
        )
        return ctx
