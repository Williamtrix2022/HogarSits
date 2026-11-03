# HogarSits — Backlog de los Sprints 2 a 6

Generado en el Sprint 1 (issue #11) a partir de [`REQUERIMIENTOS.md`](../requerimientos/REQUERIMIENTOS.md) y [`CASOS_DE_USO.md`](../requerimientos/CASOS_DE_USO.md). Cada fila es un issue de GitHub en su milestone; el estado real está en GitHub y se resume en [`SPRINTS.md`](SPRINTS.md).

> El orden dentro de cada sprint es la prioridad propuesta. Se reajusta en cada planning según lo que revele la encuesta (#10) y el avance.

## Sprint 2 — Diseño (F2)

| Issue | Historia |
|---|---|
| [#19](https://github.com/Williamtrix2022/HogarSits/issues/19) | Diagrama Entidad-Relación (draw.io) |
| [#20](https://github.com/Williamtrix2022/HogarSits/issues/20) | ADR-002: cómo se modelan las autotransiciones de Markov |
| [#21](https://github.com/Williamtrix2022/HogarSits/issues/21) | Wireframes de las pantallas principales |
| [#22](https://github.com/Williamtrix2022/HogarSits/issues/22) | Refactor de modelos y migraciones |
| [#23](https://github.com/Williamtrix2022/HogarSits/issues/23) | Comando seed_datos_simulados (RF-60, HU-10) |

## Sprint 3 — Gestión, Entrega 1 (F3)

| Issue | Historia |
|---|---|
| [#24](https://github.com/Williamtrix2022/HogarSits/issues/24) | Autenticación y roles Admin/Asesor (HU-11) |
| [#25](https://github.com/Williamtrix2022/HogarSits/issues/25) | Plantilla base de UI y navegación |
| [#26](https://github.com/Williamtrix2022/HogarSits/issues/26) | CRUD de inmuebles con estados y filtros (HU-01) |
| [#27](https://github.com/Williamtrix2022/HogarSits/issues/27) | Fotos de inmuebles con almacenamiento en S3 (RF-13) |
| [#28](https://github.com/Williamtrix2022/HogarSits/issues/28) | CRUD de clientes sin duplicados (HU-03) |
| [#29](https://github.com/Williamtrix2022/HogarSits/issues/29) | Solicitudes de atención con tiempos de espera y servicio (HU-04) |

## Sprint 4 — Gestión, Entrega 2 (F3)

| Issue | Historia |
|---|---|
| [#30](https://github.com/Williamtrix2022/HogarSits/issues/30) | Agenda de visitas sin cruces de asesor ni inmueble (HU-05) |
| [#31](https://github.com/Williamtrix2022/HogarSits/issues/31) | Bloquear o advertir inmuebles vendidos/arrendados (HU-02) |
| [#32](https://github.com/Williamtrix2022/HogarSits/issues/32) | Seguimiento de etapas con historial (HU-06) |
| [#33](https://github.com/Williamtrix2022/HogarSits/issues/33) | Alerta de solicitudes sin seguimiento (RF-25) |
| [#34](https://github.com/Williamtrix2022/HogarSits/issues/34) | Subagente tester para reglas de negocio |

## Sprint 5 — Analítica, Entrega 3 (F4)

| Issue | Historia |
|---|---|
| [#35](https://github.com/Williamtrix2022/HogarSits/issues/35) | services/poisson.py: λ por franja y ajuste (HU-07) |
| [#36](https://github.com/Williamtrix2022/HogarSits/issues/36) | services/colas.py: M/M/1 y M/M/c (HU-08) |
| [#37](https://github.com/Williamtrix2022/HogarSits/issues/37) | services/markov.py: matriz P, N=(I−Q)⁻¹ y absorción (HU-09) |
| [#38](https://github.com/Williamtrix2022/HogarSits/issues/38) | Dashboard analítico con Chart.js (RF-56, RF-57) |
| [#39](https://github.com/Williamtrix2022/HogarSits/issues/39) | Subagente revisor-estocastico y skill /modelo-estocastico |
| [#40](https://github.com/Williamtrix2022/HogarSits/issues/40) | Exportar resultados a CSV (RF-58) |

## Sprint 6 — Pruebas, AWS y Entrega (F5–F6)

| Issue | Historia |
|---|---|
| [#41](https://github.com/Williamtrix2022/HogarSits/issues/41) | Validar modelos: parámetros estimados vs simulados (RF-61) |
| [#42](https://github.com/Williamtrix2022/HogarSits/issues/42) | Pruebas funcionales e informe de pruebas |
| [#43](https://github.com/Williamtrix2022/HogarSits/issues/43) | Manual de usuario e informe final |
| [#44](https://github.com/Williamtrix2022/HogarSits/issues/44) | Presentación y sustentación del proyecto |
| [#45](https://github.com/Williamtrix2022/HogarSits/issues/45) | Imagen Docker de producción y repositorio ECR |
| [#46](https://github.com/Williamtrix2022/HogarSits/issues/46) | Despliegue en AWS: App Runner o EC2 + RDS PostgreSQL + S3 |
| [#47](https://github.com/Williamtrix2022/HogarSits/issues/47) | CD con GitHub Actions usando OIDC hacia AWS |

## Dependencias importantes

- #20 (ADR autotransiciones) y #22 (modelos) condicionan el diseño de #32 (etapas) y #37 (Markov).
- #23 (datos simulados) es necesario para probar #35–#38 y #41 antes de tener datos reales.
- #14 (Budget de AWS) debe estar hecho antes de #27 y de todos los issues AWS del Sprint 6.
- #30 (agenda) y #31 (inmuebles cerrados) dependen de #26 (inmuebles) y #29 (solicitudes).
