# HogarSits — guía para Claude Code

Sistema de gestión y análisis (Poisson, colas M/M/c, Markov) para inmobiliarias. Proyecto académico de Procesos Estocásticos (U. de Córdoba, 2026). Fuente de verdad del alcance: `README.md` y `docs/`.

## Comandos
- Entorno: `venv/Scripts/python.exe` (Windows) · deps en `requirements/{base,dev}.txt`
- BD local: `docker compose up -d db` · app: `python manage.py runserver` (settings `config.settings.dev`)
- Calidad: `ruff check .` · `pytest` · `python manage.py makemigrations --check --dry-run`

## Convenciones
- Apps en `apps/` (inmuebles, clientes, seguimiento, agenda, analitica). Config en `config/settings/{base,dev,prod}.py`.
- Matemática estocástica en `apps/analitica/services/` como funciones puras (sin imports de Django) con tests contra los ejemplos de la Propuesta (M/M/1 λ=2, μ=3; matriz P del README: P(cierre)≈22,8 %, pasos≈2,4).
- Secretos solo en `.env` (nunca en git). `DATABASE_URL` configura la BD.
- Commits convencionales (`feat:`, `fix:`, `docs:`, `chore:`, `test:`). Una rama por historia: `feature/<n>-descripcion`; PR con `Closes #n`; `main` solo por PR con CI verde.

## Sprints
Tablero maestro: `docs/sprints/SPRINTS.md`; detalle en `docs/sprints/sprint-XX.md`. Al cerrar trabajo, usar la skill `/sprint-update`. Decisiones de arquitectura en `docs/decisiones/ADR-XXX.md`.
