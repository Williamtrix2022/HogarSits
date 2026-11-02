# Sprint 0 — Fundaciones
**Fechas:** 02-nov-2026 → 15-nov-2026 · **Milestone:** Sprint 0 - Fundaciones

**Objetivo:** dejar un proyecto reproducible, con calidad automatizada y un sistema de sprints, listo para construir las fases.

## Historias comprometidas
- [x] Reestructurar proyecto Django (config/, apps/, settings por entorno) — [#1](https://github.com/Williamtrix2022/HogarSits/issues/1)
- [x] PostgreSQL + Docker Compose (migrate y tests OK contra Postgres 17 en el puerto 5433) — [#2](https://github.com/Williamtrix2022/HogarSits/issues/2)
- [x] CI con GitHub Actions (verde en el PR #12 con Postgres 17) — [#3](https://github.com/Williamtrix2022/HogarSits/issues/3)
- [x] CLAUDE.md, skill /sprint-update, plantillas — [#4](https://github.com/Williamtrix2022/HogarSits/issues/4)
- [x] Sistema de sprints en docs/ y ADR-001 — [#5](https://github.com/Williamtrix2022/HogarSits/issues/5)
- [ ] Cuenta AWS segura (MFA, IAM, Budgets) — [#6](https://github.com/Williamtrix2022/HogarSits/issues/6) *(manual, a cargo del usuario)*
- [ ] Branch protection de main — [#7](https://github.com/Williamtrix2022/HogarSits/issues/7)

## Log de avance
- 2026-11-01: estructura nueva (`config/`, `apps/`), modelos divididos por app, migraciones regeneradas, ruff y 2 tests verdes (verificado contra SQLite temporal). Milestones, labels e issues creados en GitHub.

## Review
_Pendiente al cierre del sprint._

## Retro
_Pendiente al cierre del sprint._

## Aprendizajes
- Las versiones deben fijarse tras instalar (`pip list`), no de memoria: varias que asumí no existían para Python 3.14.
- Docker: un PostgreSQL 16 nativo de Windows ocupaba el 5432 y Django se conectaba a ese en vez de al contenedor (error "autentificación falló"). Solución: publicar el contenedor en el puerto 5433 del host. Diagnóstico: `Get-NetTCPConnection -LocalPort 5432 -State Listen`.
