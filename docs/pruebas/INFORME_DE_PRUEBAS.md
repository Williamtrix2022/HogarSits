# HogarSits — Informe de pruebas

**Versión:** 1.0 · **Fecha:** 23-nov-2026 · **Sprint:** 6 · **Issue:** #42 · **Plan:** [`PLAN_DE_PRUEBAS.md`](PLAN_DE_PRUEBAS.md)

> **Alcance de las cifras.** Todo lo que sigue se **midió** en este equipo (Windows, PostgreSQL 17 en Docker, Python 3.14, Django 6.1). Las pruebas usan datos simulados o creados por la propia prueba; **ninguna usa datos reales**. Que las pruebas pasen demuestra que el sistema cumple lo que las pruebas dicen: no demuestra que sea útil para una inmobiliaria real, que solo se sabrá con el piloto.

## 1. Resumen
| | |
|---|---|
| **Pruebas definidas** | **700** (29 archivos) |
| **Pasan** | **681** |
| **Defectos conocidos declarados** (`xfail` estricto) | **5**: 4 de RN-33 y 1 del estado del inmueble (§5) |
| **Opcionales** (rendimiento, se activan con una variable de entorno) | 14, **pasan todas** al activarlas (§4) |
| **Criterios de aceptación con prueba** | **31 de 31** (13 historias de usuario) |
| **Cobertura de código** | **98,2 %** de 3 052 sentencias (§3) |
| **Duración** | ≈ 8 min la suite completa con la cobertura activada (una corrida aislada llegó a 14 min; no se investigó la causa) |
| **CI** | `ruff`, `makemigrations --check` y `pytest` en cada PR; `main` solo recibe PR con CI verde |

La suma es exacta: 681 + 5 + 14 = 700. Las 681 se obtuvieron en tres ejecuciones (la suite completa con 656, más 16 y 9 de dos archivos escritos después); el CI de cada PR ejecuta la suite entera.

## 2. Pruebas por archivo
| Archivo | Pruebas | Qué cubre |
|---|---:|---|
| `test_analisis` | 51 | Panel de análisis: datos, textos de negocio, pantalla, filtro |
| `test_revision_panel` | 45 | Correcciones de la revisión independiente (E1 a E3, R1 a R6, O1 a O3) |
| `test_inmuebles` | 44 | CRUD, filtros, historial de estado |
| `test_cuentas` | 44 | Acceso, roles, usuarios, bloqueo por intentos, contraseñas |
| `test_exportar` | 42 | CSV: formato, seguridad, coincidencia con el panel |
| `test_etapas` | 42 | Transiciones RN-30 a RN-33, autotransición, cierre con inmueble |
| `test_poisson` / `test_colas` | 34 / 34 | λ por franja y ajuste; M/M/c y Erlang C |
| `test_horarios` | 33 | Turnos y asesores disponibles (`c` efectivo) |
| `test_fotos` | 29 | Subida, validación y borrado; configuración de S3 |
| `test_validacion` / `test_markov` | 28 / 28 | Estimado frente a simulado; matriz P y absorción |
| `test_agenda_pantallas` / `test_agenda` | 26 / 10 | Agenda sin cruces (servicio, pantallas y BD) |
| `test_solicitudes`, `test_pendientes`, `test_navegacion`, `test_indicadores` | 24 c/u | Atención, seguimiento, interfaz accesible, indicadores |
| `test_clientes` | 17 | CRUD y duplicados |
| `test_aceptacion_y_rnf` | 17 | HU-01 CA3 y requisitos no funcionales por configuración |
| `test_integridad` | 16 | Restricciones de la BD |
| `test_simulacion` | 15 | El generador recupera sus parámetros |
| `test_rendimiento` | 14 | RNF-06 (opcional) |
| `test_inmuebles_cerrados`, `test_huecos_de_cobertura` | 9 c/u | RN-03; ramas de error |
| `test_seed_comando` | 7 | El comando de datos simulados |
| `test_historial_inmutable` | 5 | RN-33 (4 `xfail`) |
| `test_funcional_flujo` | 3 | **La jornada completa de punta a punta** |
| `test_smoke` | 2 | Arranque |

### Prueba funcional de punta a punta
`test_jornada_completa_de_una_inmobiliaria` recorre las pantallas por HTTP en 15 pasos y comprueba en cada uno lo que la persona vería: el administrador da de alta a una asesora y le carga el horario → registra un inmueble → la asesora entra (una clave mala no la bloquea) → registra un cliente (un correo repetido se rechaza) → abre una solicitud con la llegada automática → la atiende → agenda una visita (un cruce se rechaza y nombra con cuál; uno contiguo se permite) → reprograma y cancela → avanza por las etapas (no se puede saltar; el seguimiento sin avance queda en el historial) → cierra marcando el inmueble como vendido → ya no se puede ofrecer ese inmueble → aparece en «a quién contactar» una solicitud olvidada → no entra a la administración → ve solo sus indicadores → cambia su contraseña → el administrador ve el análisis, los indicadores del equipo y descarga un CSV. **Pasa completa.**

## 3. Cobertura de código
Medida con `coverage` sobre `apps/` y `config/`, sin migraciones ni pruebas.

| Aplicación | Sentencias | Sin cubrir | Cobertura |
|---|---:|---:|---:|
| `inmuebles` | 360 | 4 | 98,9 % |
| `seguimiento` | 361 | 4 | 98,9 % |
| `agenda` | 469 | 5 | 98,9 % |
| `cuentas` | 311 | 4 | 98,7 % |
| `clientes` | 144 | 2 | 98,6 % |
| `comun` | 60 | 1 | 98,3 % |
| `analitica` | 1 280 | 26 | 98,0 % |
| `config` | 67 | 9 | 86,6 % |
| **Total** | **3 052** | **55** | **98,2 %** |

**Qué queda sin cubrir:** los puntos de entrada `wsgi.py` y `asgi.py` (solo se ejercitan al desplegar), las rutas lentas de `validar_modelos` (`--por-tamano` y `--escenario todos`, que simulan decenas de corridas), y ramas sueltas del simulador.

**La cobertura no es calidad.** El porcentaje no dice si los `assert` son buenos. Por eso se miraron las **líneas concretas** sin cubrir y se escribieron pruebas solo donde había lógica real: la carrera de dos asesores guardando a la vez, el reinicio del contador de bloqueo cuando este ya venció, y los mensajes cuando una acción ya no aplica. Hay un hueco conocido que la cobertura no puede mostrar: **la concurrencia real** (dos peticiones simultáneas) solo se simula con un parche, no se ejecuta en paralelo.

## 4. Rendimiento (RNF-06)
Con **10 262 solicitudes** simuladas (300 días, 5 asesores), medido en el servidor sin red ni navegador: mediana de 3 repeticiones y la peor.

| Pantalla | Mediana | Peor | Consultas |
|---|---:|---:|---:|
| Cola de solicitudes | 13 ms | 93 ms | 5 |
| Cola con filtro «todas» | 23 ms | 25 ms | 6 |
| Pendientes de seguimiento | 53 ms | 64 ms | 7 |
| Inicio (a quién contactar) | 36 ms | 41 ms | 9 |
| Clientes / búsqueda | 33 / 43 ms | 33 / 46 ms | 6 |
| Inmuebles | 22 ms | 23 ms | 6 |
| Agenda de la semana | 15 ms | 16 ms | 6 |
| Análisis (30 días con datos) | 63 ms | 66 ms | 17 |
| Indicadores por asesor | 41 ms | 42 ms | 13 |
| Exportar λ por hora / matriz P | 65 / 45 ms | 67 / 46 ms | 15 |
| **Análisis, rango máximo (299 días)** | **387 ms** | **532 ms** | 17 |

**Cumple con holgura:** la peor medición (532 ms) es 5,6 veces menor que el límite de 3 s. **Limitaciones:** es el tiempo de generar la respuesta en un solo proceso; no incluye la red, la carga del navegador ni usuarios concurrentes, y se midió en el equipo de desarrollo, no en AWS.

## 5. Defectos
### 5.1 Hallados por las pruebas y corregidos
| # | Defecto | Cómo se encontró |
|---|---|---|
| 1 | Reprogramar una visita fallaba con un error 500 (`KeyError`) al enviar el formulario | Prueba de la pantalla |
| 2 | Buscar un teléfono sin espacios no encontraba uno guardado con espacios | Prueba de búsqueda |
| 3 | Los cierres se contaban por registro: un duplicado sumaba dos cierres | Prueba de indicadores con cifras exactas |
| 4 | Exportar los indicadores devolvía 400: exigía un campo que no aplica | Prueba de la exportación |
| 5 | El panel creía que no había horarios cuando el horario era justo el de por defecto, y no calculaba las esperas | Prueba de extremo a extremo con datos simulados |
| 6 | Textos con «unos 1 de cada 10» y gráfico de esperas aplastado por un valor atípico | Revisión visual con capturas |
| 7 | La última fila del ajuste de Poisson se rotulaba «P(X = k)» pero es «k o más» (**E1**) | Revisión independiente, comprobado en el código |
| 8 | El redondeo forzaba c ≥ 1 y contradecía su propia advertencia (**E2**) | Ídem |
| 9 | «Hoy hay N asesores» era un promedio histórico (**E3**) | Ídem |
| 10 | Datos simulados no avisados si el cliente llegó antes del periodo (**R5**); la media de los indicadores incluía duraciones nulas (**R6**); frases con redondeos y extremos torpes (**O1**); el CSV de esperas no traía sus parámetros (**O2**); la recomendación se ocultaba sin horarios (**O3**) | Ídem |
| 11 | El comando `probar_almacenamiento` y una prueba imprimían símbolos que la consola de Windows no admite y fallaban | Al ejecutarlos de verdad (las pruebas capturan la salida y no lo veían) |

Además se corrigieron **errores en documentos**, no en el código: el «≈ 22,8 %» de la Propuesta es un doble redondeo (el valor exacto es 22,748 %); una expectativa propia sobre el χ² de Poisson era errónea y la corrigió una prueba; y un rango mal calculado en la validación («8 a 65 veces», era 3,5 a 65).

### 5.2 Conocidos y declarados, sin corregir
| Defecto | Estado | Qué falta |
|---|---|---|
| **RN-33:** el historial de etapas se puede editar y borrar | 4 pruebas `xfail(strict)` en `test_historial_inmutable` | Decidir el mecanismo; se recomienda un trigger de PostgreSQL, que cubre `save`, `delete`, borrado en bloque y `update` |
| **El estado del inmueble no tiene `CHECK` en la BD** (HU-01 CA3 se cumple solo en el formulario) | 1 prueba `xfail(strict)` | Una restricción `CHECK` con su migración |
| **Las esperas M/M/c son de orden de magnitud** | Documentado en el panel y en `VALIDACION_MODELOS.md` | Es un límite del modelo, no un error: la validación mostró que se desvía mucho cuando los asesores salen a visitas |
| **S3 sin verificar contra un bucket real** (#27) | Código probado con almacenamiento local y en memoria | Que el responsable cree el bucket y ejecute `probar_almacenamiento` |
| **HTTPS y despliegue** (#46) | La configuración de producción exige HTTPS (probado), pero no se desplegó | Verificarlo al desplegar |

Las `xfail` son estrictas: cuando alguien arregle el defecto, la prueba pasará y la suite fallará hasta que se quite la marca, de modo que **un defecto declarado no puede desaparecer en silencio**.

## 6. Validación estadística de los modelos
Resumida en [`../diseno/VALIDACION_MODELOS.md`](../diseno/VALIDACION_MODELOS.md): λ, μ y los pasos esperados se recuperan con 1 a 2 % de error y P(cierre) con 2,6 a 6,5 % (con 120 días); el error baja al tener más datos; el χ² de Poisson está bien calibrado (rechaza ≈ 5 % con datos que sí son de Poisson). **Salvedad:** valida el código frente a los supuestos del simulador, no el realismo.

## 7. Qué no se probó
- **Usabilidad con personas** (RNF-05): requiere el piloto.
- **Datos reales de una inmobiliaria:** ninguna prueba los usa; no se sabe cómo se comportan los modelos con ellos.
- **Concurrencia real** y carga con muchos usuarios a la vez.
- **Navegadores y dispositivos distintos** (las capturas se hicieron con Edge); no hay pruebas automáticas del JavaScript de los gráficos, solo de los datos que recibe.
- **Despliegue en AWS**, HTTPS real y S3 real.
- **Copias de seguridad y recuperación.**

## 8. Conclusión
El sistema **cumple los 31 criterios de aceptación** de las 13 historias y los requisitos no funcionales que una máquina puede comprobar, con una cobertura del 98,2 % y un rendimiento muy por debajo del límite. Para presentarlo como prototipo académico, los puntos que conviene **decir en voz alta** son: las esperas del panel son una aproximación, el historial de etapas todavía no es inmutable (RN-33), los números salen de datos simulados porque la ronda 2 de entrevistas no se ha hecho, y lo que no se pudo verificar (S3, AWS, usabilidad).
