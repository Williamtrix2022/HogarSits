# ADR-004 — Autenticación segura por defecto y roles con grupos

**Estado:** aceptada · **Fecha:** 2026-11-08 · **Issue:** #24 (HU-11, RF-01 a RF-03) · **Relacionadas:** ADR-003 (modelo de datos)

## Contexto
Hay dos roles (Administrador y Asesor) y datos personales de clientes (RNF-08). El equipo irá añadiendo pantallas en varios sprints: el riesgo real no es «no proteger la primera», sino **olvidar proteger la décima**.

## Decisión
1. **Seguro por defecto:** `LoginRequiredMiddleware` de Django exige sesión en **todas** las vistas. Solo están exentas las marcadas con `@login_not_required` (el inicio de sesión de Django y el login del admin de Django). Una vista nueva queda protegida sin hacer nada.
2. **Roles = grupos de Django** (`Administrador`, `Asesor`), creados por una migración de datos. Un usuario tiene **un solo rol** (`asignar_rol`). Un superusuario cuenta como administrador. Un usuario sin rol existe pero no pasa ninguna comprobación (p. ej. los asesores simulados).
3. **Permisos por rol** con `AdminRequeridoMixin` (403 con mensaje claro para un asesor; redirección al login para un anónimo). Las pantallas de administración viven bajo `/administracion/`.
4. **Los usuarios no se borran, se desactivan** (tienen solicitudes y visitas con `PROTECT`). Un usuario desactivado no puede entrar y recibe **el mismo mensaje** que una contraseña incorrecta (no se revela si la cuenta existe).
5. **Salvaguardas de administración:** nadie puede desactivarse a sí mismo ni quitarse el rol de administrador; el formulario además impide dejar el sistema sin administradores activos.
6. El cierre de sesión es solo por `POST` (protección CSRF).
7. `/admin/` de Django queda para superusuarios (mantenimiento técnico), no para el rol Administrador del negocio.

## Alternativas descartadas
- **`@login_required` en cada vista:** depende de la memoria de cada desarrollador.
- **Modelo de usuario propio con campo `rol`:** cambia `AUTH_USER_MODEL` (difícil de revertir tras la primera migración) sin necesidad actual; los grupos cubren dos roles y admiten permisos finos si hicieran falta.
- **`django-guardian`/permisos por objeto:** el asesor solo ve «lo suyo» por filtros de consulta (Sprint 3–4); no hay requisito de permisos por fila en la BD.

## Consecuencias
- (+) Toda pantalla futura exige sesión desde el primer día; los roles son inspeccionables en el admin de Django.
- (+) 30 tests cubren acceso anónimo, login/logout, permisos por rol, ciclo de vida de usuarios y las salvaguardas.
- (−) Una comprobación de rol por petición (consultas a grupos); irrelevante a esta escala, se puede cachear en la sesión.
- (−) Pendientes de seguridad abiertos: límite de intentos de login (#60) y cambio de contraseña (#61).
- (−) Las vistas que no deban pedir sesión (p. ej. comprobación de salud para AWS, Sprint 6) **deben** marcarse con `@login_not_required`.
