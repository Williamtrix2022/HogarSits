# Sprint 2 — Diseño (Fase 2)
**Fechas:** 30-nov-2026 → 13-dic-2026 (se adelantó el arranque el 8-nov) · **Milestone:** Sprint 2 - Diseno

**Objetivo:** diseño de datos sólido, identidad visual y wireframes, y generador de datos simulados, listos para construir la gestión.

## Historias comprometidas
- [x] Diagrama Entidad-Relación (`docs/diseno/ER.md`) — [#19](https://github.com/Williamtrix2022/HogarSits/issues/19)
- [x] ADR-002: autotransiciones de Markov (`docs/decisiones/ADR-002-autotransiciones-de-markov.md`, aceptada y revisable con E3) — [#20](https://github.com/Williamtrix2022/HogarSits/issues/20)
- [x] Wireframes (`docs/diseno/WIREFRAMES.md`: 14 pantallas, mapa, flujos) — [#21](https://github.com/Williamtrix2022/HogarSits/issues/21)
- [x] Refactor de modelos y migraciones (28 tests de integridad sobre PostgreSQL) — [#22](https://github.com/Williamtrix2022/HogarSits/issues/22)
- [x] Comando seed_datos_simulados (`docs/diseno/DATOS_SIMULADOS.md`; 22 tests) — [#23](https://github.com/Williamtrix2022/HogarSits/issues/23)

## Log de avance
- 2026-11-08: modelo de datos rediseñado (Visita, HorarioAsesor, FotoInmueble, HistorialEstadoInmueble; Inmueble/Solicitud ampliados). Reglas de agenda y tiempos como restricciones de PostgreSQL (`ExclusionConstraint` + `CHECK`). ER con justificación de decisiones, ADR-003, migraciones aplicadas y probadas.
- 2026-11-08: generador de datos simulados (#23): simulación en Python puro + comando; recupera λ, μ y P de la Propuesta en los tests. Hallazgo: con la matriz del README las visitas saturan a los asesores y no se reproducen las esperas de la encuesta (ver DATOS_SIMULADOS §5); nueva pregunta para la ronda 2.
- 2026-11-08: wireframes en Mermaid (#21): mapa del sitio, 3 flujos, 14 pantallas con la identidad visual, trazabilidad a historias e issues; sintaxis validada con el parser de Mermaid 11.5.
- 2026-11-23: ADR-002 (#20): un paso de Markov es un seguimiento registrado y las autotransiciones se guardan con `origen = destino` (coincide con el generador de datos y con la matriz del README). Alternativas descartadas: observación diaria y cadena sin diagonal.

## Estado (23-nov-2026)
5 de 5 hechos. El ADR-002 se aceptó sin los datos de E3 (la ronda 1 no los recogió) y queda **revisable** cuando se complete #55; el ADR dice cuándo y qué cambiaría.

## Retro parcial
- Bien: el modelo con integridad en la BD (28 tests) y el generador de datos dieron una base sólida; la encuesta cambió el diseño antes de escribir pantallas.
- Mejorar: el generador **no reproduce las esperas reportadas** (ver `DATOS_SIMULADOS.md` §5): preguntar quién hace las visitas y cuántas por día.

## Review / Retro
**Review:** 5 de 5 historias entregadas: ER, ADR-002 y ADR-003, wireframes, modelos con integridad en la BD y generador de datos simulados.
**Retro:** bien, decidir la integridad en la BD antes de las pantallas; mejorar, el ADR-002 esperó datos de campo que la ronda 1 no recogió: para la próxima, anotar las respuestas a las preguntas clave durante la entrevista.

## Aprendizajes
- `auto_now_add` ignora el valor asignado: para datos históricos/simulados se usa `default=timezone.now, editable=False`.
- `ExclusionConstraint` requiere la extensión `btree_gist` (`BtreeGistExtension` en la migración) y solo funciona en PostgreSQL.
- Agregar un campo obligatorio a una tabla existente: generar la migración con un default temporal y fijar `preserve_default=False`.
