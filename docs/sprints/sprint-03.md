# Sprint 3 — Gestión, Entrega 1 (Fase 3)
**Fechas:** 14-dic-2026 → 27-dic-2026 (se adelantó el arranque el 8-nov) · **Milestone:** Sprint 3 - Gestion (Entrega 1)

**Objetivo:** primera entrega de la gestión: acceso con roles, interfaz base con la marca, CRUD de inmuebles y clientes, y solicitudes con tiempos.

## Historias comprometidas
- [x] Autenticación y roles Admin/Asesor (`ADR-004`, 30 tests) — [#24](https://github.com/Williamtrix2022/HogarSits/issues/24)
- [x] Plantilla base de UI y navegación (`IDENTIDAD_VISUAL.md` §6, `MOVIMIENTO.md`) — [#25](https://github.com/Williamtrix2022/HogarSits/issues/25)
- [ ] CRUD de inmuebles con estados y filtros — [#26](https://github.com/Williamtrix2022/HogarSits/issues/26)
- [ ] Fotos de inmuebles con almacenamiento en S3 — [#27](https://github.com/Williamtrix2022/HogarSits/issues/27)
- [ ] CRUD de clientes sin duplicados — [#28](https://github.com/Williamtrix2022/HogarSits/issues/28)
- [ ] Solicitudes con tiempos de espera y servicio — [#29](https://github.com/Williamtrix2022/HogarSits/issues/29)
- [ ] Protección contra fuerza bruta en el login — [#60](https://github.com/Williamtrix2022/HogarSits/issues/60)
- [ ] Cambio de contraseña propio y restablecimiento — [#61](https://github.com/Williamtrix2022/HogarSits/issues/61)

## Log de avance
- 2026-11-08: #24 — app `cuentas`: login/logout, roles por grupos, `LoginRequiredMiddleware` (toda vista exige sesión), administración de usuarios (crear, editar, activar/desactivar) con salvaguardas, plantilla mínima con tokens de la marca. Verificado con 80 tests y contra un servidor real.
- 2026-11-08: #25 — plantilla base con la identidad visual (skills `ui-ux-pro-max` y `ui-animation`): barra superior, menú que muestra solo los destinos existentes, iconos Phosphor, componentes (aviso, estado vacío, tabla, formulario accesible), panel móvil, guía de componentes y plan de movimiento. El plano del login pasa a animarse solo la primera vez. Verificado con capturas y 107 tests.

## Review / Retro
_Pendiente._

## Aprendizajes
- `LoginRequiredMiddleware` (Django 5.1+) invierte el riesgo: lo nuevo nace protegido; lo público se marca con `@login_not_required`.
- Un guard «no dejar el sistema sin administradores» es inalcanzable por HTTP (el actor siempre cuenta); se prueba a nivel de formulario.
