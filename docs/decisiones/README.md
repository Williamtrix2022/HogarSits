# Decisiones de arquitectura (ADR)

Una decisión por archivo: contexto, decisión, alternativas descartadas y consecuencias.

| ADR | Decisión | Estado |
|---|---|---|
| [ADR-001](ADR-001-stack.md) | Django monolito modular, PostgreSQL, servicios analíticos puros, CI, AWS Free Tier | Aceptada |
| ADR-002 | Cómo se modelan las autotransiciones de la cadena de Markov (issue #20) | **Pendiente**: espera la segunda ronda de entrevistas (#55) |
| [ADR-003](ADR-003-modelo-de-datos.md) | Integridad en la base de datos: `ExclusionConstraint`, `CHECK`, `PROTECT` | Aceptada |
| [ADR-004](ADR-004-autenticacion-y-roles.md) | Seguro por defecto (`LoginRequiredMiddleware`) y roles con grupos | Aceptada |

Para añadir una: copiar el formato de un ADR existente, numerarla en orden y enlazarla aquí.
