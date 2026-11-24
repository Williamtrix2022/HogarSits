"""Compara los parámetros estimados con los usados para simular (RF-61, HU-10).

    python manage.py validar_modelos                      # base: 20 réplicas de 120 días
    python manage.py validar_modelos --escenario todos     # los seis de SUPUESTOS_DE_TRABAJO
    python manage.py validar_modelos --por-tamano          # error según los días de datos
    python manage.py validar_modelos --informe salida.md   # guarda además el informe en Markdown

No lee ni escribe la base de datos: simula en memoria con semillas conocidas, así que es
reproducible y nunca toca datos reales. La salida de consola va en ASCII (la consola de Windows
no imprime λ ni μ); el informe en archivo va en UTF-8.
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.analitica.services import validacion as v

FECHA_BASE = date(2026, 1, 5)  # fija: el resultado no depende del día en que se ejecute
DIAS_POR_TAMANO = (30, 90, 300)


def _pct(x, signo: bool = False) -> str:
    """Porcentaje con coma decimal; con `signo`, siempre +/− (para sesgos)."""
    if x is None:
        return "n/d"
    return f"{x * 100:{'+' if signo else ''}.1f} %".replace(".", ",")


def _num(x, dec=2) -> str:
    return "n/d" if x is None else f"{x:.{dec}f}".replace(".", ",")


def tabla_parametros(res: v.ResumenReplicas) -> list[str]:
    filas = [
        "| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | "
        "Error rel. medio (abs.) | Error rel. p95 (abs.) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for m in res.medidas:
        filas.append(
            f"| {m.nombre} ({m.unidad}) | {_num(m.verdadero, 3)} | {_num(m.media_estimada, 3)} | "
            f"{_num(m.sesgo, 3)} | {_num(m.desviacion, 3)} | {_pct(m.error_rel_abs_medio)} | "
            f"{_pct(m.error_rel_abs_p95)} |"
        )
    return filas


def tabla_espera(res: v.ResumenReplicas) -> list[str]:
    return [
        "| Espera media (min) | Valor |",
        "|---|---:|",
        f"| **Simulada** | **{_num(res.espera_simulada_min)}** |",
        f"| M/M/c con c nominal ({res.parametros.n_asesores}) | "
        f"{_num(res.espera_modelo_nominal_min)} |",
        f"| M/M/c con c efectivo (promedio {_num(res.c_efectivo)}, redondeado) | "
        f"{_num(res.espera_modelo_efectivo_min)} |",
        f"| M/M/c hora por hora (c efectivo de cada hora) | "
        f"{_num(res.espera_modelo_por_franja_min)} |",
    ]


class Command(BaseCommand):
    help = "Valida λ, μ y P estimados frente a los usados para simular."

    def add_arguments(self, parser):
        parser.add_argument("--escenario", default="base",
                            help="nombre de un escenario o «todos» (ver SUPUESTOS_DE_TRABAJO.md)")
        parser.add_argument("--dias", type=int, default=120)
        parser.add_argument("--replicas", type=int, default=20)
        parser.add_argument("--semilla", type=int, default=100)
        parser.add_argument("--por-tamano", action="store_true",
                            help="repite el escenario con 30, 90 y 300 días de datos")
        parser.add_argument("--informe", help="ruta de un archivo .md donde guardar el informe")

    def handle(self, *args, **o):
        nombres = list(v.ESCENARIOS) if o["escenario"] == "todos" else [o["escenario"]]
        lineas = [
            f"Réplicas por escenario: {o['replicas']} · días simulados: {o['dias']} · "
            f"semilla base: {o['semilla']}", "",
        ]
        try:
            for nombre in nombres:
                p = v.parametros_de(nombre, FECHA_BASE, o["dias"], o["semilla"])
                res = v.validar_replicas(p, o["replicas"])
                lineas += self._seccion(nombre, res)
                self.stdout.write(f"[ok] escenario '{nombre}'")
            if o["por_tamano"]:
                lineas += self._por_tamano(o)
        except ValueError as error:
            raise CommandError(str(error)) from error
        informe = "\n".join(lineas) + "\n"
        if o["informe"]:
            with open(o["informe"], "w", encoding="utf-8", newline="\n") as f:
                f.write(informe)
            self.stdout.write(f"Informe guardado en {o['informe']}")
        else:
            self.stdout.write(informe.encode("ascii", "replace").decode("ascii"))

    def _seccion(self, nombre: str, res: v.ResumenReplicas) -> list[str]:
        p = res.parametros
        sufic = _num(res.franjas_suficientes * 100, 0)
        return [
            f"### Escenario «{nombre}»", "",
            f"λ = {p.clientes_por_dia:g} clientes/día · {p.n_asesores} asesores · servicio medio "
            f"{p.servicio_medio_min:g} min · {p.hora_apertura}:00 a {p.hora_cierre}:00 · "
            f"visitas {p.visita_min}–{p.visita_max} min.", "",
            *tabla_parametros(res), "",
            f"- Error máximo de una entrada de P (media de réplicas): "
            f"{_num(res.error_max_p_medio, 3)}.",
            f"- Error máximo de λ por hora (media de réplicas): "
            f"{_num(res.error_max_lambda_hora_medio, 2)} clientes/hora.",
            f"- Franjas con datos suficientes (RN-40): {sufic} %.",
            f"- Tasa de rechazo del χ² de Poisson: {_pct(res.tasa_rechazo_poisson)} "
            f"(esperado ≈ 5 %, porque los datos SÍ son de Poisson).",
            f"- Réplicas sin datos suficientes para P(cierre): "
            f"{res.sin_absorcion} de {res.replicas}.",
            "", *tabla_espera(res), "",
        ]

    def _por_tamano(self, o) -> list[str]:
        filas = [
            "### Error según los días de datos (escenario base)", "",
            "| Días | λ día: error rel. medio | μ: error rel. medio | "
            "P(cierre): error rel. medio | P(cierre): error rel. p95 | "
            "Franjas suficientes | Sin P(cierre) |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for dias in DIAS_POR_TAMANO:
            reps = o["replicas"] if dias < 300 else max(6, o["replicas"] // 3)
            res = v.validar_replicas(v.parametros_de("base", FECHA_BASE, dias, o["semilla"]), reps)
            por = {m.nombre: m for m in res.medidas}
            cierre = por.get("P(cierre desde Consulta)")
            filas.append(
                f"| {dias} | {_pct(por['λ por día laboral'].error_rel_abs_medio)} | "
                f"{_pct(por['μ'].error_rel_abs_medio)} | "
                f"{_pct(cierre.error_rel_abs_medio) if cierre else 'n/d'} | "
                f"{_pct(cierre.error_rel_abs_p95) if cierre else 'n/d'} | "
                f"{_num(res.franjas_suficientes * 100, 0)} % | {res.sin_absorcion} de {reps} |"
            )
            self.stdout.write(f"[ok] {dias} dias")
        return filas + [""]
