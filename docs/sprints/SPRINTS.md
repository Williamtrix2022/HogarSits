# HogarSits — Tablero de sprints

Sprints de 2 semanas. Metodología híbrida (ver Propuesta §10): alcance y modelos planificados desde el inicio, módulos entregados de forma incremental.
Seguimiento: este archivo + [Milestones e Issues en GitHub](https://github.com/Williamtrix2022/HogarSits/milestones). Se actualiza con la skill `/sprint-update`.

## Definition of Done
- Código en `main` vía PR con CI verde (`ruff`, `pytest`, `makemigrations --check`).
- Tests para la lógica nueva; matemática estocástica verificada contra los ejemplos de la Propuesta.
- Docs del sprint actualizados. Sin secretos en git.

## Sprints
| Sprint | Fechas | Fase | Objetivo | Estado | Progreso |
|---|---|---|---|---|---|
| [0](sprint-00.md) | 02-nov → 15-nov-2026 | — | Fundaciones: estructura, Docker, CI, sprints, AWS seguro | ✅ Cerrado | 7/7 (Budget AWS → S1) |
| [1](sprint-01.md) | 16-nov → 29-nov | F1 | Requerimientos, casos de uso, encuesta, backlog | 🚧 En curso | 6/7 |
| [2](sprint-02.md) | 30-nov → 13-dic | F2 | Diseño: ER, wireframes, ADRs, modelos, datos simulados | ✅ Cerrado | 5/5 |
| [3](sprint-03.md) | 14-dic → 27-dic | F3 | Gestión (Entrega 1): CRUD inmuebles y clientes/solicitudes, auth | 🚧 En curso | 7/8 |
| [4](sprint-04.md) | 28-dic → 10-ene | F3 | Gestión (Entrega 2): agenda sin cruces, seguimiento de etapas | ✅ Cerrado | 7/7 |
| 5 | 11-ene → 24-ene | F4 | Analítica (Entrega 3): Poisson, M/M/c, Markov, dashboard | 🚧 Siguiente | 0/7 |
| 6 | 25-ene → 07-feb | F5-F6 | Pruebas, despliegue AWS, informe y sustentación | ⏳ | 0/7 |

> Las fechas son una propuesta: ajústalas al calendario real de la asignatura.

## Estado al 8-nov-2026 (verificado el 17-nov-2026)

- **Sprint 0** cerrado. **Sprint 1** (requerimientos) casi completo: falta una tarea que depende de personas, no de código: la **segunda ronda de entrevistas (#55)**. El **Budget de AWS (#14)** se cerró el 17-nov-2026.
- **Sprint 2** (diseño) completo: el **ADR-002 de Markov (#20)** se aceptó el 23-nov-2026 y es revisable al completar #55.
- **Sprint 3** (gestión, entrega 1) casi completo (7/8): acceso con roles, plantilla base, inmuebles, clientes, solicitudes y la seguridad del login (#60, #61). Falta solo **#27, fotos en S3** (necesita bucket y credenciales de AWS).
- **Sprint 4** (gestión, entrega 2) **completo (7/7)**: agenda sin cruces (#30), inmuebles cerrados (#31), etapas con historial (#32), «a quién contactar hoy» (#33), recordatorio de visitas (#52), horarios de asesores con `c` efectivo (#53) y el subagente `tester` (#34). El `tester` destapó un hueco: **RN-33, el historial de etapas se puede editar y borrar**; está descrito en pruebas `xfail` y falta decidir el mecanismo antes del Sprint 5.
- **Pruebas:** 342 automáticas sobre PostgreSQL real; el CI de GitHub las corre en cada PR.
- Los arranques se **adelantaron** respecto a las fechas propuestas (el calendario real de la asignatura manda).

## Aprendizaje por sprint

*Lo previsto. Lo que realmente se aprendió está en [`../aprendizaje/README.md`](../aprendizaje/README.md).*
| Sprint | Skills / Claude Code | Orquestación | AWS |
|---|---|---|---|
| 0 | skill `/sprint-update` | Docker Compose, GitHub Actions | Cuenta, MFA, IAM, Budgets |
| 1 | skill de historias de usuario | Issues/Milestones/Projects | — |
| 3 | — | — | S3 (media) en dev |
| 4 | subagente `tester` | — | — |
| 5 | subagente `revisor-estocastico`, skill `/modelo-estocastico` | — | — |
| 6 | — | CD con GitHub Actions (OIDC) | ECR, App Runner/EC2, RDS |
