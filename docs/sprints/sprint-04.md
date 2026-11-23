# Sprint 4 — Gestión, Entrega 2 (Fase 3)
**Fechas:** 28-dic-2026 → 10-ene-2027 (se adelantó el arranque el 23-nov) · **Milestone:** Sprint 4 - Gestion (Entrega 2)

**Objetivo:** segunda entrega de la gestión: agenda de visitas sin cruces, seguimiento de etapas con historial, alertas y disponibilidad de asesores.

## Historias comprometidas
- [x] Agenda de visitas sin cruces de asesor ni inmueble (26 tests) — [#30](https://github.com/Williamtrix2022/HogarSits/issues/30)
- [x] Bloquear o advertir inmuebles vendidos/arrendados (11 tests) — [#31](https://github.com/Williamtrix2022/HogarSits/issues/31)
- [x] Seguimiento de etapas con historial (42 tests) — [#32](https://github.com/Williamtrix2022/HogarSits/issues/32)
- [x] Alertas y recordatorios de seguimiento (24 tests, junto con #52) — [#33](https://github.com/Williamtrix2022/HogarSits/issues/33)
- [ ] Subagente `tester` para reglas de negocio — [#34](https://github.com/Williamtrix2022/HogarSits/issues/34)
- [x] Recordatorio de visitas próximas (panel «Mis visitas» del inicio) — [#52](https://github.com/Williamtrix2022/HogarSits/issues/52)
- [ ] Horario semanal de asesores y disponibilidad por franja — [#53](https://github.com/Williamtrix2022/HogarSits/issues/53)

## Log de avance
- 2026-11-23: #31 — una solicitud rechaza inmuebles Vendidos, Arrendados o inactivos (RN-03) y el selector no los lista; al cerrar un inmueble con solicitudes abiertas se avisa (RF-15). La regla vive en `apps/inmuebles/services.py` y la reutiliza la agenda.
- 2026-11-23: #30 — agenda semanal con filtro por asesor; agendar, reprogramar, cancelar y marcar realizada. El cruce se detecta antes de guardar (nombra la visita en conflicto) y la restricción de la BD queda como red de seguridad. Reprogramar es atómico: si el nuevo horario choca, la visita original se conserva.
- 2026-11-23: #32 — detalle de solicitud (W9) con indicador de etapas, historial y visitas. Solo se permiten las transiciones de RN-30; Cierre y Abandono son absorbentes (RN-31). Seguir en la misma etapa se guarda como autotransición con nota (ADR-002) y se muestra «sin avance». Al cerrar se ofrece marcar el inmueble como Vendido/Arrendado con bitácora (RN-05, RF-43).
- 2026-11-23: #33 y #52 — la pantalla de inicio (W2) muestra «A quién contactar hoy» (pendientes por antigüedad, marcadas «Sin seguimiento» al superar N días; RN-13) y «Mis visitas» de hoy y mañana. N es configurable (`DIAS_SIN_SEGUIMIENTO`, por defecto 3, pendiente de E7). Un seguimiento sin avance también reinicia el conteo (ADR-002). El asesor ve lo suyo; el administrador, todo el equipo con filtro.

## Estado (23-nov-2026)
5 de 7 hechos (304 tests en total). Faltan #53 (horario semanal de asesores y asesores disponibles por franja) y #34 (subagente `tester`).
**Siguiente recomendado:** #53, que alimenta el `c` efectivo del análisis de colas del Sprint 5.

## Review / Retro
_Se completan al cerrar el sprint._

## Aprendizajes
- Un umbral «más de N días» debe probarse en el borde (N exacto no cuenta); y el umbral va en configuración, no en el código, mientras la encuesta no lo confirme.
- Un filtro por asesor que llega por la URL debe ignorarse para quien no es administrador: se prueba forzando `?asesor=` con un asesor común.
- Reprogramar dentro de una transacción: la visita original se cancela primero, así no estorba al nuevo horario (correrla 15 minutos sobre sí misma es válido), y si algo falla se deshace todo.
- Un formulario enlazado no tiene `initial`: calcular valores derivados de la instancia, no de `self.initial`, o la vista revienta en el POST (lo destapó una prueba).
