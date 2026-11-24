# HogarSits — Plan de pruebas

**Versión:** 1.0 · **Fecha:** 2026-11-23 · **Sprint:** 6 · **Issue:** #42 · **Informe de resultados:** [`INFORME_DE_PRUEBAS.md`](INFORME_DE_PRUEBAS.md)

## 1. Alcance y estrategia
Se prueba **cada criterio de aceptación** de las 13 historias de usuario y los requisitos no funcionales que se pueden comprobar con una máquina. Las pruebas corren contra **PostgreSQL real** (no contra mocks), porque las restricciones de la base de datos son parte de las reglas (`ExclusionConstraint` para los cruces, `CHECK` para tiempos y etapas, correo único).

| Nivel | Qué comprueba | Dónde |
|---|---|---|
| **Matemática pura** | Fórmulas contra los ejemplos de la Propuesta, contra un cálculo independiente y recuperando los parámetros de una simulación | `test_poisson`, `test_colas`, `test_markov`, `test_simulacion`, `test_validacion` |
| **Integridad en la BD** | Que la base rechace lo inválido aunque la interfaz fallara | `test_integridad`, `test_agenda` |
| **Servicios y reglas de negocio** | Cada regla RN-01 a RN-33 ([`COBERTURA_REGLAS.md`](../requerimientos/COBERTURA_REGLAS.md)) | `test_solicitudes`, `test_etapas`, `test_pendientes`, `test_horarios`, `test_indicadores`… |
| **Pantallas** | Formularios, listas, filtros, permisos por rol, mensajes de error | `test_inmuebles`, `test_clientes`, `test_agenda_pantallas`, `test_analisis`, `test_exportar`… |
| **Funcional de punta a punta** | Una jornada completa por HTTP: de crear al asesor a cerrar un negocio y ver indicadores | `test_funcional_flujo` |
| **No funcionales** | Seguridad por configuración, zona horaria, idioma, requisitos de rendimiento | `test_aceptacion_y_rnf`, `test_rendimiento` |

**Principios:** una prueba que falla describe un defecto *o* una expectativa errónea, y se averigua cuál antes de tocar nada; una prueba debe poder fallar (se comprueba rompiendo la regla a propósito); las cifras se calculan a mano antes de escribir el `assert`.

## 2. Trazabilidad: historia → criterio → pruebas
31 criterios de aceptación, todos con al menos una prueba automática. Se **verifica** que cada prueba citada exista.

| Historia | Título | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **HU-01** | Gestionar inmuebles | CA1 · crear un inmueble con tipo, operación, dirección, precio, área y habitaciones | `test_inmuebles::test_crear_inmueble_valido_con_precio_y_area_en_formato_colombiano`<br>`test_inmuebles::test_datos_invalidos_no_crean_nada_y_dicen_como_corregir` |
|  |  | CA2 · filtrar por estado, operación y rango de precio | `test_inmuebles::test_filtrar_por_estado_operacion_y_tipo`<br>`test_inmuebles::test_filtrar_por_rango_de_precio_acepta_puntos`<br>`test_inmuebles::test_los_filtros_se_combinan` |
|  |  | CA3 · el estado solo toma Disponible, Reservado, Vendido o Arrendado | `test_aceptacion_y_rnf::test_un_estado_inventado_no_se_acepta`<br>`test_aceptacion_y_rnf::test_el_modelo_define_exactamente_cuatro_estados`<br>`test_integridad::test_alquiler_no_puede_quedar_vendido` |
| **HU-02** | Evitar ofrecer inmuebles cerrados | CA1 · no se agenda una visita en un inmueble Vendido o Arrendado | `test_agenda_pantallas::test_no_se_agenda_un_inmueble_cerrado`<br>`test_inmuebles_cerrados::test_una_solicitud_rechaza_un_inmueble_cerrado` |
|  |  | CA2 · al marcar un Cierre, el sistema propone actualizar el inmueble | `test_etapas::test_cierre_marcando_el_inmueble_lo_cierra_con_bitacora`<br>`test_etapas::test_cierre_sin_marcar_el_inmueble_solo_recuerda` |
| **HU-03** | Registrar clientes sin duplicados | CA1 · un correo existente muestra al cliente y no crea otro | `test_clientes::test_correo_duplicado_se_rechaza_sin_distinguir_mayusculas`<br>`test_integridad::test_correo_unico_sin_distinguir_mayusculas` |
|  |  | CA2 · nombre, correo y teléfono obligatorios y validados | `test_clientes::test_campos_obligatorios`<br>`test_clientes::test_telefono_invalido` |
| **HU-04** | Registrar solicitudes con hora de llegada | CA1 · la llegada se guarda automáticamente | `test_solicitudes::test_registrar_fija_la_llegada_automaticamente_y_queda_en_espera`<br>`test_solicitudes::test_el_formulario_ignora_una_llegada_enviada_a_mano` |
|  |  | CA2 · al iniciar y finalizar se registran las horas | `test_solicitudes::test_tomar_asigna_al_asesor_y_guarda_el_inicio`<br>`test_solicitudes::test_finalizar_guarda_el_fin_despues_del_inicio` |
|  |  | CA3 · el fin no puede ser anterior al inicio | `test_integridad::test_fin_no_puede_ser_anterior_al_inicio`<br>`test_integridad::test_inicio_no_puede_ser_anterior_a_la_llegada` |
| **HU-05** | Agendar visitas sin cruces | CA1 · sin cruce del mismo asesor | `test_agenda_pantallas::test_rechaza_cruce_de_asesor_e_indica_con_cual`<br>`test_agenda::test_rechaza_cruce_del_mismo_asesor` |
|  |  | CA2 · sin cruce del mismo inmueble | `test_agenda_pantallas::test_rechaza_cruce_de_inmueble`<br>`test_agenda::test_rechaza_cruce_del_mismo_inmueble` |
|  |  | CA3 · reprogramar y cancelar; lo cancelado no bloquea | `test_agenda_pantallas::test_una_cancelada_libera_el_horario`<br>`test_agenda_pantallas::test_reprogramar_cancela_la_original_y_enlaza_la_nueva`<br>`test_agenda_pantallas::test_reprogramar_con_conflicto_conserva_la_original` |
| **HU-06** | Seguir la etapa del cliente | CA1 · cada cambio queda con fecha y hora, y se ve el historial | `test_etapas::test_avanzar_guarda_la_transicion_y_actualiza_la_etapa`<br>`test_etapas::test_registrar_desde_la_pantalla_y_ver_el_historial` |
|  |  | CA2 · Cierre y Abandono no admiten más cambios | `test_etapas::test_cierre_y_abandono_son_absorbentes`<br>`test_etapas::test_la_bd_tambien_impide_salir_de_un_estado_final` |
| **HU-07** | Ver demanda por franja horaria | CA1 · λ estimado por franja | `test_poisson::test_recupera_lambda_por_hora_y_los_picos`<br>`test_analisis::test_la_pantalla_muestra_las_tres_secciones_con_frases_de_negocio` |
|  |  | CA2 · Poisson ajustado junto a la frecuencia observada | `test_poisson::test_una_franja_con_llegadas_de_poisson_no_se_rechaza`<br>`test_analisis::test_las_graficas_tienen_la_forma_que_espera_el_javascript` |
| **HU-08** | Dimensionar asesores | CA1 · ρ, L, Lq, W y Wq con λ, μ y c | `test_colas::test_mm1_ejemplo_de_la_propuesta`<br>`test_colas::test_dos_asesores_esperan_unos_29_minutos`<br>`test_colas::test_lq_coincide_con_la_cadena_de_nacimiento_y_muerte` |
|  |  | CA2 · si ρ ≥ 1, advertencia de inestabilidad | `test_colas::test_con_rho_mayor_o_igual_a_uno_no_se_inventan_cifras`<br>`test_analisis::test_frase_de_inestabilidad_no_da_cifras` |
|  |  | CA3 · se sugiere el menor c que cumple el umbral | `test_colas::test_recomienda_tres_asesores_para_esperar_menos_de_20_minutos`<br>`test_analisis::test_un_umbral_mas_estricto_pide_mas_asesores` |
| **HU-09** | Conocer la probabilidad de cierre | CA1 · matriz P estimada con los datos registrados | `test_markov::test_estima_frecuencias_relativas`<br>`test_markov::test_recupera_la_matriz_de_la_simulacion`<br>`test_analisis::test_el_detalle_tecnico_trae_las_tablas_equivalentes` |
|  |  | CA2 · P(cierre), P(abandono) y pasos desde cada etapa | `test_markov::test_probabilidad_de_cierre_y_pasos_de_la_propuesta`<br>`test_markov::test_probabilidades_de_las_otras_etapas_del_wireframe_w12`<br>`test_markov::test_coincide_con_la_potencia_de_la_matriz` |
| **HU-10** | Probar con datos simulados | CA1 · un comando genera datos con λ, μ y P configurables | `test_seed_comando::test_genera_datos_coherentes`<br>`test_simulacion::test_recupera_lambda_diario`<br>`test_simulacion::test_recupera_la_probabilidad_de_cierre_de_la_propuesta` |
|  |  | CA2 · el informe compara parámetros reales y estimados | `test_validacion::test_recupera_lambda_mu_y_pasos_con_error_pequeno`<br>`test_validacion::test_el_comando_escribe_el_informe_en_utf8` |
| **HU-11** | Controlar accesos | CA1 · un asesor no administra usuarios | `test_cuentas::test_asesor_no_administra_usuarios`<br>`test_funcional_flujo::test_jornada_completa_de_una_inmobiliaria` |
|  |  | CA2 · sin iniciar sesión no se accede a ninguna pantalla | `test_cuentas::test_anonimo_es_enviado_al_login`<br>`test_funcional_flujo::test_ninguna_pantalla_es_publica_salvo_el_acceso` |
| **HU-12** | No perder solicitudes ni visitas | CA1 · lista de pendientes, la más antigua primero | `test_pendientes::test_se_ordenan_por_antiguedad_la_mas_olvidada_primero`<br>`test_pendientes::test_el_inicio_lista_lo_pendiente_del_asesor_con_la_marca` |
|  |  | CA2 · las de más de N días sin movimiento, marcadas | `test_pendientes::test_se_marca_sin_seguimiento_solo_al_superar_n_dias`<br>`test_pendientes::test_n_es_configurable` |
|  |  | CA3 · mis visitas de hoy y mañana | `test_pendientes::test_visitas_de_hoy_y_manana_solamente`<br>`test_pendientes::test_el_inicio_muestra_mis_visitas` |
| **HU-13** | Evaluar el desempeño del equipo | CA1 · atendidas, visitas, cierres y atención media por asesor y rango | `test_indicadores::test_cuenta_atendidas_visitas_cierres_y_media`<br>`test_indicadores::test_lo_de_fuera_del_periodo_no_entra` |
|  |  | CA2 · un asesor solo ve sus propios indicadores | `test_indicadores::test_un_asesor_ve_solo_su_fila`<br>`test_indicadores::test_un_asesor_no_puede_ver_a_otro_cambiando_la_url` |

## 3. Requisitos no funcionales
| RNF | Tema | Pruebas |
|---|---|---|
| RNF-01 | Corrección matemática | `test_colas::test_mm1_ejemplo_de_la_propuesta`<br>`test_markov::test_probabilidad_de_cierre_y_pasos_de_la_propuesta`<br>`test_validacion::test_recupera_lambda_mu_y_pasos_con_error_pequeno` |
| RNF-02 | Calidad | `test_aceptacion_y_rnf::test_ningun_servicio_estocastico_importa_django` |
| RNF-03 | Integridad de datos | `test_agenda::test_rechaza_cruce_del_mismo_asesor`<br>`test_integridad::test_correo_unico_sin_distinguir_mayusculas` |
| RNF-04 | Seguridad | `test_aceptacion_y_rnf::test_las_contrasenas_se_guardan_con_hash`<br>`test_aceptacion_y_rnf::test_la_produccion_exige_https_y_cookies_seguras`<br>`test_aceptacion_y_rnf::test_el_gitignore_protege_los_secretos_y_los_datos_de_encuestas`<br>`test_cuentas::test_login_incorrecto_muestra_mensaje_sin_revelar_cual_dato_falla` |
| RNF-05 | Usabilidad | `test_aceptacion_y_rnf::test_la_interfaz_esta_en_espanol_de_colombia`<br>`test_navegacion::test_los_errores_de_formulario_se_enlazan_con_su_campo` |
| RNF-06 | Rendimiento | `test_rendimiento::test_cada_pantalla_responde_en_menos_de_3_segundos` |
| RNF-07 | Zona horaria | `test_aceptacion_y_rnf::test_la_zona_horaria_es_bogota_y_los_datos_se_guardan_en_utc`<br>`test_poisson::test_la_hora_es_la_de_bogota_no_la_utc` |
| RNF-08 | Privacidad | `test_aceptacion_y_rnf::test_el_gitignore_protege_los_secretos_y_los_datos_de_encuestas`<br>`test_seed_comando::test_limpiar_no_toca_datos_reales` |

**Sin prueba automática** (se verifican de otra forma): RNF-05 «utilizable por personal sin formación técnica» (requiere usuarios reales: pendiente del piloto), RNF-09 portabilidad (se prueba construyendo la imagen de Docker, ver Sprint 6 #45) y RNF-10 mantenibilidad (revisión documental: ADR, tablero y commits convencionales).

## 4. Entorno y datos
- **Base de datos:** PostgreSQL 17 en Docker (`docker compose up -d db`); pytest-django crea una base temporal por corrida.
- **Datos de prueba:** fixtures mínimas por prueba; para los análisis, `seed_datos_simulados` con semilla fija. **Nunca datos reales.**
- **CI:** cada PR corre `ruff`, `makemigrations --check` y `pytest` en GitHub Actions; `main` solo se actualiza con el CI verde.

## 5. Cómo ejecutar
```
docker compose up -d db
pytest                                   # suite completa
pytest tests/test_funcional_flujo.py     # la jornada de punta a punta
set HOGARSITS_RENDIMIENTO=1 && pytest tests/test_rendimiento.py -s     # RNF-06 (lenta, opcional)
python manage.py validar_modelos --escenario todos --por-tamano        # validación estadística
coverage run -m pytest && coverage report                              # cobertura de código
```

## 6. Criterios de salida
- Todas las pruebas pasan y el CI está verde (las `xfail(strict)` son defectos conocidos y declarados, ver el informe).
- Cada criterio de aceptación tiene al menos una prueba (§2).
- RNF-06: ninguna pantalla supera los 3 s con más de 10 000 solicitudes.
- Los defectos hallados quedan corregidos o registrados con su decisión pendiente.
