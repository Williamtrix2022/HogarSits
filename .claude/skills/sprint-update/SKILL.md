---
name: sprint-update
description: Actualiza el seguimiento del sprint de HogarSits (docs/sprints) con los issues cerrados del milestone y lo trabajado, y prepara el commit. Usar al terminar una historia o cerrar un sprint.
---

# sprint-update

1. Determina el sprint activo: la fila 🚧 en `docs/sprints/SPRINTS.md` (milestone `Sprint N`).
2. Lee el estado real en GitHub:
   - `gh issue list --milestone "Sprint N" --state all --json number,title,state,closedAt`
   - `git log --oneline` desde el inicio del sprint.
3. En `docs/sprints/sprint-0N.md`: marca `[x]` las historias cuyo issue esté cerrado, añade una línea fechada en "Log de avance" con lo hecho, y anota aprendizajes (skills, orquestación, AWS) si los hubo.
4. En `docs/sprints/SPRINTS.md`: actualiza la columna de progreso (cerrados/total) y el estado del sprint.
5. Si el sprint terminó (todo cerrado o fecha vencida): completa "Review" y "Retro", marca ✅ y deja el siguiente sprint en 🚧.
6. Muestra el diff al usuario y propone `git commit -m "docs(sprint): actualizar sprint N"`. No hagas push sin confirmación.

No inventes avances: solo registra lo verificable en issues, commits o archivos.
