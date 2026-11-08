# Sprint 2 — Diseño (Fase 2)
**Fechas:** 30-nov-2026 → 13-dic-2026 (se adelantó el arranque el 8-nov) · **Milestone:** Sprint 2 - Diseno

**Objetivo:** diseño de datos sólido, identidad visual y wireframes, y generador de datos simulados, listos para construir la gestión.

## Historias comprometidas
- [x] Diagrama Entidad-Relación (`docs/diseno/ER.md`) — [#19](https://github.com/Williamtrix2022/HogarSits/issues/19)
- [ ] ADR-002: autotransiciones de Markov — [#20](https://github.com/Williamtrix2022/HogarSits/issues/20) *(bloqueado hasta la segunda ronda de entrevistas, #55)*
- [ ] Wireframes de las pantallas principales (con la identidad visual) — [#21](https://github.com/Williamtrix2022/HogarSits/issues/21)
- [x] Refactor de modelos y migraciones (28 tests de integridad sobre PostgreSQL) — [#22](https://github.com/Williamtrix2022/HogarSits/issues/22)
- [ ] Comando seed_datos_simulados (con picos por franja y visitas que ocupan al asesor) — [#23](https://github.com/Williamtrix2022/HogarSits/issues/23)

## Log de avance
- 2026-11-08: modelo de datos rediseñado (Visita, HorarioAsesor, FotoInmueble, HistorialEstadoInmueble; Inmueble/Solicitud ampliados). Reglas de agenda y tiempos como restricciones de PostgreSQL (`ExclusionConstraint` + `CHECK`). ER con justificación de decisiones, ADR-003, migraciones aplicadas y probadas.

## Review / Retro
_Pendiente._

## Aprendizajes
- `auto_now_add` ignora el valor asignado: para datos históricos/simulados se usa `default=timezone.now, editable=False`.
- `ExclusionConstraint` requiere la extensión `btree_gist` (`BtreeGistExtension` en la migración) y solo funciona en PostgreSQL.
- Agregar un campo obligatorio a una tabla existente: generar la migración con un default temporal y fijar `preserve_default=False`.
