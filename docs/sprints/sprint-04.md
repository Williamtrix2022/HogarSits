# Sprint 4 — Gestión, Entrega 2 (Fase 3)
**Fechas:** 28-dic-2026 → 10-ene-2027 (se adelantó el arranque el 23-nov) · **Milestone:** Sprint 4 - Gestion (Entrega 2)

**Objetivo:** segunda entrega de la gestión: agenda de visitas sin cruces, seguimiento de etapas con historial, alertas y disponibilidad de asesores.

## Historias comprometidas
- [x] Agenda de visitas sin cruces de asesor ni inmueble (26 tests) — [#30](https://github.com/Williamtrix2022/HogarSits/issues/30)
- [x] Bloquear o advertir inmuebles vendidos/arrendados (11 tests) — [#31](https://github.com/Williamtrix2022/HogarSits/issues/31)
- [x] Seguimiento de etapas con historial (42 tests) — [#32](https://github.com/Williamtrix2022/HogarSits/issues/32)
- [x] Alertas y recordatorios de seguimiento (24 tests, junto con #52) — [#33](https://github.com/Williamtrix2022/HogarSits/issues/33)
- [x] Subagente `tester` para reglas de negocio (`.claude/agents/tester.md` + `docs/requerimientos/COBERTURA_REGLAS.md`) — [#34](https://github.com/Williamtrix2022/HogarSits/issues/34)
- [x] Recordatorio de visitas próximas (panel «Mis visitas» del inicio) — [#52](https://github.com/Williamtrix2022/HogarSits/issues/52)
- [x] Horario semanal de asesores y disponibilidad por franja (33 tests) — [#53](https://github.com/Williamtrix2022/HogarSits/issues/53)

## Log de avance
- 2026-11-23: #31 — una solicitud rechaza inmuebles Vendidos, Arrendados o inactivos (RN-03) y el selector no los lista; al cerrar un inmueble con solicitudes abiertas se avisa (RF-15). La regla vive en `apps/inmuebles/services.py` y la reutiliza la agenda.
- 2026-11-23: #30 — agenda semanal con filtro por asesor; agendar, reprogramar, cancelar y marcar realizada. El cruce se detecta antes de guardar (nombra la visita en conflicto) y la restricción de la BD queda como red de seguridad. Reprogramar es atómico: si el nuevo horario choca, la visita original se conserva.
- 2026-11-23: #32 — detalle de solicitud (W9) con indicador de etapas, historial y visitas. Solo se permiten las transiciones de RN-30; Cierre y Abandono son absorbentes (RN-31). Seguir en la misma etapa se guarda como autotransición con nota (ADR-002) y se muestra «sin avance». Al cerrar se ofrece marcar el inmueble como Vendido/Arrendado con bitácora (RN-05, RF-43).
- 2026-11-23: #33 y #52 — la pantalla de inicio (W2) muestra «A quién contactar hoy» (pendientes por antigüedad, marcadas «Sin seguimiento» al superar N días; RN-13) y «Mis visitas» de hoy y mañana. N es configurable (`DIAS_SIN_SEGUIMIENTO`, por defecto 3, pendiente de E7). Un seguimiento sin avance también reinicia el conteo (ADR-002). El asesor ve lo suyo; el administrador, todo el equipo con filtro.
- 2026-11-23: #53 — administración de horarios semanales (turnos por asesor, varios días a la vez, sin cruces) y pantalla de asesores disponibles por franja de una hora. `disponibilidad.py` calcula el `c` efectivo = asesores con turno que cubre toda la franja − los que están en una visita (las realizadas también ocupan, para datos históricos). Solo administrador.
- 2026-11-23: #34 — subagente `tester` (`.claude/agents/tester.md`): escribe y ejecuta pruebas de RN-01 a RN-33, solo en `tests/` y en la matriz de cobertura, y reporta los fallos sin tocar `apps/`. Se armó `COBERTURA_REGLAS.md` (reglas → pruebas) y el primer encargo real confirmó un **hueco: RN-33, el historial de etapas se puede editar y borrar**. Quedó descrito en 5 pruebas (4 `xfail(strict=True)`) y pendiente de decidir el mecanismo (trigger de BD recomendado).

## Estado (23-nov-2026)
**7 de 7 hechos** (342 pruebas en total, 4 de ellas `xfail` a propósito: ver RN-33). Sprint completo. **Siguiente:** Sprint 5 (analítica), que consume `apps/agenda/disponibilidad.py` para el `c` efectivo y el historial de etapas para la matriz de Markov.

## Review / Retro
**Review:** 7 de 7 historias: agenda sin cruces, inmuebles cerrados, etapas con historial, «a quién contactar hoy», recordatorio de visitas, horarios con asesores disponibles y el subagente `tester`. La gestión (Entregas 1 y 2) está completa salvo las fotos en S3 (#27, Sprint 3).
**Retro:** *bien:* una regla por servicio, probada en el borde, y el `tester` destapó un hueco real al armar la matriz de cobertura; *mejorar:* la suite pasó de 4 a 14 minutos en una corrida (conviene `pytest -n` o separar lo lento) y el ADR-002 se aceptó sin datos de E3; *siguiente:* decidir la inmutabilidad del historial (RN-33) antes de estimar la matriz de Markov en el Sprint 5.

## Aprendizajes
- El `c` efectivo exige que el turno cubra **toda** la franja: una franja de una hora a medias dentro de un turno no cuenta, o se sobreestima la capacidad.
- Una prueba que describe una regla aún incumplida se deja `xfail(strict=True)`: el CI sigue verde y, al arreglarla, `strict` obliga a quitar la marca.
- Un umbral «más de N días» debe probarse en el borde (N exacto no cuenta); y el umbral va en configuración, no en el código, mientras la encuesta no lo confirme.
- Un filtro por asesor que llega por la URL debe ignorarse para quien no es administrador: se prueba forzando `?asesor=` con un asesor común.
- Reprogramar dentro de una transacción: la visita original se cancela primero, así no estorba al nuevo horario (correrla 15 minutos sobre sí misma es válido), y si algo falla se deshace todo.
- Un formulario enlazado no tiene `initial`: calcular valores derivados de la instancia, no de `self.initial`, o la vista revienta en el POST (lo destapó una prueba).
