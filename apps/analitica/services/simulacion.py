"""Simulación de la operación de una inmobiliaria (RF-60, HU-10).

Módulo de Python puro: **no importa Django**. Devuelve estructuras simples que el comando
`seed_datos_simulados` persiste. Sirve para validar los modelos estocásticos con parámetros
conocidos (λ, μ, P), por eso todo es reproducible con una semilla.

Qué simula (calibrado con la ronda 1 de encuestas, docs/investigacion/resultados):
  * Llegadas: proceso de Poisson **no homogéneo**; λ constante por hora y con picos de mañana y
    tarde. El total diario es Poisson(clientes_por_dia).
  * Atención: cada cliente es atendido por el asesor que pueda empezar antes (cola FIFO con c
    asesores); duración exponencial con media `servicio_medio_min`.
  * Visitas: duran 30–120 min y **ocupan al asesor** (también bloquean el inmueble); nunca se
    cruzan, igual que exige la BD.
  * Etapas: cadena de Markov con la matriz `matriz` (por defecto la del README). Los pasos sin
    avance (p. ej. Consulta→Consulta) se registran como transiciones con origen = destino,
    provisional hasta que ADR-002 decida cómo se modelan.

Limitaciones: no cambia el estado de los inmuebles al cerrar un negocio (el inventario se
supone repuesto); las trayectorias se truncan al terminar el periodo (quedan "en curso").
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np

MATRIZ_README = (
    (0.20, 0.50, 0.00, 0.00, 0.30),
    (0.00, 0.15, 0.45, 0.00, 0.40),
    (0.00, 0.00, 0.20, 0.55, 0.25),
    (0.00, 0.00, 0.00, 1.00, 0.00),
    (0.00, 0.00, 0.00, 0.00, 1.00),
)

CONSULTA, VISITA, NEGOCIACION, CIERRE, ABANDONO = 1, 2, 3, 4, 5
BARRIOS = ("Centro", "La Castellana", "Cantaclaro", "El Recreo", "Mocarí", "Villa Margarita")


def validar_matriz(matriz) -> None:
    """La matriz debe ser 5x5, estocástica por filas y con Cierre/Abandono absorbentes."""
    if len(matriz) != 5 or any(len(f) != 5 for f in matriz):
        raise ValueError("La matriz de transición debe ser de 5x5.")
    for i, fila in enumerate(matriz, start=1):
        if any(p < 0 for p in fila):
            raise ValueError(f"La fila {i} tiene probabilidades negativas.")
        if not math.isclose(sum(fila), 1.0, abs_tol=1e-9):
            raise ValueError(f"La fila {i} debe sumar 1 (suma {sum(fila):.4f}).")
    if tuple(matriz[3]) != (0, 0, 0, 1, 0) or tuple(matriz[4]) != (0, 0, 0, 0, 1):
        raise ValueError("Cierre (4) y Abandono (5) deben ser estados absorbentes.")


def perfil_horario_por_defecto(apertura: int, cierre: int) -> tuple[float, ...]:
    """Pesos por hora con picos hacia las 10:00 y las 16:00 (valle al mediodía). Suman 1."""
    pesos = []
    for h in range(apertura, cierre):
        centro = h + 0.5
        w = 1.0 + math.exp(-((centro - 10) ** 2) / 2) + math.exp(-((centro - 16) ** 2) / 2)
        pesos.append(w)
    total = sum(pesos)
    return tuple(w / total for w in pesos)


@dataclass(frozen=True)
class Parametros:
    fecha_inicio: date
    dias: int = 30
    clientes_por_dia: float = 12.0
    n_asesores: int = 3
    servicio_medio_min: float = 25.0
    visita_min: int = 30
    visita_max: int = 120
    hora_apertura: int = 8
    hora_cierre: int = 18
    n_inmuebles: int = 40
    matriz: tuple = MATRIZ_README
    dias_entre_etapas: float = 2.0
    dias_laborales: tuple = (0, 1, 2, 3, 4, 5)  # lunes a sábado
    perfil_horario: tuple | None = None
    zona: str = "America/Bogota"
    semilla: int = 42

    def validar(self) -> None:
        validar_matriz(self.matriz)
        if self.dias < 1 or self.n_asesores < 1 or self.n_inmuebles < 1:
            raise ValueError("dias, n_asesores y n_inmuebles deben ser al menos 1.")
        if self.clientes_por_dia <= 0 or self.servicio_medio_min <= 0:
            raise ValueError("clientes_por_dia y servicio_medio_min deben ser positivos.")
        if not 0 <= self.hora_apertura < self.hora_cierre <= 24:
            raise ValueError("Horario inválido: se requiere 0 <= apertura < cierre <= 24.")
        if not 0 < self.visita_min <= self.visita_max:
            raise ValueError("Duración de visita inválida: 0 < visita_min <= visita_max.")
        if (self.hora_cierre - self.hora_apertura) * 60 < self.visita_max:
            raise ValueError("La visita más larga no cabe en el horario de atención.")
        horas = self.hora_cierre - self.hora_apertura
        if self.perfil_horario is not None and len(self.perfil_horario) != horas:
            raise ValueError(f"perfil_horario debe tener {horas} valores (uno por hora).")


@dataclass
class InmuebleSim:
    operacion: str  # VENTA | ALQUILER
    tipo_inmueble: str  # CASA | APARTAMENTO
    precio: float
    area_m2: float
    habitaciones: int
    barrio: str


@dataclass
class EtapaSim:
    origen: int
    destino: int
    fecha: datetime
    nota: str = ""


@dataclass
class VisitaSim:
    inmueble: int
    asesor: int
    inicio: datetime
    fin: datetime


@dataclass
class SolicitudSim:
    cliente: int
    inmueble: int | None
    asesor: int
    tipo_interes: str  # COMPRA | ALQUILER
    presupuesto: float
    llegada: datetime
    inicio: datetime
    fin: datetime
    etapa_actual: int = CONSULTA
    etapas: list[EtapaSim] = field(default_factory=list)
    visitas: list[VisitaSim] = field(default_factory=list)


@dataclass
class Resultado:
    parametros: Parametros
    inmuebles: list[InmuebleSim]
    n_clientes: int
    solicitudes: list[SolicitudSim]


def _libre(intervalos, ini, fin) -> bool:
    """¿[ini, fin) no se cruza con ningún intervalo? (rangos semiabiertos, como en la BD)."""
    return all(fin <= a or ini >= b for a, b in intervalos)


def _primer_hueco(intervalos, desde, duracion):
    """Primer instante >= desde en que cabe `duracion` sin cruzar los intervalos ocupados."""
    candidato = desde
    for a, b in sorted(intervalos):
        if candidato + duracion <= a:
            break
        if candidato < b:
            candidato = b
    return candidato


def _precio(rng, operacion: str) -> float:
    if operacion == "VENTA":
        valor = rng.lognormal(math.log(180_000_000), 0.5)
        return float(round(min(max(valor, 60_000_000), 900_000_000), -6))
    valor = rng.lognormal(math.log(1_300_000), 0.45)
    return float(round(min(max(valor, 500_000), 6_000_000), -4))


def _generar_inmuebles(rng, n: int) -> list[InmuebleSim]:
    inmuebles = []
    for _ in range(n):
        operacion = "VENTA" if rng.random() < 0.6 else "ALQUILER"
        tipo = "CASA" if rng.random() < 0.55 else "APARTAMENTO"
        inmuebles.append(
            InmuebleSim(
                operacion=operacion,
                tipo_inmueble=tipo,
                precio=_precio(rng, operacion),
                area_m2=float(round(rng.uniform(45, 220), 1)),
                habitaciones=int(rng.integers(1, 6)),
                barrio=str(BARRIOS[int(rng.integers(0, len(BARRIOS)))]),
            )
        )
    return inmuebles


def simular(p: Parametros) -> Resultado:
    """Genera `p.dias` días de operación. Determinista para una misma `p.semilla`."""
    p.validar()
    rng = np.random.default_rng(p.semilla)
    tz = ZoneInfo(p.zona)
    pesos = p.perfil_horario or perfil_horario_por_defecto(p.hora_apertura, p.hora_cierre)
    inmuebles = _generar_inmuebles(rng, p.n_inmuebles)
    ocupado_asesor: list[list[tuple[datetime, datetime]]] = [[] for _ in range(p.n_asesores)]
    ocupado_inmueble: list[list[tuple[datetime, datetime]]] = [[] for _ in range(p.n_inmuebles)]
    periodo_fin = datetime.combine(p.fecha_inicio + timedelta(days=p.dias), time(0), tzinfo=tz)

    def a_horario(t: datetime) -> datetime:
        """Lleva `t` al siguiente instante dentro del horario laboral."""
        while True:
            apertura = t.replace(hour=p.hora_apertura, minute=0, second=0, microsecond=0)
            cierre = t.replace(hour=p.hora_cierre % 24, minute=0, second=0, microsecond=0)
            if p.hora_cierre == 24:
                cierre = apertura.replace(hour=0) + timedelta(days=1)
            if t.weekday() not in p.dias_laborales or t >= cierre:
                t = apertura + timedelta(days=1)
                continue
            return max(t, apertura)

    def hueco_visita(desde: datetime, dur: timedelta, asesor: int, inmueble: int):
        """Primera franja de 30 min con asesor e inmueble libres, dentro del horario."""
        t = desde.replace(second=0, microsecond=0)
        if t < desde:
            t += timedelta(minutes=1)
        if t.minute % 30:
            t += timedelta(minutes=30 - t.minute % 30)
        for _ in range(15 * 48):  # hasta ~15 días de búsqueda
            t = a_horario(t)
            cierre = t.replace(hour=p.hora_cierre % 24, minute=0, second=0, microsecond=0)
            if p.hora_cierre == 24:
                cierre = t.replace(hour=0, minute=0) + timedelta(days=1)
            if t + dur <= cierre:
                if _libre(ocupado_asesor[asesor], t, t + dur) and _libre(
                    ocupado_inmueble[inmueble], t, t + dur
                ):
                    return t
                t += timedelta(minutes=30)
            else:
                t = cierre  # siguiente iteración la lleva a la apertura del día siguiente
        return None

    solicitudes: list[SolicitudSim] = []
    n_clientes = 0

    for d in range(p.dias):
        fecha = p.fecha_inicio + timedelta(days=d)
        if fecha.weekday() not in p.dias_laborales:
            continue
        llegadas = []
        for i, w in enumerate(pesos):
            base = datetime.combine(fecha, time(p.hora_apertura + i), tzinfo=tz)
            for _ in range(int(rng.poisson(p.clientes_por_dia * w))):
                llegadas.append(base + timedelta(seconds=float(rng.uniform(0, 3600))))
        llegadas.sort()

        for llegada in llegadas:
            servicio = timedelta(minutes=max(1.0, float(rng.exponential(p.servicio_medio_min))))
            inicio, asesor = min(
                (_primer_hueco(ocupado_asesor[a], llegada, servicio), a)
                for a in range(p.n_asesores)
            )
            fin = inicio + servicio
            ocupado_asesor[asesor].append((inicio, fin))

            if n_clientes == 0 or rng.random() < 0.9:
                cliente, n_clientes = n_clientes, n_clientes + 1
            else:
                cliente = int(rng.integers(0, n_clientes))

            inmueble = int(rng.integers(0, p.n_inmuebles)) if rng.random() < 0.85 else None
            if inmueble is not None:
                operacion = inmuebles[inmueble].operacion
                precio = inmuebles[inmueble].precio * float(rng.uniform(0.85, 1.05))
            else:
                operacion = "VENTA" if rng.random() < 0.6 else "ALQUILER"
                precio = _precio(rng, operacion)
            sol = SolicitudSim(
                cliente=cliente,
                inmueble=inmueble,
                asesor=asesor,
                tipo_interes="COMPRA" if operacion == "VENTA" else "ALQUILER",
                presupuesto=float(round(precio, -3)),
                llegada=llegada,
                inicio=inicio,
                fin=fin,
            )

            etapa, t = CONSULTA, fin
            while etapa in (CONSULTA, VISITA, NEGOCIACION):
                destino = int(rng.choice(5, p=p.matriz[etapa - 1])) + 1
                espera = timedelta(days=float(rng.exponential(p.dias_entre_etapas)))
                siguiente = a_horario(t + espera)
                if etapa == CONSULTA and destino == VISITA:
                    objetivo = sol.inmueble if sol.inmueble is not None else int(
                        rng.integers(0, p.n_inmuebles)
                    )
                    dur = timedelta(
                        minutes=5 * round(int(rng.integers(p.visita_min, p.visita_max + 1)) / 5)
                    )
                    inicio_visita = hueco_visita(siguiente, dur, asesor, objetivo)
                    if inicio_visita is None or inicio_visita >= periodo_fin:
                        break  # fuera del periodo simulado: la solicitud queda en curso
                    ocupado_asesor[asesor].append((inicio_visita, inicio_visita + dur))
                    ocupado_inmueble[objetivo].append((inicio_visita, inicio_visita + dur))
                    sol.visitas.append(
                        VisitaSim(objetivo, asesor, inicio_visita, inicio_visita + dur)
                    )
                    siguiente = inicio_visita
                if siguiente >= periodo_fin:
                    break
                sol.etapas.append(
                    EtapaSim(etapa, destino, siguiente, "sin avance" if destino == etapa else "")
                )
                etapa, t = destino, siguiente
            sol.etapa_actual = etapa
            solicitudes.append(sol)

    return Resultado(p, inmuebles, n_clientes, solicitudes)
