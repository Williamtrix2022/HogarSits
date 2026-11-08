# ADR-003 — Modelo de datos con integridad en la base de datos

**Estado:** aceptada · **Fecha:** 2026-11-08 · **Relacionadas:** ADR-001 (stack), ADR-002 (pendiente: autotransiciones de Markov, #20) · **Detalle:** [`docs/diseno/ER.md`](../diseno/ER.md)

## Contexto
Los modelos estocásticos solo valen lo que valen los datos que los alimentan (hora de llegada, inicio y fin de atención, transiciones de etapa). La encuesta (ronda 1) muestra que las inmobiliarias ya sufren inconsistencias: visitas cruzadas, inmuebles ofrecidos cuando ya estaban cerrados, solicitudes perdidas. El sistema tiene pocos usuarios pero **varios puntos de escritura** (formularios, admin, comandos de carga, futuros scripts), por lo que validar solo en la interfaz no basta.

## Decisión
1. Las reglas que dependen de una sola fila o de un rango de tiempo se implementan como **restricciones de PostgreSQL** (`CHECK`, `UNIQUE` funcional y `EXCLUDE` con `btree_gist`); las que dependen de varias tablas o de la lógica de etapas, en una **capa de servicio** con transacciones.
2. Las visitas usan `ExclusionConstraint` con `tstzrange [inicio, fin)` por asesor y por inmueble, excluyendo las canceladas.
3. `timestamp_llegada` usa `default=timezone.now` (no `auto_now_add`) para admitir datos históricos y simulados.
4. `on_delete=PROTECT` en relaciones que preservan historial; los inmuebles se desactivan.
5. `etapa_actual` es una copia denormalizada; `SeguimientoEtapa` es la fuente de verdad.
6. El asesor es `AUTH_USER_MODEL`; su disponibilidad se modela con `HorarioAsesor` y las `Visita`.
7. `SeguimientoEtapa` **no** prohíbe `origen = destino` hasta que ADR-002 decida.
8. Una sola inmobiliaria por instalación (sin multi-tenant).

## Alternativas descartadas
- **Validar solo en formularios/`clean()`:** no protege de concurrencia ni de escrituras fuera de la UI.
- **Bloquear franjas con una tabla de "slots":** más estructuras y más código que una restricción declarativa.
- **Calcular `etapa_actual` solo con la última transición:** consultas más lentas y complejas en cada listado sin beneficio a esta escala.
- **Perfil de asesor propio (`Asesor` con `OneToOne` a `User`):** duplica datos; no hace falta hasta que existan campos propios.
- **`inmobiliaria_id` en todas las tablas:** coste inmediato sin usuario que lo necesite.

## Consecuencias
- (+) Los datos que llegan a λ, μ y P son consistentes por construcción; la agenda es segura ante concurrencia; los tests (28) verifican las reglas contra PostgreSQL real.
- (+) La BD documenta las reglas de negocio con nombre (`visita_sin_cruce_asesor`, …).
- (−) **Acoplamiento a PostgreSQL** (`btree_gist`, `EXCLUDE`): no se puede usar SQLite. Ya era el stack elegido (ADR-001).
- (−) Los errores de BD son técnicos: la capa de servicio/`clean()` debe traducirlos a mensajes claros para el usuario (#30).
- (−) Al desplegar en RDS hay que confirmar que la extensión `btree_gist` está permitida (Sprint 6, #46).
- Si la ronda 2 confirma visitas grupales, se elimina `visita_sin_cruce_inmueble` con una migración.
