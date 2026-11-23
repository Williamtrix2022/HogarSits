# Sprint 4 — Gestión, Entrega 2 (Fase 3)
**Fechas:** 28-dic-2026 → 10-ene-2027 (se adelantó el arranque el 23-nov) · **Milestone:** Sprint 4 - Gestion (Entrega 2)

**Objetivo:** segunda entrega de la gestión: agenda de visitas sin cruces, seguimiento de etapas con historial, alertas y disponibilidad de asesores.

## Historias comprometidas
- [x] Agenda de visitas sin cruces de asesor ni inmueble (26 tests) — [#30](https://github.com/Williamtrix2022/HogarSits/issues/30)
- [x] Bloquear o advertir inmuebles vendidos/arrendados (11 tests) — [#31](https://github.com/Williamtrix2022/HogarSits/issues/31)
- [ ] Seguimiento de etapas con historial — [#32](https://github.com/Williamtrix2022/HogarSits/issues/32)
- [ ] Alertas y recordatorios de seguimiento — [#33](https://github.com/Williamtrix2022/HogarSits/issues/33)
- [ ] Subagente `tester` para reglas de negocio — [#34](https://github.com/Williamtrix2022/HogarSits/issues/34)
- [ ] Recordatorio de visitas próximas — [#52](https://github.com/Williamtrix2022/HogarSits/issues/52)
- [ ] Horario semanal de asesores y disponibilidad por franja — [#53](https://github.com/Williamtrix2022/HogarSits/issues/53)

## Log de avance
- 2026-11-23: #31 — una solicitud rechaza inmuebles Vendidos, Arrendados o inactivos (RN-03) y el selector no los lista; al cerrar un inmueble con solicitudes abiertas se avisa (RF-15). La regla vive en `apps/inmuebles/services.py` y la reutiliza la agenda.
- 2026-11-23: #30 — agenda semanal con filtro por asesor; agendar, reprogramar, cancelar y marcar realizada. El cruce se detecta antes de guardar (nombra la visita en conflicto) y la restricción de la BD queda como red de seguridad. Reprogramar es atómico: si el nuevo horario choca, la visita original se conserva.

## Estado (23-nov-2026)
2 de 7 hechos. **Siguiente recomendado:** #32 (seguimiento de etapas con historial): hace falta para #33 y para la matriz de Markov del Sprint 5. Antes conviene cerrar #20 (ADR-002), porque decide cómo se registran las autotransiciones.

## Review / Retro
_Se completan al cerrar el sprint._

## Aprendizajes
- Reprogramar dentro de una transacción: la visita original se cancela primero, así no estorba al nuevo horario (correrla 15 minutos sobre sí misma es válido), y si algo falla se deshace todo.
- Un formulario enlazado no tiene `initial`: calcular valores derivados de la instancia, no de `self.initial`, o la vista revienta en el POST (lo destapó una prueba).
