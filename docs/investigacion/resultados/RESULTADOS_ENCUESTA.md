# HogarSits — Resultados de la validación con inmobiliarias (ronda 1)

**Fecha de análisis:** 2026-11-07 · **Sprint:** 1 · **Instrumento:** [`ENCUESTA_INMOBILIARIAS.md`](../ENCUESTA_INMOBILIARIAS.md)
**Fuente:** exportación de Google Forms (5-nov-2026). El archivo crudo **no se versiona** (repositorio público; ver §8). Aquí solo hay resultados agregados y anónimos.

> **Cuidado con la muestra: n = 3** (I01, I02, I04) frente a la meta de 8–15. Son conteos, no porcentajes representativos. Sirven para orientar el diseño y detectar contradicciones con los supuestos, no para generalizar a Montería. Falta I03 (¿se perdió, se descartó o está pendiente?).

## 1. Perfil de la muestra

| | I01 | I02 | I04 |
|---|---|---|---|
| Tamaño declarado | Mediana | Mediana | Pequeña |
| Asesores (total / en un día típico) | 3 / 2 | 5 / 4 | 2 / 2 |
| Inmuebles en cartera | 27 | 80 | 35 |
| Operación | Ambos | Ambos | Ambos |
| Horario | 7:00–19:00 | 8:00–18:00 | 8:00–17:00 |

Las tres trabajan **venta y alquiler a la vez**, con carteras de 27 a 80 inmuebles y 2 a 5 asesores: escala pequeña.

## 2. Situación actual (P1–P4)

| Pregunta | Resultado (de 3) |
|---|---|
| Registro de inmuebles (P1) | Excel/Sheets: **3** |
| Seguimiento de clientes (P2) | WhatsApp manual: **2** · Hojas de cálculo: 1 |
| Problemas para actualizar/seguir (P3) | Frecuentemente: **2** · Algunas veces: 1 |
| Perder una solicitud sin seguimiento (P4) | **3 de 3** |
| Ofrecer un inmueble ya vendido/arrendado (P4) | 2 |
| Visitas cruzadas (P4) | 2 |
| Clientes esperando por falta de asesores (P4) | 2 |
| Ninguno de los problemas (P4) | 0 |

**Lectura:** todas viven en Excel + WhatsApp y **todas** han perdido solicitudes por falta de seguimiento. Los cuatro problemas que HogarSits pretende resolver aparecen al menos en 2 de 3.

## 3. Función más útil (P5; 1 = más útil)

| Función | I01 | I02 | I04 | Promedio |
|---|---|---|---|---|
| Inventario centralizado | 1 | 1 | 1 | **1,0** |
| Agenda y alertas de seguimiento | 3 | 2 | 2 | **2,3** |
| Reportes de atención y desempeño | 4 | 3 | 3 | 3,3 |
| Probabilidad de cierre | 2 | 4 | 4 | 3,3 |

**Lectura (importante):** el inventario es lo primero para las tres y la agenda/alertas lo segundo. Lo que diferencia a HogarSits en la Propuesta, **la analítica estocástica, queda de último** (solo I01 valora la probabilidad de cierre). Es coherente con el orden de sprints actual (gestión antes que analítica), pero obliga a **presentar la analítica en lenguaje de negocio** y no como "Poisson/Markov".

## 4. Interés y disposición a pagar (P6–P8)

- Probar un prototipo: **Sí 3/3**. Pagar: "necesito conocer el producto" 1, "depende del precio y las funciones" 2, ningún "sí" directo.
- Precio razonable: $50.000–$100.000: **2** · $100.000–$180.000: 1. Está **en o por debajo del rango de los competidores** del Estudio (~$100.000–$180.000/mes).
- Piloto: **Sí 3/3**. Datos históricos anonimizados: No 1, Tal vez 2, Sí 0.

## 5. Parámetros operativos (P9–P12)

| | I01 | I02 | I04 |
|---|---|---|---|
| Clientes nuevos / día (P9a) | 20 | 8 | 4 |
| Horas pico (P9b) | Mañana, mediodía, tarde | Mañana, tarde, fines de semana | Mañana, tarde |
| Primera atención (P10a) | 30–60 min | 10–30 min | 10–30 min |
| Visita a un inmueble (P10b) | 120 min | 45 min | 30 min |
| Espera típica (P12a) | 30 min | 10 min | 15 min |
| Espera máxima aceptable (P12b) | 20 min | 30 min | 30 min |

**Lectura:** llegadas de 4 a 20 clientes/día; picos en **mañana y tarde** (no uniformes); atención de 10 a 60 min; las **visitas duran 30–120 min** y sacan al asesor de la oficina.

### Contraste con el modelo M/M/c (ilustrativo)
Con puntos medios de los rangos (λ = clientes/día ÷ horas de atención; tiempo de servicio = punto medio de P10a; c = asesores de un día típico):

| | λ (cl/h) | μ (cl/h) | c | ρ | Wq modelo | Wq reportado |
|---|---|---|---|---|---|---|
| I01 | 1,67 | 1,33 | 2 | 0,63 | **≈ 29 min** | 30 min |
| I02 | 0,80 | 3,00 | 4 | 0,07 | ≈ 0 min | 10 min |
| I04 | 0,44 | 3,00 | 2 | 0,07 | ≈ 0 min | 15 min |

- **I01 coincide** con el modelo (29 vs 30 min): el sistema M/M/c describe bien una oficina cargada y su espera (30 min) supera lo que considera aceptable (20 min). Con c = 2 el modelo recomienda revisar la dotación.
- **I02 e I04 no coinciden**: el modelo dice que casi no hay espera, pero reportan 10–15 min. Hipótesis a verificar: (a) los asesores están **fuera en visitas** y c efectivo es menor; (b) las llegadas son **a ráfagas**, no uniformes; (c) la espera incluye tareas por WhatsApp. Es una advertencia sobre los supuestos (supuestos de §7 de requerimientos): λ constante y servicio solo en oficina **no bastan**.
- Cálculo con n = 3, rangos y supuestos de exponencialidad no verificados: es una ilustración, no una conclusión.

## 6. Observaciones cualitativas (I02 e I04)

- Quieren centralizar inventario, organizar visitas, **recordatorios** y reportes de **desempeño de asesores**.
- Condiciones de adopción: **fácil de usar, económico, sin conocimientos técnicos y que proteja la información** de la inmobiliaria.
- Las notas **no registran** las respuestas a E2–E5 (etapas reales, seguimientos sin avance, reservas, visitas grupales): ADR-002 sigue sin datos.

## 7. Implicaciones para el diseño

| # | Hallazgo | Cambio propuesto | Dónde impacta |
|---|---|---|---|
| 1 | 3/3 pierden solicitudes; I02 pide recordatorios | Subir RF-25 (alerta sin seguimiento) de *debería* a **debe** y añadir **recordatorios de visita/seguimiento** | RF-25, #33 (Sprint 4) |
| 2 | Inventario es lo más valioso | Mantener CRUD de inmuebles como primera entrega; cuidar búsqueda y estado | #26 (Sprint 3) |
| 3 | La analítica es lo menos valorado | Mantener el módulo (requisito de la asignatura) pero con **lenguaje de negocio** ("de cada 10 clientes, X cierran", "con N asesores esperarías M min") y vista de administrador simple | HU-07 a HU-09, #38 |
| 4 | Piden desempeño por asesor (I02) | Añadir **indicadores por asesor** (solicitudes atendidas, visitas, cierres, tiempos) con los mismos datos | Nuevo RF, Sprint 5 |
| 5 | Visitas de 30–120 min sacan al asesor de la oficina | Modelar la **disponibilidad del asesor**: una visita lo ocupa. Define c efectivo | #22, decisión abierta 2 |
| 6 | Picos por franja, I02/I04 no calzan con λ constante | Estimar λ **por franja** (mañana/tarde/día de semana) y validar el supuesto de Poisson; el generador debe simular picos | #23, #35 |
| 7 | Escala pequeña (2–5 asesores, 27–80 inmuebles) | Priorizar sencillez de UI; RNF-06 (10 000 solicitudes) es holgado, no hay que sobredimensionar | RNF-05/06 |
| 8 | Precio esperado ≤ $100.000 | Solo informativo: sigue siendo prototipo académico; sin precio | — |
| 9 | Todas operan venta y alquiler | Confirmado: `Inmueble.tipo` y los dos tipos de cierre (vendido/arrendado) | Modelo |
| 10 | 3/3 quieren piloto; datos históricos "tal vez" | Pilotar con **I02** (más asesores, más cartera, notas detalladas); pedir historial en una segunda visita; mantener datos simulados | Sprint 6, #41 |

**Parámetros por defecto sugeridos para el generador de datos (RF-60):** 2–5 asesores; 9–12 h de atención; 4–20 llegadas/día repartidas con picos mañana/tarde; primera atención 10–60 min (exponencial); visita 30–120 min; espera máxima aceptable 20–30 min.

## 8. Privacidad y manejo del archivo crudo

El CSV contiene notas libres de los entrevistados y está pensado como material interno del equipo. Como el repositorio es **público**, se excluye con `.gitignore` (`docs/*.csv`) y solo se versionan estos resultados agregados. Recomendación: guardar el crudo en una carpeta privada del equipo (Drive). I04 pidió **anonimato**; I01 e I02 aceptan que se cite su nombre, pero en esta ronda no se publica ningún nombre.

## 9. Pendientes

- [ ] Aplicar la encuesta a más inmobiliarias hasta llegar al menos a 8 (faltan 5) y aclarar el estado de **I03**.
- [ ] Segunda ronda corta con I02 (piloto): E2 (etapas reales), E3 (seguimientos sin avance), E4 (reservas), E5 (visitas grupales/varias solicitudes), E7 (días para considerar perdida una solicitud).
- [ ] Decidir los cambios de la tabla §7 y reflejarlos en `REQUERIMIENTOS.md` v0.2 y en el backlog.
