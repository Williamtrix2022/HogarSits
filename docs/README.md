# Documentación de HogarSits

Índice de todo lo que hay en `docs/`. **Última actualización: 24-nov-2026** (Sprint 6 en curso).

## Para empezar
| Qué | Dónde |
|---|---|
| **Sustentación corta** (una página: lista previa, demo en orden, cifras y preguntas) | [`presentacion/SUSTENTACION_CORTA.md`](presentacion/SUSTENTACION_CORTA.md) |
| Guion de sustentación completo | [`presentacion/GUION_SUSTENTACION.md`](presentacion/GUION_SUSTENTACION.md) |
| **Manual de usuario** (asesores y administradores, con capturas) | [`manual/MANUAL_DE_USUARIO.md`](manual/MANUAL_DE_USUARIO.md) |
| **Informe final** | [`informe/INFORME_FINAL.md`](informe/INFORME_FINAL.md) |
| Sitio de presentación | [williamtrix2022.github.io/HogarSits](https://williamtrix2022.github.io/HogarSits/) (código en `../site/`) |
| Sistema en vivo (demostración, datos simulados) | [hogarsits.onrender.com](https://hogarsits.onrender.com/) |
| Qué es el proyecto, fases y cómo correrlo | [`../README.md`](../README.md) |
| Estado de los sprints (tablero maestro) | [`sprints/SPRINTS.md`](sprints/SPRINTS.md) |
| Convenciones para trabajar con Claude Code | [`../CLAUDE.md`](../CLAUDE.md) |

## Origen del proyecto
| Documento | Contenido |
|---|---|
| `HogarSits_Propuesta_Proyecto.docx` | Propuesta académica: objetivos, modelos estocásticos, fases, metodología |
| `HogarSits_Estudio_de_Mercado.md` | Mercado, competencia, propuesta de valor |
| `IDENTIDAD VISUAL/` | Hoja de marca y logo horizontal |

## Fase 1: requerimientos e investigación
| Documento | Contenido |
|---|---|
| [`requerimientos/REQUERIMIENTOS.md`](requerimientos/REQUERIMIENTOS.md) | RF/RNF con prioridad, historias de usuario, **estado de implementación** (v0.2) |
| [`requerimientos/CASOS_DE_USO.md`](requerimientos/CASOS_DE_USO.md) | Casos de uso, máquinas de estado, reglas de negocio |
| [`investigacion/ENCUESTA_INMOBILIARIAS.md`](investigacion/ENCUESTA_INMOBILIARIAS.md) | Instrumento de validación con inmobiliarias |
| [`investigacion/resultados/RESULTADOS_ENCUESTA.md`](investigacion/resultados/RESULTADOS_ENCUESTA.md) | Resultados agregados y anónimos de la ronda 1 (n = 3) |

> Los datos crudos de las encuestas (`docs/*.csv`) **no se versionan**: el repositorio es público.

## Despliegue en AWS (Sprint 6)
| Documento | Contenido |
|---|---|
| [`aws/DESPLIEGUE_RENDER.md`](aws/DESPLIEGUE_RENDER.md) | Demostración en Render: qué se despliega, contraseñas, qué esperar de la capa gratuita y limitaciones |
| [`aws/FOTOS_S3.md`](aws/FOTOS_S3.md) | Bucket privado, usuario IAM de mínimo privilegio y verificación de las fotos |
| [`aws/IMAGEN_DOCKER.md`](aws/IMAGEN_DOCKER.md) | Imagen de producción: qué hace, cómo probarla, qué se verificó y cómo subirla a ECR |

## Pruebas (Sprint 6)
| Documento | Contenido |
|---|---|
| [`pruebas/PLAN_DE_PRUEBAS.md`](pruebas/PLAN_DE_PRUEBAS.md) | Estrategia, trazabilidad de los 31 criterios de aceptación y de los RNF a pruebas que existen |
| [`pruebas/INFORME_DE_PRUEBAS.md`](pruebas/INFORME_DE_PRUEBAS.md) | Resultados medidos: 700 pruebas, cobertura 98,2 %, rendimiento con 10 000 solicitudes, defectos y qué no se probó |

## Fase 2: diseño
| Documento | Contenido |
|---|---|
| [`diseno/ER.md`](diseno/ER.md) | Diagrama entidad-relación y decisiones de datos |
| [`diseno/DATOS_SIMULADOS.md`](diseno/DATOS_SIMULADOS.md) | Generador de datos de prueba y sus límites |
| [`diseno/VALIDACION_MODELOS.md`](diseno/VALIDACION_MODELOS.md) | Parámetros estimados frente a simulados: error medido y límites (incluye el límite del modelo de esperas) |
| [`diseno/WIREFRAMES.md`](diseno/WIREFRAMES.md) | Mapa del sitio, flujos y 14 pantallas |
| [`diseno/IDENTIDAD_VISUAL.md`](diseno/IDENTIDAD_VISUAL.md) | Paleta, tipografía, componentes, accesibilidad |
| [`diseno/MOVIMIENTO.md`](diseno/MOVIMIENTO.md) | Plan de movimiento (qué se anima y qué no) |

## Decisiones de arquitectura
Ver [`decisiones/README.md`](decisiones/README.md).

## Seguimiento y aprendizaje
| Documento | Contenido |
|---|---|
| [`sprints/SPRINTS.md`](sprints/SPRINTS.md) | Tablero, Definition of Done, aprendizaje por sprint |
| [`sprints/BACKLOG.md`](sprints/BACKLOG.md) | Backlog de los sprints 2 a 6 con estado real |
| `sprints/sprint-00.md` a `sprint-03.md` | Planning, log, review y retro de cada sprint |
| [`aprendizaje/README.md`](aprendizaje/README.md) | Lo aprendido: skills, orquestación, AWS |
