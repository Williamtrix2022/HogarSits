# Notas de aprendizaje

Lo aprendido por tema, una entrada corta por sprint: **Claude Code (skills, subagentes)**, **orquestación (Docker Compose, GitHub Actions, flujo de PR)** y **AWS**. La tabla "Aprendizaje por sprint" de [`../sprints/SPRINTS.md`](../sprints/SPRINTS.md) dice qué estaba previsto aprender en cada uno; aquí queda lo que realmente pasó.

## Claude Code: skills y agentes
- **Skill propia** (`.claude/skills/sprint-update/SKILL.md`): frontmatter `name` + `description` e instrucciones en Markdown.
- **Skills de diseño** (`.agents/skills/ui-ux-pro-max`, `ui-animation`): se usan como **asesoras, no como órdenes**. Flujo que funcionó: generar el sistema de diseño con `search.py --design-system`, **verificar cada recomendación contra el producto** y descartar lo que choca (paleta y tipografía de otra marca, patrón de landing, scroll reveal), luego consultar guías puntuales (`--domain ux`).
- **`ui-animation`** obliga a decidir *si* animar antes de *cómo*: se anima poco, y lo de alta frecuencia no se anima. Esa pasada llevó a corregir el plano del login, que se repetía en cada visita.
- **Capturas para criticar el propio trabajo:** Edge headless (`--screenshot`) basta para ver pantallas reales, incluidos estados de error generados con el cliente de pruebas de Django.
- **Subagente propio** (`.claude/agents/tester.md`, #34): frontmatter `name`, `description`, `tools` y `model`, y el cuerpo es el *prompt de sistema*. Lo que decidió si sirve:
  - **`description` es el disparador:** dice *cuándo* usarlo («cuando se cree o cambie una regla»), no solo qué hace.
  - **Herramientas mínimas y límites escritos:** puede escribir solo en `tests/` y en la matriz de cobertura, y **no toca `apps/`**. Si una prueba destapa un fallo, lo reporta; arreglarlo es decisión del desarrollador. Es la misma regla de «todo autocorrector necesita una lista explícita de qué toca».
  - **Una matriz como memoria** (`docs/requerimientos/COBERTURA_REGLAS.md`): el agente empieza por las filas ❌ y ⚠️ en lugar de redescubrir qué falta. Al armarla se encontró un hueco real (RN-33: el historial de etapas se podía editar y borrar).
  - **Disponibilidad:** el tipo `tester` apareció en la misma sesión, unos minutos después de crear el archivo (no hizo falta reiniciar); justo después de crearlo aún no estaba, así que una primera prueba se hizo pidiéndole a un agente genérico que leyera el archivo y siguiera sus instrucciones.
  - **Validar con un caso real:** esa corrida confirmó el hueco de RN-33 con 4 pruebas que fallan. Las instrucciones bastaron; solo faltó decir qué excepción esperar cuando el rechazo aún no está definido.
  - **Un hallazgo no debe romper el CI:** las pruebas que describen una regla aún sin cumplir se dejan `xfail(strict=True)`: el CI sigue verde y, al arreglar la regla, `strict` obliga a quitar la marca.
  - Un subagente es **un contexto aparte**: sirve para tareas acotadas que dejan un informe, no para decisiones que necesitan la conversación completa.
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
- **Una restricción de BD no basta para la experiencia:** se detecta el cruce de visitas antes de guardar para nombrar la visita en conflicto, y la restricción queda como red de seguridad ante dos asesores guardando a la vez.
- **Reprogramar es atómico:** se cancela la original y se crea la nueva en una transacción; si el nuevo horario choca, la excepción deshace todo y la original no se pierde.
- Un formulario enlazado (POST) no trae `initial`: lo derivado de la instancia se calcula desde la instancia (lo destapó una prueba).
- En es-CO los decimales se muestran con coma (`4,0`): las pruebas de pantalla deben comprobar la celda exacta, no un fragmento que pueda coincidir por casualidad.

## Probabilidad y método
- Con la matriz del README, **P(cierre desde Consulta) = 22,75 %** y **2,4 pasos** hasta absorción; el generador de datos los recupera en los tests.
- Con 3 entrevistas, los números orientan pero no generalizan: el modelo M/M/c acertó con una inmobiliaria y no con las otras dos (ver `diseno/DATOS_SIMULADOS.md` §5).

## AWS
- **Hecho:** cuenta con usuario IAM y MFA (Sprint 0), y el **Budget** `hogarsits-cero-gasto` (1 USD, #14, 17-nov-2026).
- **Aprendido con el Budget:** desde el 30-sep-2026 AWS exige **verificar el correo** de cada destinatario (lo avisa un banner en la pantalla de Presupuestos); sin verificar, las alertas no llegan.
- **Pendiente:** crear el bucket de fotos (#27) y todo el Sprint 6.
- Para el despliegue: `btree_gist` en RDS, `@login_not_required` en la comprobación de salud, y servir los estáticos desde el mismo dominio (el sprite de iconos ya va en línea por esto).
