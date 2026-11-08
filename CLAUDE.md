# HogarSits — guía para Claude Code

Sistema de gestión y análisis (Poisson, colas M/M/c, Markov) para inmobiliarias. Proyecto académico de Procesos Estocásticos (U. de Córdoba, 2026). Fuente de verdad del alcance: `README.md` y `docs/`.

## Comandos
- Entorno: `venv/Scripts/python.exe` (Windows) · deps en `requirements/{base,dev}.txt`
- BD local: `docker compose up -d db` · app: `python manage.py runserver` (settings `config.settings.dev`)
- Calidad: `ruff check .` · `pytest` (requiere PostgreSQL en Docker) · `python manage.py makemigrations --check --dry-run`
- Datos de prueba: `python manage.py seed_datos_simulados` (ver `docs/diseno/DATOS_SIMULADOS.md`; `--limpiar` los borra)

## Convenciones
- Apps en `apps/` (cuentas, comun, inmuebles, clientes, seguimiento, agenda, analitica). `comun` guarda lo compartido (campo de pesos, mixin de formularios accesibles, filtros de formato). Config en `config/settings/{base,dev,prod}.py`.
- Matemática estocástica en `apps/analitica/services/` como funciones puras (sin imports de Django) con tests contra los ejemplos de la Propuesta (M/M/1 λ=2, μ=3; matriz P del README: P(cierre)≈22,8 %, pasos≈2,4).
- Seguridad: `LoginRequiredMiddleware` protege **toda** vista; lo público se marca con `@login_not_required`. Roles = grupos `Administrador`/`Asesor` (`apps/cuentas/roles.py`, ADR-004).
- UI: nuevas pantallas extienden `templates/base.html` (`titulo_pagina`, `acciones`, `contenido`) y usan `templates/componentes/`; el menú muestra solo los destinos de `apps/cuentas/navegacion.py` cuya URL existe. Catálogo en `/administracion/componentes/`. Reglas: `docs/diseno/IDENTIDAD_VISUAL.md` y `MOVIMIENTO.md`.
- `.agents/` son skills de terceros: **no** lintear ni autocorregir (excluido en `pyproject.toml`).
- Secretos solo en `.env` (nunca en git). `DATABASE_URL` configura la BD.
- Commits convencionales (`feat:`, `fix:`, `docs:`, `chore:`, `test:`). Una rama por historia: `feature/<n>-descripcion`; PR con `Closes #n`; `main` solo por PR con CI verde.

## Sprints
Tablero maestro: `docs/sprints/SPRINTS.md`; detalle en `docs/sprints/sprint-XX.md`. Al cerrar trabajo, usar la skill `/sprint-update`. Decisiones de arquitectura en `docs/decisiones/ADR-XXX.md`.
