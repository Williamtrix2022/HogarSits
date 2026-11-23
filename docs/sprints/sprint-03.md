# Sprint 3 — Gestión, Entrega 1 (Fase 3)
**Fechas:** 14-dic-2026 → 27-dic-2026 (se adelantó el arranque el 8-nov) · **Milestone:** Sprint 3 - Gestion (Entrega 1)

**Objetivo:** primera entrega de la gestión: acceso con roles, interfaz base con la marca, CRUD de inmuebles y clientes, y solicitudes con tiempos.

## Historias comprometidas
- [x] Autenticación y roles Admin/Asesor (`ADR-004`, 30 tests) — [#24](https://github.com/Williamtrix2022/HogarSits/issues/24)
- [x] Plantilla base de UI y navegación (`IDENTIDAD_VISUAL.md` §6, `MOVIMIENTO.md`) — [#25](https://github.com/Williamtrix2022/HogarSits/issues/25)
- [x] CRUD de inmuebles con estados y filtros (44 tests; historial de estado incluido) — [#26](https://github.com/Williamtrix2022/HogarSits/issues/26)
- [ ] Fotos de inmuebles con almacenamiento en S3 — [#27](https://github.com/Williamtrix2022/HogarSits/issues/27)
- [x] CRUD de clientes sin duplicados (17 tests) — [#28](https://github.com/Williamtrix2022/HogarSits/issues/28)
- [x] Solicitudes con tiempos de espera y servicio (24 tests) — [#29](https://github.com/Williamtrix2022/HogarSits/issues/29)
- [x] Protección contra fuerza bruta en el login (5 fallos = 15 min de bloqueo) — [#60](https://github.com/Williamtrix2022/HogarSits/issues/60)
- [x] Cambio de contraseña propio y restablecimiento — [#61](https://github.com/Williamtrix2022/HogarSits/issues/61)

## Log de avance
- 2026-11-08: #24 — app `cuentas`: login/logout, roles por grupos, `LoginRequiredMiddleware` (toda vista exige sesión), administración de usuarios (crear, editar, activar/desactivar) con salvaguardas, plantilla mínima con tokens de la marca. Verificado con 80 tests y contra un servidor real.
- 2026-11-08: #25 — plantilla base con la identidad visual (skills `ui-ux-pro-max` y `ui-animation`): barra superior, menú que muestra solo los destinos existentes, iconos Phosphor, componentes (aviso, estado vacío, tabla, formulario accesible), panel móvil, guía de componentes y plan de movimiento. El plano del login pasa a animarse solo la primera vez. Verificado con capturas y 107 tests.
- 2026-11-08: #26 — CRUD de inmuebles: lista con búsqueda y filtros (estado, operación, tipo, rango de precio, inactivos), paginación, alta, ficha con historial de estado (RF-12 adelantado), desactivar en lugar de borrar. «Inmuebles» apareció solo en el menú. Se creó `apps/comun` (campo de pesos, resumen de errores accesible). Se corrigió un desborde en móvil de la plantilla base (#25).

## Estado (23-nov-2026)
7 de 8 hechos (238 tests en total). Falta solo **#27, fotos en S3**: el Budget de AWS (#14) ya existe; falta crear el bucket y las credenciales.
- 2026-11-17: #14 (Sprint 1) — AWS Budget `hogarsits-cero-gasto` (1,00 US$) creado; se desbloquea #27.
- 2026-11-23: #60 — bloqueo temporal tras 5 fallos seguidos por usuario + IP durante 15 min (modelo `IntentoAcceso`, estado en BD para varios workers).
- 2026-11-23: #61 — cambio de contraseña propio (`/cuenta/clave/`) y restablecimiento por el administrador, que además levanta el bloqueo del usuario. La recuperación por correo sigue fuera de alcance.
- 2026-11-23: #28 — CRUD de clientes con búsqueda por nombre, correo o teléfono (ignora espacios y guiones). Correo único sin distinguir mayúsculas; teléfono repetido solo avisa (RN-10).
- 2026-11-23: #29 — cola de solicitudes con llegada automática (RN-11) y transiciones En espera → En atención → Finalizado / Cancelado en `services.py`, con bloqueo de fila. Tiempos de espera y servicio según RN-21; las canceladas no cuentan para μ (RN-22).

## Review / Retro
_Se completan al cerrar el sprint._

## Aprendizajes
- Una rejilla `1fr` crece hasta el ancho mínimo de su contenido (una tabla): en móvil se usa `minmax(0, 1fr)` para que la tabla se desplace dentro de su contenedor.
- Un campo del formulario que no se muestra (`activo` al crear) llega como «falso» y deja el registro inactivo: se elimina del formulario de alta.
- Validar el destino de un `next` con `url_has_allowed_host_and_scheme` evita redirecciones abiertas.
- `LoginRequiredMiddleware` (Django 5.1+) invierte el riesgo: lo nuevo nace protegido; lo público se marca con `@login_not_required`.
- Una `ExclusionConstraint` en la BD no basta para la UX: se detecta el cruce antes de guardar para nombrar la visita en conflicto, y la restricción queda como red de seguridad (ver sprint 4).
- Buscar un teléfono sin importar su formato exige comparar contra el teléfono sin separadores (`Replace` en la consulta), no con `icontains` sobre lo escrito.
- Un guard «no dejar el sistema sin administradores» es inalcanzable por HTTP (el actor siempre cuenta); se prueba a nivel de formulario.
