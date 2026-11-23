# HogarSits — Supuestos de trabajo (escenarios simulados)

**Versión:** 1.0 · **Fecha:** 2026-11-23 · **Relacionados:** [`GUION_RONDA_2.md`](GUION_RONDA_2.md) · [`../diseno/DATOS_SIMULADOS.md`](../diseno/DATOS_SIMULADOS.md) · issue #55

> ## ⚠️ Esto NO son resultados de entrevistas
> Los valores de este documento son **hipótesis del equipo** para poder probar el sistema y medir **qué tanto cambian los resultados si el supuesto cambia**. **No provienen de ninguna inmobiliaria**, no son datos de campo y **no sustituyen** a la ronda 2. Cada uno se reemplaza por el dato real cuando exista. Citar uno de estos valores como si fuera un hallazgo sería presentar un dato inventado como investigación.

## 1. Qué es dato y qué es supuesto
| | Origen | Dónde está | Cómo se cita |
|---|---|---|---|
| **Dato real** | Ronda 1: 3 inmobiliarias (I01, I02, I04), por conveniencia | [`resultados/RESULTADOS_ENCUESTA.md`](resultados/RESULTADOS_ENCUESTA.md) | «En 3 de 3 inmobiliarias consultadas…» (conteos, n = 3) |
| **Supuesto** | Decisión del equipo, sin dato detrás | Este documento | «Se supuso N = 3 días; se probó N = 2, 5 y 7» |
| **Dato simulado** | Generado por `seed_datos_simulados` con una semilla | La BD, con marcas `sim_`, `@sim.hogarsits.test` y `[SIM]` | «Datos simulados con parámetros X» |

Los **perfiles de la ronda 1** (4 a 20 llegadas por día, 2 a 5 asesores, visitas de 30 a 120 min) sí son datos reales, aunque con n = 3; por eso el generador los usa como rango. Aquí solo van los parámetros **sin dato**.

## 2. Los supuestos
Cada fila dice qué se supone, el valor con el que hoy corre el sistema, el rango a probar, y **qué pregunta de la ronda 2 lo reemplazaría**.

| ID | Supuesto | Valor base (hoy) | Rango a probar | Lo reemplaza |
|---|---|---|---|---|
| **S1** | Días sin movimiento para marcar «sin seguimiento» (N) | 3 | 2 · 3 · 5 · 7 | Pregunta **E7** |
| **S2** | Cómo se cuenta un paso sin avance (diagonal de P) | Cada seguimiento cuenta (ADR-002) | Diagonal más alta y más baja | Pregunta **E3** |
| **S3** | Quién hace las visitas | El **mismo** asesor que atiende en oficina | Visitas más cortas; (ver límite en S3) | Pregunta **V1** |
| **S4** | Asesores disponibles en una oficina cargada | 3 | 2 · 3 · 4 | Ronda 1 da 2 a 5; el real, **V1** |
| **S5** | Días entre etapas de una solicitud | 2 (media, exponencial) | 1 · 2 · 5 | Preguntas **E3 / E7** |
| **S6** | Horario de atención | 8:00–18:00, lunes a sábado | 7–19 · 8–17 | Ronda 1 da 7–19, 8–18, 8–17 |

### S1 — N días sin seguimiento
No hay dato: la ronda 1 no preguntó cuántos días. El valor 3 es provisional (`DIAS_SIN_SEGUIMIENTO`, por defecto 3). **Efecto:** con N bajo hay más solicitudes marcadas «Sin seguimiento» y el panel «A quién contactar hoy» se llena de rojo; con N alto se esconden solicitudes que ya se enfriaron. Se mide contando las marcadas para cada N (ver §4).

### S2 — La diagonal de la matriz P
Las probabilidades de **permanecer** en una etapa dependen de cuánto se registre cada seguimiento (ADR-002). Se prueban dos variantes de la matriz base del README que cambian **solo la diagonal** y reparten el resto en la misma proporción. Valores calculados (no supuestos) con la matriz fundamental `N = (I − Q)⁻¹`:

| Variante | Diagonal (Consulta, Visita, Negociación) | P(cierre desde Consulta) | Pasos esperados desde Consulta |
|---|---|---|---|
| Menos permanencia | 0,05 · 0,05 · 0,05 | 22,8 % | 2,06 |
| **Base (README)** | 0,20 · 0,15 · 0,20 | 22,7 % | **2,40** |
| Más permanencia | 0,40 · 0,30 · 0,40 | 22,8 % | 3,11 |

**Lo que muestra:** la diagonal **no cambia la probabilidad de cierre** (≈ 22,8 % en las tres) pero **sí los pasos esperados** (2,06 → 3,11). Es la consecuencia del ADR-002: el modo de contar los pasos cambia el «tiempo hasta cerrar», no *si* se cierra. Matrices en JSON para `--matriz`:

```
menos: [[0.05,0.594,0,0,0.356],[0,0.05,0.503,0,0.447],[0,0,0.05,0.653,0.297],[0,0,0,1,0],[0,0,0,0,1]]
mas:   [[0.4,0.375,0,0,0.225],[0,0.3,0.371,0,0.329],[0,0,0.4,0.413,0.187],[0,0,0,1,0],[0,0,0,0,1]]
```

### S3 — Quién hace las visitas
El generador supone que **la visita ocupa al mismo asesor** que atiende en oficina. Con ese supuesto, una oficina de 2 asesores y 20 clientes al día **se satura** (hallazgo de `DATOS_SIMULADOS.md` §5: espera simulada de 217 min contra 30 reportados). Si en la realidad las visitas las hace otra persona, el modelo sobreestima la saturación.
**Límite honesto:** el generador **no tiene** una opción «visita hecha por otra persona». Con las banderas actuales solo se puede **aproximar** acortando las visitas (`--visita-min` y `--visita-max`). Si la pregunta V1 muestra que es el caso común, habrá que cambiar el generador (y `disponibilidad.py`), no solo un parámetro.

### S4, S5, S6
Se prueban con las banderas del generador (§3). No tienen mayor discusión: son perillas para ver sensibilidad.

## 3. Escenarios (todos hipotéticos)
Todos con `--semilla 7` y `--reemplazar` (borra solo lo simulado, nunca datos reales). **No se han ejecutado para este documento**: son recetas; los resultados se miran cuando existan los servicios del Sprint 5.

| Escenario | Qué prueba | Comando (`python manage.py seed_datos_simulados …`) |
|---|---|---|
| **E0 · Base** | Referencia con los valores por defecto | `--dias 60 --semilla 7 --reemplazar` |
| **E1 · Oficina cargada** | Perfil tipo I01 (saturación documentada) | `--dias 60 --clientes-por-dia 20 --asesores 2 --servicio-min 45 --apertura 7 --cierre 19 --semilla 7 --reemplazar` |
| **E2 · E1 con tercer asesor** | S4: cuánto alivia un asesor más | `--dias 60 --clientes-por-dia 20 --asesores 3 --servicio-min 45 --apertura 7 --cierre 19 --semilla 7 --reemplazar` |
| **E3 · E1 con visitas cortas** | S3: aproximación a «visitas que ocupan menos» | `--dias 60 --clientes-por-dia 20 --asesores 2 --servicio-min 45 --apertura 7 --cierre 19 --visita-min 30 --visita-max 45 --semilla 7 --reemplazar` |
| **E4 · Más permanencia** | S2: diagonal alta | `--dias 60 --matriz '<mas>' --semilla 7 --reemplazar` |
| **E5 · Seguimiento lento** | S5: etapas cada 5 días | `--dias 60 --dias-entre-etapas 5 --semilla 7 --reemplazar` |

En PowerShell, las comillas del JSON de `--matriz` se escriben distinto; usar un archivo o escapar con cuidado.

## 4. Cómo medir la sensibilidad
**Hoy** (sin esperar al Sprint 5):
- **S1:** cuántas solicitudes en curso quedan marcadas para cada N, **medido a la fecha en que terminó la simulación** (no a hoy):
  ```
  python manage.py shell -c "from django.db.models import Max; from apps.seguimiento.services import pendientes_de_seguimiento as p; from apps.seguimiento.models import SolicitudAtencion as S, SeguimientoEtapa as T; fin = max(S.objects.aggregate(m=Max('timestamp_llegada'))['m'], T.objects.aggregate(m=Max('fecha_transicion'))['m']); print({n: sum(x.sin_seguimiento for x in p(ahora=fin, umbral_dias=n)) for n in (1,2,3,5,7,14)}, 'de', len(p(ahora=fin)))"
  ```
  **Por qué «a la fecha de fin»:** los datos simulados envejecen con el calendario real. Medidos «a hoy», semanas después de generarlos, todas las solicitudes llevan más de 7 días sin movimiento y **cualquier N las marca todas**: la sensibilidad sale plana y no dice nada (así ocurrió al probar esta receta). Solo cuenta las solicitudes **en curso** al final del periodo.
  **Ejemplo ilustrativo (datos simulados, no de campo):** con los 310 datos simulados que hoy hay en la BD de desarrollo (parámetros de generación no registrados), de 68 solicitudes en curso quedan marcadas **42, 33, 17, 6, 1 y 0** para N = 1, 2, 3, 5, 7 y 14. Es decir, el supuesto S1 **sí mueve el resultado**: pasar de N = 3 a N = 5 deja la lista de «sin seguimiento» en un tercio. Esa sensibilidad es la razón para preguntar E7 en campo.
- **S3/S4:** pantalla **Administración → Horarios → Asesores disponibles** (`c` efectivo por franja) con los horarios cargados.

**Con el Sprint 5** (#35 a #37): λ por franja, M/M/c (ρ, Lq, Wq) y la matriz P estimada. La comparación útil es **cuánto se mueve cada resultado** entre escenarios, no su valor absoluto: si Wq cambia mucho al pasar de E2 a E1, ese supuesto importa y vale la pena preguntarlo en campo.

## 5. Cómo usarlos sin engañar a nadie
1. **Rotular siempre** lo simulado: en tablas y gráficas, «datos simulados (escenario E1)». Ninguna cifra de este documento va al informe sin esa etiqueta.
2. **Separar datos de supuestos** en el informe: una sección «Datos de campo (n = 3)» y otra «Supuestos y análisis de sensibilidad».
3. **Antes de una demo con datos reales**, ejecutar `seed_datos_simulados --limpiar`.
4. **Reemplazar, no acumular:** cuando llegue una respuesta de la ronda 2, se actualiza la fila del supuesto (valor, fuente, fecha) y se anota que **ya no es supuesto**.
5. **Si la ronda 2 no se hace**, decirlo: «No se realizó la segunda ronda; se usaron estos supuestos y se midió cuánto cambian los resultados».

**Texto sugerido para el informe:**
> *Los parámetros S1 a S6 no pudieron validarse con las inmobiliarias consultadas (n = 3 en la primera ronda; la segunda no se realizó / se realizó con n = __). Se adoptaron valores de trabajo y se analizó la sensibilidad de los resultados a su variación (§X). Las cifras derivadas de datos simulados se rotulan como tales y no deben interpretarse como el comportamiento de ninguna inmobiliaria real.*

## 6. Registro de reemplazos
| ID | Valor de trabajo | ¿Ya hay dato real? | Fuente y fecha | Valor definitivo |
|---|---|---|---|---|
| S1 | 3 días | ☐ | | |
| S2 | ADR-002 (cada seguimiento cuenta) | ☐ | | |
| S3 | Mismo asesor | ☐ | | |
| S4 | 3 asesores | ☐ | | |
| S5 | 2 días | ☐ | | |
| S6 | 8:00–18:00 L–S | ☐ | | |
