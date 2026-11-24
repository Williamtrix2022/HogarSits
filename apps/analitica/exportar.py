"""Exportación de los resultados del análisis a CSV (RF-58).

Cada tabla se arma aquí como (encabezados, filas) a partir del `Resumen`; la vista solo la
escribe como CSV. Formato pensado para abrirse con **Excel en español (es-CO)**: separador `;`,
coma decimal y UTF-8 con marca BOM (para que las tildes no se rompan).

Seguridad: una celda de texto que empiece por `=`, `+`, `-`, `@`, tabulación o retorno se
interpretaría como una **fórmula** al abrirla en Excel (inyección de CSV). Esas celdas se
neutralizan con un apóstrofo inicial. Los números no se tocan.
"""

import csv
from datetime import date

from apps.analitica.analisis import Resumen
from apps.analitica.services.markov import NOMBRES

SEPARADOR = ";"
PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")

TABLAS = {
    "lambda": "Llegadas por hora (λ)",
    "poisson": "Ajuste de Poisson en la hora pico",
    "colas": "Esperas según el número de asesores (M/M/c)",
    "matriz": "Matriz de transición P",
    "absorcion": "Probabilidad de cierre y pasos esperados",
}


def celda(valor):
    """Valor listo para escribir: números con coma decimal; texto a salvo de fórmulas."""
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float):
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")  # sin notación científica (Excel no la lee)
        return ("0" if texto in ("", "-0") else texto).replace(".", ",")
    texto = str(valor)
    return "'" + texto if texto.startswith(PELIGROSOS) else texto


def _simulado(r: Resumen) -> str:
    return "sí" if r.hay_simulados else "no"


def tabla(r: Resumen, nombre: str) -> tuple[list[str], list[list]]:
    """(encabezados, filas) de una tabla. Cada fila lleva `datos_simulados` al final, para que
    la advertencia viaje con el archivo y no se pierda al abrirlo en otro lado."""
    if nombre not in TABLAS:
        raise KeyError(nombre)
    sim = _simulado(r)

    if nombre == "lambda":
        enc = ["hora", "dias_observados", "llegadas", "lambda_clientes_por_hora",
               "datos_suficientes", "datos_simulados"]
        filas = [[f"{f.hora:02d}:00", f.dias_observados, f.llegadas, f.lam, f.suficiente, sim]
                 for f in r.franjas]

    elif nombre == "poisson":
        enc = ["hora_pico", "llegadas_en_la_hora_k", "frecuencia_observada_pct",
               "poisson_pct", "datos_simulados"]
        a, pico = r.ajuste_pico, r.franja_pico
        filas = [] if a is None else [
            [f"{pico.hora:02d}:00", k, o * 100, e * 100, sim]
            for k, o, e in zip(a.ks, a.observada, a.esperada, strict=True)
        ]

    elif nombre == "colas":
        enc = ["asesores", "rho", "estable", "prob_esperar", "Lq_clientes",
               "Wq_min", "W_min", "datos_simulados"]
        filas = [
            [q.c, q.rho, q.estable, q.p_espera,
             q.Lq if q.estable else None,
             q.Wq * 60 if q.estable else None,
             q.W * 60 if q.estable else None, sim]
            for q in r.tabla_c
        ]

    elif nombre == "matriz":
        enc = ["desde_etapa", "hacia_consulta", "hacia_visita", "hacia_negociacion",
               "hacia_cierre", "hacia_abandono", "observaciones", "datos_simulados"]
        est = r.markov.estimacion
        filas = []
        for i in range(5):
            fila = est.matriz[i]  # None = sin observaciones: no se inventa (RN-43)
            valores = list(fila) if fila else [None] * 5
            filas.append([NOMBRES[i + 1], *valores, est.n_por_origen[i], sim])

    else:  # absorcion
        enc = ["desde_etapa", "prob_cierre_pct", "prob_abandono_pct", "pasos_esperados",
               "datos_simulados"]
        a = r.markov.absorcion
        filas = [] if a is None else [
            [NOMBRES[e], a.p_cierre[i] * 100, a.p_abandono[i] * 100, a.pasos[i], sim]
            for i, e in enumerate((1, 2, 3))
        ]
    return enc, filas


def tabla_asesores(indicadores, simulado: bool) -> tuple[list[str], list[list]]:
    """Indicadores por asesor (RF-62). Una atención media sin finalizadas sale vacía."""
    enc = ["asesor", "solicitudes_atendidas", "visitas_realizadas", "cierres",
           "atencion_media_min", "atenciones_finalizadas", "datos_simulados"]
    sim = "sí" if simulado else "no"
    filas = [
        [i.nombre, i.atendidas, i.visitas_realizadas, i.cierres, i.atencion_media_min,
         i.n_finalizadas, sim]
        for i in indicadores
    ]
    return enc, filas


def escribir(respuesta, encabezados: list[str], filas: list[list]) -> None:
    """Escribe el CSV (con BOM) en un objeto con `write`, p. ej. un HttpResponse."""
    respuesta.write("﻿")
    w = csv.writer(respuesta, delimiter=SEPARADOR, lineterminator="\r\n")
    w.writerow([celda(h) for h in encabezados])
    for fila in filas:
        w.writerow([celda(v) for v in fila])


def nombre_de_archivo(nombre: str, desde: date, hasta: date) -> str:
    return f"hogarsits_{nombre}_{desde.isoformat()}_{hasta.isoformat()}.csv"
