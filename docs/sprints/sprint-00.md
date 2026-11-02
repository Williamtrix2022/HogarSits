# Sprint 0 — Fundaciones
**Estado:** ✅ Cerrado (01-nov-2026) · **Fechas:** 02-nov-2026 → 15-nov-2026 · **Milestone:** Sprint 0 - Fundaciones

**Objetivo:** dejar un proyecto reproducible, con calidad automatizada y un sistema de sprints, listo para construir las fases.

## Historias comprometidas
- [x] Reestructurar proyecto Django (config/, apps/, settings por entorno) — [#1](https://github.com/Williamtrix2022/HogarSits/issues/1)
- [x] PostgreSQL + Docker Compose (migrate y tests OK contra Postgres 17 en el puerto 5433) — [#2](https://github.com/Williamtrix2022/HogarSits/issues/2)
- [x] CI con GitHub Actions (verde en el PR #12 con Postgres 17) — [#3](https://github.com/Williamtrix2022/HogarSits/issues/3)
- [x] CLAUDE.md, skill /sprint-update, plantillas — [#4](https://github.com/Williamtrix2022/HogarSits/issues/4)
- [x] Sistema de sprints en docs/ y ADR-001 — [#5](https://github.com/Williamtrix2022/HogarSits/issues/5)
- [x] Cuenta AWS segura: usuario IAM y MFA hechos; el Budget pasó a [#14](https://github.com/Williamtrix2022/HogarSits/issues/14) (Sprint 1) — [#6](https://github.com/Williamtrix2022/HogarSits/issues/6)
- [x] Branch protection de main — [#7](https://github.com/Williamtrix2022/HogarSits/issues/7)

## Log de avance
- 2026-11-01: estructura nueva (`config/`, `apps/`), modelos divididos por app, migraciones regeneradas, ruff y 2 tests verdes (verificado contra SQLite temporal). Milestones, labels e issues creados en GitHub.

## Review
Entregado: proyecto Django reestructurado (`config/`, `apps/`), PostgreSQL 17 con Docker Compose, CI en GitHub Actions (verde), `main` protegida con PR + CI obligatorios, `CLAUDE.md`, skill `/sprint-update`, plantillas, sistema de sprints y ADR-001. Verificado: `migrate`, 2 tests y admin funcionando contra Postgres en Docker. Cuenta AWS con usuario IAM y MFA. 6 de 7 historias; el Budget de AWS pasa al Sprint 1 (#14).

## Retro
- Bien: PRs pequeños con CI verde; el diagnóstico del puerto 5432 fue rápido.
- Mejorar: probar Docker antes de dar la historia por lista; fijar versiones tras instalar, no de memoria; hacer el Budget de AWS antes que cualquier otra cosa de AWS.

## Aprendizajes
- Las versiones deben fijarse tras instalar (`pip list`), no de memoria: varias que asumí no existían para Python 3.14.
- Docker: un PostgreSQL 16 nativo de Windows ocupaba el 5432 y Django se conectaba a ese en vez de al contenedor (error "autentificación falló"). Solución: publicar el contenedor en el puerto 5433 del host. Diagnóstico: `Get-NetTCPConnection -LocalPort 5432 -State Listen`.
