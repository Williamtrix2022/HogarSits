# HogarSits — Generador de datos simulados

**Versión:** 1.0 · **Fecha:** 2026-11-08 · **Sprint:** 2 · **Issue:** #23 (RF-60, HU-10)
**Código:** `apps/analitica/services/simulacion.py` (Python puro, sin Django) · `apps/analitica/management/commands/seed_datos_simulados.py` · **Tests:** `tests/test_simulacion.py`, `tests/test_seed_comando.py` (22).

Para qué sirve: desarrollar y **validar** los modelos (Poisson, colas, Markov) con parámetros **conocidos** antes de tener datos reales. Si el modelo estima λ, μ y P cerca de los valores con los que se simuló, el código es correcto (#41).

## 1. Uso

```bash
python manage.py seed_datos_simulados                         # 30 días, parámetros por defecto
python manage.py seed_datos_simulados --dias 90 --asesores 4 --clientes-por-dia 15
python manage.py seed_datos_simulados --matriz '[[...5x5...]]' --semilla 7
python manage.py seed_datos_simulados --reemplazar            # borra lo simulado y regenera
python manage.py seed_datos_simulados --limpiar               # solo borra lo simulado
```

**Seguridad:** lo simulado se marca (usuarios `sim_asesorN`, correos `@sim.hogarsits.test`, inmuebles `[SIM] …`) y `--limpiar`/`--reemplazar` solo borran esas marcas; nunca datos reales (hay un test). Sin `--reemplazar`, el comando se niega a generar si ya hay datos simulados. Misma `--semilla` → mismos datos.

## 2. Parámetros y valores por defecto

| Parámetro | Defecto | Origen |
|---|---|---|
| `--dias` | 30 (termina hoy) | — |
| `--clientes-por-dia` | 12 (Poisson) | Ronda 1: 4–20 por día |
| `--asesores` | 3 | Ronda 1: 2–5 |
| `--servicio-min` | 25 (exponencial) | Ronda 1: primera atención 10–60 min |
| `--visita-min` / `--visita-max` | 30 / 120 | Ronda 1: visitas de 30–120 min |
| `--apertura` / `--cierre` | 8 / 18 (lunes a sábado) | Ronda 1: 9–12 h de atención |
| `--inmuebles` | 40 | Ronda 1: 27–80 |
| `--dias-entre-etapas` | 2 (media, exponencial) | Supuesto; validar en la ronda 2 |
| `--matriz` | La del README | Hipotética (Propuesta §5.3) |
| Perfil horario | Picos hacia las 10:00 y las 16:00, valle al mediodía | Ronda 1: picos de mañana y tarde |

## 3. Qué simula

1. **Llegadas:** Poisson **no homogéneo**: por cada hora, `Poisson(clientes_por_dia × peso_hora)`, con hora de llegada uniforme dentro de la hora.
2. **Atención:** cola con c asesores; cada cliente va con el asesor que pueda empezar antes; tiempo de servicio exponencial. Hay espera cuando todos están ocupados.
3. **Visitas:** al pasar de Consulta a Visita se agenda una visita (30–120 min) en el primer hueco de 30 min **libre para ese asesor y para ese inmueble**, dentro del horario. La visita **ocupa al asesor**, así que reduce los asesores disponibles para atender (el hallazgo de la ronda 1).
4. **Etapas:** cadena de Markov con la matriz dada, con tiempos exponenciales entre etapas ajustados a horario laboral. Los pasos sin avance (Consulta→Consulta) se guardan como transición con origen = destino y nota «sin avance» (**provisional hasta ADR-002**).
5. **Censura:** las trayectorias se cortan al terminar el periodo (quedan «en curso»), como en datos reales.

## 4. Qué se verifica (tests)
Mismos datos con la misma semilla · λ diario recuperado (±5 %) · picos de mañana y tarde · tiempo de servicio medio recuperado (±5 %) · ningún asesor atiende dos cosas a la vez, y las consultas no se solapan con sus visitas · visitas sin cruces por asesor ni inmueble y dentro de horario · transiciones válidas · **P(cierre | Consulta) = 22,8 % ± 2,5 y 2,4 pasos** (valores de la Propuesta) · matriz P estimada a ±0,03 de la real · validación de parámetros · el comando respeta las restricciones de la BD, no toca datos reales y es idempotente con `--reemplazar`.

## 5. Límites y hallazgo (leer antes de usar los datos)

**El generador no reproduce las esperas que reportaron las inmobiliarias.** Simulando 120 días con los perfiles de la ronda 1 (valores puntuales, n = 3):

| Perfil | Parámetros | Espera media simulada | Espera reportada |
|---|---|---|---|
| I01 | 20 cl/día · 2 asesores · servicio 45 min · 7–19 h | **217 min** (sistema saturado) | 30 min |
| I02 | 8 cl/día · 4 asesores · servicio 20 min | 0,1 min | 10 min |
| I04 | 4 cl/día · 2 asesores · servicio 20 min | 0,5 min | 15 min |

Lectura (hipótesis, no conclusión):
- **I01 se satura** porque, con la matriz del README, ~6 de cada 10 clientes terminan agendando una visita y esa visita (≈75 min) ocupa al **mismo** asesor: 20 consultas × 45 min + ~12 visitas × 75 min ≈ 30 h de trabajo al día para 2 asesores × 12 h. En la realidad las visitas pueden hacerlas otras personas, ser menos frecuentes o repartirse de otro modo. Falta saber **quién hace las visitas y cuántas por día** (nueva pregunta para la ronda 2, #55).
- **I02 e I04 casi no tienen cola** en el modelo, pero reportan 10–15 min de espera: puede ser percepción, ráfagas más agudas que mis picos, o tareas fuera de las visitas (WhatsApp, papeleo) que ocupan al asesor y que el modelo no representa.
- Conclusión práctica: los parámetros por defecto producen **datos útiles para probar el código**, no un retrato de ninguna inmobiliaria real. La calibración con datos reales queda para el piloto (Sprint 6).

Otras simplificaciones: no cambia el estado de los inmuebles al cerrar (se supone inventario repuesto); un cliente ≈ una solicitud (90 % clientes nuevos); no hay canal de llegada ni ausencias de asesores; la espera entre etapas es exponencial (supuesto).
