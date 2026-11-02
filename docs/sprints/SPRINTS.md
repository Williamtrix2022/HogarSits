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
| [0](sprint-00.md) | 02-nov → 15-nov-2026 | — | Fundaciones: estructura, Docker, CI, sprints, AWS seguro | ✅ Cerrado | 6/7 (+1 movida a S1) |
| [1](sprint-01.md) | 16-nov → 29-nov | F1 | Requerimientos, casos de uso, encuesta, backlog | 🚧 En curso | 0/5 |
| 2 | 30-nov → 13-dic | F2 | Diseño: ER, wireframes, ADRs, modelos, datos simulados | ⏳ | — |
| 3 | 14-dic → 27-dic | F3 | Gestión (Entrega 1): CRUD inmuebles y clientes/solicitudes, auth | ⏳ | — |
| 4 | 28-dic → 10-ene | F3 | Gestión (Entrega 2): agenda sin cruces, seguimiento de etapas | ⏳ | — |
| 5 | 11-ene → 24-ene | F4 | Analítica (Entrega 3): Poisson, M/M/c, Markov, dashboard | ⏳ | — |
| 6 | 25-ene → 07-feb | F5-F6 | Pruebas, despliegue AWS, informe y sustentación | ⏳ | — |

> Las fechas son una propuesta: ajústalas al calendario real de la asignatura.

## Aprendizaje por sprint
| Sprint | Skills / Claude Code | Orquestación | AWS |
|---|---|---|---|
| 0 | skill `/sprint-update` | Docker Compose, GitHub Actions | Cuenta, MFA, IAM, Budgets |
| 1 | skill de historias de usuario | Issues/Milestones/Projects | — |
| 3 | — | — | S3 (media) en dev |
| 4 | subagente `tester` | — | — |
| 5 | subagente `revisor-estocastico`, skill `/modelo-estocastico` | — | — |
| 6 | — | CD con GitHub Actions (OIDC) | ECR, App Runner/EC2, RDS |
