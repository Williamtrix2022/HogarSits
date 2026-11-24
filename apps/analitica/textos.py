"""Frases en lenguaje de negocio para cada cifra del análisis (RF-59).

La encuesta mostró que la analítica fue lo menos valorado: una cifra con «λ» o «P» sueltas no
le sirve a un gerente. Cada resultado se acompaña de una frase que cualquiera entiende; la parte
técnica va aparte, plegada. Funciones puras: sin Django, probables sin base de datos.
"""

from apps.analitica.services.colas import Cola
from apps.analitica.services.markov import NOMBRES, Absorcion
from apps.analitica.services.poisson import AjustePoisson, Franja


def num(valor: float, decimales: int = 1) -> str:
    """Número con coma decimal (es-CO): 2.3989 → «2,4»."""
    texto = f"{valor:.{decimales}f}"
    return texto.replace(".", ",")


def duracion(horas: float) -> str:
    """Una duración dada en horas, dicha como la diría una persona."""
    minutos = horas * 60
    if minutos < 1:
        return "menos de 1 minuto"
    if minutos < 60:
        n = round(minutos)
        return f"unos {n} minuto" + ("" if n == 1 else "s")
    h, m = divmod(round(minutos), 60)
    return f"{h} h" + (f" {m} min" if m else "")


def _rango_hora(hora: int) -> str:
    return f"{hora:02d}:00 y {hora + 1:02d}:00"


def _de_cada_10(proporcion: float) -> str:
    """«alrededor de 3 de cada 10 clientes»; sin números raros en los extremos."""
    n = round(proporcion * 10)
    if n <= 0:
        return "casi ningún cliente"
    if n >= 10:
        return "casi todos los clientes"
    return f"alrededor de {n} de cada 10 clientes"


def _asesores(n: int) -> str:
    return f"{n} asesor" + ("" if n == 1 else "es")


def frase_demanda(pico: Franja | None, valle: Franja | None) -> str:
    if pico is None:
        return "Todavía no hay llegadas registradas en este periodo."
    texto = (
        f"Los clientes llegan sobre todo entre las {_rango_hora(pico.hora)}: "
        f"unos {num(pico.lam)} por hora."
    )
    if valle is not None and valle.hora != pico.hora:
        texto += (
            f" La hora más tranquila es entre las {_rango_hora(valle.hora)} ({num(valle.lam)})."
        )
    return texto


def frase_ajuste(ajuste: AjustePoisson | None) -> str:
    if ajuste is None:
        return ""
    if not ajuste.probado:
        return "Hay muy pocos días observados para decir si las llegadas siguen un patrón al azar."
    if ajuste.rechaza:
        return (
            "En esta hora las llegadas no se comportan como llegadas al azar: tienden a "
            "venir en grupos. Las cifras de espera pueden quedarse cortas."
        )
    return "En esta hora las llegadas se comportan como llegadas al azar, como supone el modelo."


def frase_colas(cola: Cola | None, c: int | None) -> str:
    if cola is None or c is None:
        return "No hay datos suficientes para calcular las esperas."
    if not cola.estable:
        return (
            f"Con {_asesores(c)} disponibles la carga es demasiado alta: la fila crecería sin "
            "límite. Hace falta más personal."
        )
    texto = (
        f"Con {_asesores(c)} disponible{'' if c == 1 else 's'}, un cliente espera en promedio "
        f"{duracion(cola.Wq)} antes de ser atendido; {_de_cada_10(cola.p_espera)} "
        "tienen que esperar."
    )
    if cola.al_limite:
        texto += (
            " Cuidado: el sistema está casi al límite y una pequeña alza de clientes "
            "dispararía la espera."
        )
    return texto


def frase_recomendacion(c_min: int | None, umbral_min: float, c_actual: int | None) -> str:
    if c_min is None:
        return (
            f"Ni con muchos asesores se logra que la espera baje de {num(umbral_min, 0)} minutos."
        )
    texto = (
        f"Para que la espera en la hora pico no pase de {num(umbral_min, 0)} minutos se necesitan "
        f"al menos {_asesores(c_min)} disponibles."
    )
    if c_actual is not None and c_min > c_actual:
        texto += f" Hoy hay {_asesores(c_actual)}."
    return texto


def frase_cierre(absorcion: Absorcion | None) -> str:
    if absorcion is None:
        return "Todavía no hay datos suficientes para estimar cuántos clientes cierran."
    cierran = round(absorcion.p_cierre[0] * 10)
    return (
        f"De cada 10 clientes que consultan, unos {cierran} terminan cerrando y {10 - cierran} "
        f"abandonan. En promedio un cliente necesita unos {num(absorcion.pasos[0])} seguimientos "
        "para llegar a un resultado."
    )


def frases_por_etapa(absorcion: Absorcion | None) -> list[str]:
    if absorcion is None:
        return []
    return [
        f"{NOMBRES[etapa]} → cierre: {num(absorcion.p_cierre[i] * 100, 0)} %"
        for i, etapa in enumerate((1, 2, 3))
    ]
