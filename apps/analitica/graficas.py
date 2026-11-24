"""Datos listos para dibujar con Chart.js. Solo da forma al `Resumen`; no calcula."""

from apps.analitica.analisis import Resumen
from apps.analitica.services.markov import NOMBRES


def _pct(x: float) -> float:
    return round(x * 100, 1)


def construir(r: Resumen) -> dict:
    demanda = None
    if r.franjas:
        demanda = {
            "horas": [f"{f.hora:02d}:00" for f in r.franjas],
            "lam": [round(f.lam, 3) for f in r.franjas],
            "suficiente": [f.suficiente for f in r.franjas],
        }

    ajuste = None
    if r.ajuste_pico is not None and r.franja_pico is not None:
        a = r.ajuste_pico
        ajuste = {
            "hora": f"{r.franja_pico.hora:02d}:00",
            "ks": list(a.ks),
            "etiquetas": list(a.etiquetas),
            "observada": [_pct(x) for x in a.observada],
            "esperada": [_pct(x) for x in a.esperada],
        }

    colas = None
    if r.tabla_c:
        colas = {
            "c": [q.c for q in r.tabla_c],
            "wq_min": [round(q.Wq * 60, 1) if q.estable else None for q in r.tabla_c],
            "umbral": r.umbral_min,
        }

    cierre = None
    absorcion = r.markov.absorcion
    if absorcion is not None:
        cierre = {
            "etapas": [NOMBRES[e] for e in (1, 2, 3)],
            "cierre": [_pct(x) for x in absorcion.p_cierre],
            "abandono": [_pct(x) for x in absorcion.p_abandono],
        }
    return {"demanda": demanda, "ajuste": ajuste, "colas": colas, "cierre": cierre}
