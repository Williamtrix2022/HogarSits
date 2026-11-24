# Sprint 5 — Analítica, Entrega 3 (Fase 4)
**Fechas:** 11-ene-2027 → 24-ene-2027 (se adelantó el arranque el 23-nov) · **Milestone:** Sprint 5 - Analitica (Entrega 3)

**Objetivo:** la analítica estocástica del proyecto: λ por franja y ajuste de Poisson, colas M/M/c y cadena de Markov, con un panel que las explique en lenguaje de negocio.

## Historias comprometidas
- [x] `services/poisson.py`: λ por franja y ajuste de Poisson (30 tests) — [#35](https://github.com/Williamtrix2022/HogarSits/issues/35)
- [x] `services/colas.py`: M/M/1 y M/M/c con Erlang C (32 tests) — [#36](https://github.com/Williamtrix2022/HogarSits/issues/36)
- [x] `services/markov.py`: matriz P, N=(I−Q)⁻¹ y absorción (26 tests) — [#37](https://github.com/Williamtrix2022/HogarSits/issues/37)
- [x] Dashboard analítico con Chart.js (51 tests) — [#38](https://github.com/Williamtrix2022/HogarSits/issues/38)
- [x] Subagente `revisor-estocastico` y skill `/modelo-estocastico` — [#39](https://github.com/Williamtrix2022/HogarSits/issues/39)
- [x] Exportar resultados a CSV (42 tests) — [#40](https://github.com/Williamtrix2022/HogarSits/issues/40)
- [x] Indicadores por asesor (24 tests) — [#54](https://github.com/Williamtrix2022/HogarSits/issues/54)

## Log de avance
- 2026-11-23: #35, #36, #37 — los tres modelos como **Python puro** (sin Django) y verificados contra los ejemplos del proyecto: M/M/1 con λ=2 y μ=3; wireframe W11 (2 asesores → 28,8 min, 3 → 4,0 min); matriz del README (P(cierre | Consulta) = 22,748 %, 2,3989 pasos). Además, comprobaciones **independientes**: la cadena de nacimiento y muerte para las colas, potencias de P para la absorción, y la recuperación de los parámetros de la simulación.
- 2026-11-23: #39 — subagente `revisor-estocastico` (solo lectura) y skill `/modelo-estocastico`. Su primera revisión de los tres módulos dio ✅ sin errores de resultado y tres reservas, que se atendieron: marca «al límite» (ρ > 0,95), matriz casi singular y grados de libertad ≥ 0.
- 2026-11-23: #38 — panel **Análisis** (demanda, asesores y esperas, probabilidad de cierre) con filtro de fechas y umbral de espera, frases en lenguaje de negocio (RF-59), detalle técnico plegable con tablas equivalentes, Chart.js 4.4.7 copiado al proyecto y advertencias (RN-40, RN-43, datos simulados, horarios sin cargar). Revisado con capturas.
- 2026-11-23: #40 — cinco tablas descargables en CSV para Excel es-CO (`;`, coma decimal, BOM), con neutralización de fórmulas y la marca `datos_simulados` en cada fila.
- 2026-11-23: #54 — indicadores por asesor; el asesor ve solo su fila (HU-13 CA2) y el administrador ve al equipo, con exportación.

## Estado (23-nov-2026)
**7 de 7 hechos** (584 pruebas, 4 `xfail` a propósito). **Siguiente:** Sprint 6 (pruebas, informe, despliegue en AWS y sustentación). Pendientes que no son de código: #55 (entrevistas) y #27 (bucket de S3). Deuda conocida: las correcciones E1 a E3 de la revisión (arriba) y **RN-33** (el historial de etapas se puede editar y borrar) afecta la fiabilidad de la matriz P y conviene resolverla antes del piloto.

## Review / Retro
**Review:** la matemática estocástica está completa, con cuatro tipos de prueba por modelo (ejemplo conocido, comprobación independiente, recuperación de parámetros simulados y bordes) y un panel que traduce cada cifra a lenguaje de negocio.
**Retro:** *bien:* escribir el ejemplo conocido antes del código y comprobar por un segundo camino; mirar las capturas del panel (destapó textos con «unos 1» y un gráfico aplastado por un valor atípico); el revisor como segundo par de ojos. *Mejorar:* varias de mis expectativas eran erróneas y las corrigió una prueba (ver Aprendizajes), así que conviene calcular el valor a mano **antes** de escribir el `assert`; la suite pasó de 4 a 14 minutos por corrida y conviene investigarlo; y quedó pendiente validar con datos reales (la ronda 2).

**Revisión independiente de la capa del panel** (agente `revisor-estocastico`, 23-nov-2026): ⚠️ *correcto con reservas*. Sin errores de unidades, de RN-22 ni de RN-42, y `c_efectivo_por_hora` coincide con `disponibilidad()` en 78 franjas (0 diferencias). **Hallazgos verificados en el código y pendientes de corrección** (se atienden en el Sprint 6, dentro de #42):
- **E1:** la última fila del ajuste de Poisson se rotula «P(X = k)» pero es «k o más».
- **E2:** `_redondear_c` fuerza c ≥ 1 aunque el promedio sea < 0,5, y contradice la advertencia «menos de un asesor libre».
- **E3:** «Hoy hay N asesores» es en realidad el promedio histórico de la hora pico.
- Riesgos y observaciones: promedio de c diluido por turnos que no empiezan en hora exacta (R1); frases que afirman más de lo que respalda el número (R3, R4, O1); `hay_simulados` no mira las transiciones (R5); dos «tiempos medios» con filtros distintos (R6); el CSV de colas no lleva sus parámetros (O2).

## Aprendizajes
- **Una expectativa que falla puede estar mal ella.** Esperé que mezclar horas con picos rechazara Poisson siempre; con picos suaves la dispersión es 1,05 y no se rechaza. La prueba correcta usa la dispersión teórica `1 + Var(λ)/E(λ)`.
- **«≈ 22,8 %» es doble redondeo.** El valor exacto es 22,748 %; a un decimal es 22,7 %. Los documentos (CLAUDE.md, Propuesta) arrastran el 22,8; el test afirma el exacto.
- **λ por franja exige contar las horas con cero llegadas.**
- **No usar «es igual al valor por defecto» como señal de «no hay dato»:** los datos simulados tenían justo el horario por defecto y el panel creyó que no había horarios.
- **Los datos simulados envejecen con el calendario real:** medidos «a hoy» semanas después, cualquier umbral marca todo. Se mide a la fecha en que terminó la simulación.
- **El modelo M/M/c trabaja con asesores completos:** redondear 1,8 → 2 y 1,4 → 1 puede cambiar la espera de minutos a horas; se declara en pantalla.
- **Un valor atípico aplasta un gráfico:** se recorta el eje y el punto se dibuja como triángulo, con el valor real en el tooltip y en la tabla.
- **Inyección de CSV:** cualquier celda de texto que empiece por `=`, `+`, `-` o `@` se interpreta como fórmula en Excel; se neutraliza con un apóstrofo (los números no se tocan).
- **Contar por solicitud, no por registro:** un registro duplicado de «→ Cierre» sumaba dos cierres.
- **Copiar Chart.js al proyecto** (con licencia y SHA-256) evita depender de un CDN en tiempo de ejecución.
