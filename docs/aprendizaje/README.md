# Notas de aprendizaje

Registro de lo aprendido por tema (una entrada corta por sprint): **Claude Code (skills, subagentes)**, **orquestación (Docker Compose, GitHub Actions)** y **AWS**. Ver la tabla "Aprendizaje por sprint" en `../sprints/SPRINTS.md`.

## Sprint 0
- Skill propia: `.claude/skills/sprint-update/SKILL.md` (frontmatter `name` + `description`, instrucciones en Markdown).
- Docker Compose: `depends_on` con `condition: service_healthy` para esperar a Postgres.
- GitHub Actions: `services:` levanta Postgres como contenedor del job.
