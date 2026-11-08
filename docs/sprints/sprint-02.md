# Sprint 2 — Diseño (Fase 2)
**Fechas:** 30-nov-2026 → 13-dic-2026 (se adelantó el arranque el 8-nov) · **Milestone:** Sprint 2 - Diseno

**Objetivo:** diseño de datos sólido, identidad visual y wireframes, y generador de datos simulados, listos para construir la gestión.

## Historias comprometidas
- [x] Diagrama Entidad-Relación (`docs/diseno/ER.md`) — [#19](https://github.com/Williamtrix2022/HogarSits/issues/19)
- [ ] ADR-002: autotransiciones de Markov — [#20](https://github.com/Williamtrix2022/HogarSits/issues/20) *(bloqueado hasta la segunda ronda de entrevistas, #55)*
- [x] Wireframes (`docs/diseno/WIREFRAMES.md`: 14 pantallas, mapa, flujos) — [#21](https://github.com/Williamtrix2022/HogarSits/issues/21)
- [x] Refactor de modelos y migraciones (28 tests de integridad sobre PostgreSQL) — [#22](https://github.com/Williamtrix2022/HogarSits/issues/22)
- [x] Comando seed_datos_simulados (`docs/diseno/DATOS_SIMULADOS.md`; 22 tests) — [#23](https://github.com/Williamtrix2022/HogarSits/issues/23)

## Log de avance
- 2026-11-08: modelo de datos rediseñado (Visita, HorarioAsesor, FotoInmueble, HistorialEstadoInmueble; Inmueble/Solicitud ampliados). Reglas de agenda y tiempos como restricciones de PostgreSQL (`ExclusionConstraint` + `CHECK`). ER con justificación de decisiones, ADR-003, migraciones aplicadas y probadas.
- 2026-11-08: generador de datos simulados (#23): simulación en Python puro + comando; recupera λ, μ y P de la Propuesta en los tests. Hallazgo: con la matriz del README las visitas saturan a los asesores y no se reproducen las esperas de la encuesta (ver DATOS_SIMULADOS §5); nueva pregunta para la ronda 2.
- 2026-11-08: wireframes en Mermaid (#21): mapa del sitio, 3 flujos, 14 pantallas con la identidad visual, trazabilidad a historias e issues; sintaxis validada con el parser de Mermaid 11.5.

## Estado (8-nov-2026)
4 de 5 hechos. Falta **#20 (ADR-002)**, bloqueado por la segunda ronda de entrevistas (#55): hace falta saber cómo registran las inmobiliarias un seguimiento que no cambia la etapa.

## Retro parcial
- Bien: el modelo con integridad en la BD (28 tests) y el generador de datos dieron una base sólida; la encuesta cambió el diseño antes de escribir pantallas.
- Mejorar: el generador **no reproduce las esperas reportadas** (ver `DATOS_SIMULADOS.md` §5): preguntar quién hace las visitas y cuántas por día.

## Review / Retro
_Se completan al cerrar el sprint (con el ADR-002)._

## Aprendizajes
- `auto_now_add` ignora el valor asignado: para datos históricos/simulados se usa `default=timezone.now, editable=False`.
- `ExclusionConstraint` requiere la extensión `btree_gist` (`BtreeGistExtension` en la migración) y solo funciona en PostgreSQL.
- Agregar un campo obligatorio a una tabla existente: generar la migración con un default temporal y fijar `preserve_default=False`.
