"""Frases en lenguaje de negocio para cada cifra del análisis (RF-59).

La encuesta mostró que la analítica fue lo menos valorado: una cifra con «λ» o «P» sueltas no
le sirve a un gerente. Cada resultado se acompaña de una frase que cualquiera entiende; la parte
técnica va aparte, plegada. Funciones puras: sin Django, probables sin base de datos.

Redondeo: se hace **al final** y con mitades hacia arriba (2,5 → 3). `round()` de Python lleva
las mitades al par (2,5 → 2), y una frase que dice «unos 2» cuando el número es 2,5 sorprende.
"""

from apps.analitica.services.colas import Cola
from apps.analitica.services.markov import NOMBRES, Absorcion
from apps.analitica.services.poisson import AjustePoisson, Franja


def _entero(x: float) -> int:
    """Entero más cercano, con las mitades hacia arriba."""
    return int(x + 0.5)


def num(valor: float, decimales: int = 1) -> str:
    """Número con coma decimal (es-CO): 2.3989 → «2,4»."""
    texto = f"{valor:.{decimales}f}"
    return texto.replace(".", ",")


def duracion(horas: float) -> str:
    """Una duración dada en horas, dicha como la diría una persona."""
    minutos = horas * 60
    if minutos < 1:
        return "menos de 1 minuto"
    n = _entero(minutos)
    if n >= 60:
        h, m = divmod(n, 60)
        return f"{h} h" + (f" {m} min" if m else "")
    if n == 1:
        return "alrededor de 1 minuto"
    return f"unos {n} minutos"


def _rango_hora(hora: int) -> str:
    return f"{hora:02d}:00 y {hora + 1:02d}:00"


def _de_cada_10(proporcion: float) -> str:
    """«alrededor de 3 de cada 10 clientes»; sin números raros en los extremos."""
    n = _entero(proporcion * 10)
    if n <= 0:
        return "casi ningún cliente"
    if n >= 10:
        return "casi todos los clientes"
    return f"alrededor de {n} de cada 10 clientes"


def _asesores(n: int) -> str:
    return f"{n} asesor" + ("" if n == 1 else "es")


def _libres(n: int) -> str:
    return f"{n} asesor libre" if n == 1 else f"{n} asesores libres"


def frase_demanda(pico: Franja | None, valle: Franja | None) -> str:
    if pico is None:
        return "Todavía no hay llegadas registradas en este periodo."
    ritmo = "menos de 0,1" if pico.lam < 0.05 else num(pico.lam)
    texto = (
        f"Los clientes llegan sobre todo entre las {_rango_hora(pico.hora)}: "
        f"unos {ritmo} por hora."
    )
    if valle is not None and valle.hora != pico.hora:
        texto += (
            f" La hora más tranquila es entre las {_rango_hora(valle.hora)} ({num(valle.lam)})."
        )
    if not pico.suficiente:  # RN-40: el aviso va junto a la cifra, no solo en la lista general
        texto += " Ojo: son pocos datos en esa hora, así que no es una cifra firme."
    return texto


def frase_ajuste(ajuste: AjustePoisson | None) -> str:
    """Qué dice la prueba χ², sin decir más de lo que prueba."""
    if ajuste is None:
        return ""
    if not ajuste.probado:
        return "Faltan datos para probar si las llegadas en esta hora siguen un patrón al azar."
    if ajuste.rechaza and ajuste.indice_dispersion > 1:
        return (
            "En esta hora las llegadas no se comportan como llegadas al azar: tienden a venir "
            "en grupos. Las cifras de espera pueden quedarse cortas."
        )
    if ajuste.rechaza:
        return (
            "En esta hora las llegadas son más regulares de lo que supone el modelo (llegan más "
            "parejas que al azar). Las esperas reales pueden ser algo menores."
        )
    return (
        "No hay evidencia en contra de que las llegadas en esta hora sean al azar, como supone "
        "el modelo (con pocos días observados la prueba detecta poco)."
    )


def frase_colas(cola: Cola | None, c: int | None) -> str:
    if cola is None or c is None:
        return "No hay datos suficientes para calcular las esperas."
    disponibles = f"{_asesores(c)} disponible" + ("" if c == 1 else "s")
    if not cola.estable:
        return (
            f"Con {disponibles} la carga es demasiado alta: la fila crecería sin límite. "
            "Hace falta más personal."
        )
    texto = (
        f"Con {disponibles}, un cliente espera en promedio {duracion(cola.Wq)} antes de ser "
        f"atendido; {_de_cada_10(cola.p_espera)} tienen que esperar."
    )
    if cola.al_limite:
        texto += (
            " Cuidado: el sistema está casi al límite y una pequeña alza de clientes "
            "dispararía la espera."
        )
    return texto


def frase_recomendacion(c_min: int | None, umbral_min: float, c_habitual: int | None) -> str:
    if c_min is None:
        return (
            f"Ni con muchos asesores se logra que la espera baje de {num(umbral_min, 0)} minutos."
        )
    texto = (
        f"Para que la espera en la hora pico no pase de {num(umbral_min, 0)} minutos se necesitan "
        f"al menos {_asesores(c_min)} disponibles."
    )
    if c_habitual is not None and c_min > c_habitual:
        # Es un promedio histórico de la hora pico, no lo de hoy.
        texto += f" En la hora pico suele haber {_libres(c_habitual)}."
    return texto


def frase_cierre(absorcion: Absorcion | None) -> str:
    if absorcion is None:
        return "Todavía no hay datos suficientes para estimar cuántos clientes cierran."
    p = absorcion.p_cierre[0]
    if p >= 0.95:
        reparto = "casi todos terminan cerrando"
    elif p < 0.05:
        reparto = "casi ninguno termina cerrando"
    else:
        cierran = _entero(p * 10)
        reparto = f"unos {cierran} terminan cerrando y {10 - cierran} abandonan"
    return (
        f"De cada 10 clientes que consultan, {reparto}. En promedio un cliente necesita unos "
        f"{num(absorcion.pasos[0])} seguimientos para llegar a un resultado."
    )


def frases_por_etapa(absorcion: Absorcion | None) -> list[str]:
    if absorcion is None:
        return []
    return [
        f"{NOMBRES[etapa]} → cierre: {num(absorcion.p_cierre[i] * 100, 0)} %"
        for i, etapa in enumerate((1, 2, 3))
    ]
