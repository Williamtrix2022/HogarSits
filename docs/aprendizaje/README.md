# Notas de aprendizaje

Lo aprendido por tema, una entrada corta por sprint: **Claude Code (skills, subagentes)**, **orquestación (Docker Compose, GitHub Actions, flujo de PR)** y **AWS**. La tabla "Aprendizaje por sprint" de [`../sprints/SPRINTS.md`](../sprints/SPRINTS.md) dice qué estaba previsto aprender en cada uno; aquí queda lo que realmente pasó.

## Claude Code: skills y agentes
- **Skill propia** (`.claude/skills/sprint-update/SKILL.md`): frontmatter `name` + `description` e instrucciones en Markdown.
- **Skills de diseño** (`.agents/skills/ui-ux-pro-max`, `ui-animation`): se usan como **asesoras, no como órdenes**. Flujo que funcionó: generar el sistema de diseño con `search.py --design-system`, **verificar cada recomendación contra el producto** y descartar lo que choca (paleta y tipografía de otra marca, patrón de landing, scroll reveal), luego consultar guías puntuales (`--domain ux`).
- **`ui-animation`** obliga a decidir *si* animar antes de *cómo*: se anima poco, y lo de alta frecuencia no se anima. Esa pasada llevó a corregir el plano del login, que se repetía en cada visita.
- **Capturas para criticar el propio trabajo:** Edge headless (`--screenshot`) basta para ver pantallas reales, incluidos estados de error generados con el cliente de pruebas de Django.
- **Cuidado con las herramientas automáticas:** `ruff --fix` recorrió `.agents/` (código de terceros) y lo modificó. Ahora está excluido en `pyproject.toml`. Regla: **todo autocorrector necesita una lista explícita de qué toca**.

## Orquestación y calidad
- **Docker Compose:** `depends_on` con `condition: service_healthy` espera a Postgres. Un PostgreSQL nativo en el 5432 hizo que Django se conectara al servidor equivocado (error de autenticación); solución: publicar el contenedor en el **5433**. Diagnóstico: `Get-NetTCPConnection -LocalPort 5432 -State Listen`.
- **GitHub Actions:** `services:` levanta Postgres como contenedor del job; el CI corre `ruff`, `makemigrations --check` y `pytest`.
- **Flujo de PR con `main` protegida:** una rama por historia, `Closes #n`, CI verde, *squash merge*. Dos PR que tocan la misma tabla de `SPRINTS.md` chocan: resolver con `git merge origin/main` en la rama.
- **Mermaid:** `mermaid.parse` en Node (con `jsdom`) valida la sintaxis de los diagramas sin abrir un navegador; no sustituye ver el render.
- **Plantillas en caché:** con `runserver --noreload` Django no ve los cambios de plantillas; reiniciar el servidor.

## Django y datos
- `auto_now_add` ignora el valor asignado: para datos históricos o simulados, `default=timezone.now, editable=False`.
- `ExclusionConstraint` necesita `btree_gist` y solo existe en PostgreSQL.
- Un campo que no se muestra en el formulario (`activo` al crear) llega como «falso»: se elimina del formulario de alta.
- Validar el destino de un `next` con `url_has_allowed_host_and_scheme` evita redirecciones abiertas.
- Una rejilla `1fr` crece hasta el ancho mínimo de su contenido; en móvil, `minmax(0, 1fr)`.
- `LoginRequiredMiddleware` (Django 5.1+) invierte el riesgo: lo nuevo nace protegido.

## Probabilidad y método
- Con la matriz del README, **P(cierre desde Consulta) = 22,75 %** y **2,4 pasos** hasta absorción; el generador de datos los recupera en los tests.
- Con 3 entrevistas, los números orientan pero no generalizan: el modelo M/M/c acertó con una inmobiliaria y no con las otras dos (ver `diseno/DATOS_SIMULADOS.md` §5).

## AWS
- **Hecho:** cuenta con usuario IAM y MFA (Sprint 0).
- **Pendiente:** el **Budget con alerta a 1 USD (#14)**. Debe estar listo antes de crear cualquier recurso (fotos en S3 #27 y todo el Sprint 6).
- Para el despliegue: `btree_gist` en RDS, `@login_not_required` en la comprobación de salud, y servir los estáticos desde el mismo dominio (el sprite de iconos ya va en línea por esto).
