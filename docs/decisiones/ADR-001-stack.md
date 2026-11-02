# ADR-001 — Stack y estructura base

**Estado:** aceptada · **Fecha:** 2026-11-01

## Contexto
El proyecto empezó como un esqueleto Django con SQLite, sin tests ni entorno reproducible. Se busca una base escalable y que sirva para aprender orquestación y AWS.

## Decisión
- **Django 6.1 monolito modular** (`apps/`), settings por entorno (`config/settings/`), configuración por variables de entorno (django-environ).
- **PostgreSQL** (Docker Compose en local; RDS en AWS) en vez de SQLite: igual en dev y prod.
- **Servicios analíticos puros** en `apps/analitica/services/` (NumPy/SciPy), sin dependencias de Django → testeables contra los ejemplos de la Propuesta.
- **Calidad**: ruff + pytest + CI en GitHub Actions.
- **AWS (Free Tier)**: imagen Docker → ECR → App Runner/EC2, RDS PostgreSQL, S3 para fotos; despliegue desde Actions con OIDC (Sprint 6).

## Consecuencias
+ Entornos reproducibles, despliegue simple, matemática aislada y verificable.
− Más piezas que mantener (Docker, CI) que un proyecto académico mínimo; se compensa con el objetivo de aprendizaje.
− Se descartó un frontend separado (React) por alcance; se puede reconsiderar tras el Sprint 5.
