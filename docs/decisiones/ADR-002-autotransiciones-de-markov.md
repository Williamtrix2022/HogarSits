# ADR-002 — Cómo se modelan las autotransiciones de la cadena de Markov

**Estado:** aceptada (revisable con la encuesta E3) · **Fecha:** 2026-11-23 · **Issue:** #20 · **Relacionadas:** ADR-003 (modelo de datos), #32 (seguimiento de etapas), #37 (`services/markov.py`)

## Contexto
La matriz P del README tiene probabilidades de **permanecer** en una etapa (p. ej. Consulta→Consulta = 0,20). Para estimar esa diagonal desde los datos hay que decidir **cuándo cuenta un paso sin cambio de etapa** (decisión abierta 1 de `CASOS_DE_USO.md` §5). Es la decisión que define qué se guarda en `SeguimientoEtapa` y qué significa un «paso» en el tiempo esperado hasta la absorción.

La ronda 1 de encuestas (n = 3) no registró las respuestas a E3 (¿cómo anotan un seguimiento sin cambio de etapa?), así que no hay datos del campo. El modelo ya admite `origen = destino` (ADR-003, punto 7) y el generador de datos simulados (#23) ya guarda esos pasos como transición con la nota «sin avance».

## Decisión
**Un paso es un seguimiento registrado.** Cada vez que el asesor registra un seguimiento de una solicitud, se guarda una fila en `SeguimientoEtapa`:
- Si la etapa **cambia**, `origen ≠ destino`.
- Si **no cambia**, `origen = destino` (autotransición), con una nota opcional que dice qué pasó («sin avance», «no contestó»…).

Reglas que se derivan:
1. Solo se permiten las transiciones de RN-30: Consulta→{Consulta, Visita, Abandono}; Visita→{Visita, Negociación, Abandono}; Negociación→{Negociación, Cierre, Abandono}. **Quedarse en la misma etapa es válido solo en las transitorias**; Cierre y Abandono son absorbentes (RN-31).
2. La matriz se estima con frecuencias: `P[i][j] = n_ij / Σ_j n_ij`, contando las autotransiciones en `n_ii`. Es lo que `services/markov.py` (#37) debe implementar.
3. El «paso» es un **evento de seguimiento**, no un día. Los pasos esperados hasta la absorción (`N·1`) se interpretan como «seguimientos hasta cerrar o abandonar», no como días.
4. La pantalla de seguimiento ofrece «Seguir en la misma etapa» junto a las etapas siguientes, con el campo de nota.

## Alternativas descartadas
- **B. Observación periódica (un trabajo diario que escribe una autotransición por cada solicitud abierta sin cambios).** Hace que el «paso» sea un día calendario, que es más fácil de interpretar. Pero **fabrica datos** que nadie registró, la diagonal crece con el tiempo que una solicitud queda olvidada (premia no hacer seguimiento) y exige un trabajo programado en producción (Sprint 6).
- **C. No registrar autotransiciones (cadena «de saltos»).** Quita la diagonal: P tiene ceros en la diagonal y las probabilidades de absorción son **las mismas**, pero se pierde el Consulta→Consulta = 0,20 de la Propuesta y los pasos esperados dejan de coincidir (≈ 2,4). Sin diagonal tampoco se puede comparar con los datos simulados.

## Consecuencias
- (+) No hay que cambiar el esquema ni los datos simulados: ya usan esta convención.
- (+) Los datos reflejan lo que el asesor realmente hizo; no hay filas inventadas.
- (+) Coincide con la matriz de la Propuesta: P(cierre) ≈ 22,8 % y ≈ 2,4 pasos siguen siendo el ejemplo de prueba de #37.
- (−) La diagonal depende de **qué tan seguido se registra** un seguimiento: un equipo disciplinado mostrará más autotransiciones que uno que solo anota los avances. Hay que decirlo en el informe y en el dashboard (#38).
- (−) Exige que el asesor registre también los seguimientos sin avance; la pantalla lo facilita con una opción de un clic.

## Cuándo revisarla
Si la segunda ronda (#55, pregunta E3) muestra que las inmobiliarias **no anotan** los seguimientos sin avance, se pasa a la opción C (se quita la diagonal y se documenta) o se evalúa B con un trabajo diario. El cambio no toca el esquema, solo el servicio de #32 y la estimación de #37. Se registraría como un ADR que reemplaza a este.
