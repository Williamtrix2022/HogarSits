# Cobertura de las reglas de negocio (RN-01 a RN-33)

Qué prueba automática respalda cada regla de [`CASOS_DE_USO.md`](CASOS_DE_USO.md) §4. La mantiene el subagente [`tester`](../../.claude/agents/tester.md) y se revisa al cerrar cada sprint. Estado al **23-nov-2026** (342 pruebas contra PostgreSQL real).

Leyenda: ✅ cubierta · ⚠️ parcial o con una duda abierta · ❌ sin cubrir. «BD» = la restricción vive en PostgreSQL y se prueba disparándola.

## Agenda
| RN | Estado | Dónde se hace cumplir | Pruebas |
|---|---|---|---|
| RN-01 cruce del asesor | ✅ | BD (`ExclusionConstraint`) + servicio | `test_agenda::test_rechaza_cruce_del_mismo_asesor`, `test_visitas_contiguas_no_se_cruzan` · `test_agenda_pantallas::test_rechaza_cruce_de_asesor_e_indica_con_cual`, `test_visitas_contiguas_estan_permitidas` |
| RN-02 cruce del inmueble | ⚠️ | BD + servicio | `test_agenda::test_rechaza_cruce_del_mismo_inmueble` · `test_agenda_pantallas::test_rechaza_cruce_de_inmueble`. **Duda abierta:** las visitas grupales (varios clientes, mismo inmueble y hora) no están definidas |
| RN-03 inmueble cerrado | ✅ | servicio (`inmuebles/services`) | `test_inmuebles_cerrados::test_una_solicitud_rechaza_un_inmueble_cerrado` · `test_agenda_pantallas::test_no_se_agenda_un_inmueble_cerrado` |
| RN-04 canceladas liberan el horario | ✅ | BD (`condition`) | `test_agenda::test_visita_cancelada_libera_el_horario` · `test_agenda_pantallas::test_una_cancelada_libera_el_horario`, `test_reprogramar_cancela_la_original_y_enlaza_la_nueva` |
| RN-05 proponer el estado del inmueble al cerrar | ✅ | servicio + vista | `test_etapas::test_cierre_marcando_el_inmueble_lo_cierra_con_bitacora`, `test_cierre_sin_marcar_el_inmueble_solo_recuerda` |
| RN-06 futuro; realizada solo si ya empezó | ✅ | servicio | `test_agenda_pantallas::test_no_se_agenda_en_el_pasado`, `test_realizada_solo_si_ya_empezo` |

## Clientes y solicitudes
| RN | Estado | Dónde | Pruebas |
|---|---|---|---|
| RN-10 correo único | ✅ | BD + formulario | `test_integridad::test_correo_unico_sin_distinguir_mayusculas` · `test_clientes::test_correo_duplicado_se_rechaza_sin_distinguir_mayusculas`. El teléfono repetido solo **avisa** (`test_telefono_repetido_avisa_pero_guarda`); la regla pide revisarlo |
| RN-11 la llegada la fija el sistema | ✅ | modelo + formulario | `test_solicitudes::test_registrar_fija_la_llegada_automaticamente_y_queda_en_espera`, `test_el_formulario_ignora_una_llegada_enviada_a_mano` |
| RN-12 un único asesor responsable | ✅ | modelo (FK) + servicio | `test_solicitudes::test_no_se_puede_tomar_dos_veces`, `test_solo_el_responsable_finaliza` |
| RN-13 «sin seguimiento» tras N días | ✅ | servicio | `test_pendientes::test_se_marca_sin_seguimiento_solo_al_superar_n_dias` (borde exacto de N) y `test_n_es_configurable`. N = 3 provisional hasta E7 |

## Tiempos de atención
| RN | Estado | Dónde | Pruebas |
|---|---|---|---|
| RN-20 llegada ≤ inicio ≤ fin | ✅ | BD (`CheckConstraint`) + servicio | `test_integridad::test_inicio_no_puede_ser_anterior_a_la_llegada`, `test_fin_no_puede_ser_anterior_al_inicio` · `test_solicitudes::test_tomar_asigna_al_asesor_y_guarda_el_inicio` |
| RN-21 espera y servicio | ✅ | servicio | `test_solicitudes::test_ciclo_completo_calcula_espera_y_servicio` |
| RN-22 solo las finalizadas aportan a μ | ✅ | servicio | `test_solicitudes::test_cancelada_no_aporta_a_mu` |

## Etapas (Markov)
| RN | Estado | Dónde | Pruebas |
|---|---|---|---|
| RN-30 transiciones válidas | ✅ | servicio | `test_etapas::test_no_se_saltan_ni_se_retroceden_etapas`, `test_destinos_permitidos_siguen_la_tabla_rn30`, `test_avanzar_guarda_la_transicion_y_actualiza_la_etapa` |
| RN-31 Cierre y Abandono absorbentes | ✅ | BD + servicio | `test_etapas::test_cierre_y_abandono_son_absorbentes`, `test_la_bd_tambien_impide_salir_de_un_estado_final` · `test_integridad::test_no_se_sale_de_cierre_ni_abandono` |
| RN-32 nace en Consulta | ✅ | modelo (default) | `test_etapas::test_toda_solicitud_nace_en_consulta` |
| RN-33 historial con origen, destino, fecha; no se borra ni edita | ⚠️ | — | Guardar origen, destino, fecha y autor está probado (`test_avanzar_guarda_la_transicion_y_actualiza_la_etapa`). **La inmutabilidad NO se cumple:** `test_historial_inmutable` la describe con 4 pruebas `xfail(strict=True)` (editar destino, editar nota, borrar una fila, borrar en bloque) y 1 de control (`test_crear_nuevas_transiciones_sigue_permitido`) que pasa |

## Hallazgos abiertos
1. **RN-33, inmutabilidad (hallazgo del tester, 23-nov-2026; confirmado con pruebas).** `SeguimientoEtapa` se puede editar y borrar: el modelo no lo impide y el admin de Django lo muestra como inline editable (`apps/seguimiento/admin.py`). La regla dice que el historial no se borra ni edita, y la matriz de Markov se estima desde esa tabla. **Falta decidir el mecanismo.** Un `save`/`delete` sobrescrito en el modelo no cubre el borrado en bloque ni `queryset.update()`; un **trigger de PostgreSQL** cubre los tres caminos (es el camino coherente con ADR-003, que pone la integridad en la BD). Al implementarlo: quitar los `xfail`, poner el admin en solo lectura, y revisar `tests/test_pendientes.py::test_el_ultimo_movimiento_es_el_seguimiento_mas_reciente`, que usa `update()` para fabricar historial antiguo. El `CASCADE` desde `SolicitudAtencion` también borra historial: decidir si se protege.
2. **RN-02, visitas grupales:** decisión abierta de la ronda 2 (#55).
3. **RN-10, teléfono:** hoy solo avisa; la regla pide revisar si debe ser único.
4. **Nombre desfasado:** `test_integridad::test_autotransicion_permitida_hasta_decidir_adr_002` conserva «hasta decidir» aunque el ADR-002 ya se aceptó; renombrar.

## Cómo se usa
Para cubrir un hueco o una regla nueva: pedir al subagente `tester` la RN concreta («cubre RN-33») y revisar su informe. El tester escribe solo en `tests/` y en este archivo; si una prueba destapa un fallo, lo reporta y no toca el código de la aplicación.
