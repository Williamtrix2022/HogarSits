# HogarSits — Documento de Requerimientos (Fase 1)

**Versión:** 0.2 (borrador) · **Fecha:** 2026-11-07 · **Sprint:** 1–2 · **Issues:** #8, #50
**Fuentes:** `docs/HogarSits_Propuesta_Proyecto.docx`, `docs/HogarSits_Estudio_de_Mercado.md`, `README.md`.

> **Estado de validación.** La v0.1 se derivó de la Propuesta y del Estudio de Mercado. La v0.2 incorpora la **ronda 1 de encuestas (n = 3, ver [resultados](../investigacion/resultados/RESULTADOS_ENCUESTA.md))**: muestra pequeña, así que las necesidades siguen siendo **hipótesis** parcialmente respaldadas. Los requerimientos marcados con ⚠️ dependen de esa validación y pueden cambiar. Hasta tener datos reales, el sistema se desarrolla con datos simulados.

**Cambios en v0.2** (detalle en §10): RF-25 sube a *debe*; nuevos RF-26, RF-35, RF-36, RF-59 y RF-62; RF-60 incorpora picos y ocupación del asesor; nuevas HU-12 y HU-13.

---

## 1. Propósito y alcance

HogarSits es una aplicación web para una inmobiliaria que (a) centraliza inmuebles, clientes, solicitudes, visitas y etapas comerciales, y (b) analiza los registros con procesos estocásticos: Poisson (llegadas), teoría de colas M/M/c (atención) y cadenas de Markov (avance del cliente).

**Dentro del alcance:** gestión de inmuebles, clientes, solicitudes de atención, agenda de visitas sin cruces, seguimiento de etapas, módulo analítico con dashboard, generación de datos simulados, pruebas y documentación.

**Fuera del alcance (versión académica):** pasarela de pagos, firma de contratos, publicación en portales inmobiliarios, app móvil, acceso de clientes finales al sistema, integración con WhatsApp, facturación, multi-inmobiliaria (multi-tenant).

## 2. Actores

| Actor | Descripción | Acceso |
|---|---|---|
| **Administrador** | Responsable comercial / dueño. Gestiona usuarios, ve todos los indicadores. | Total |
| **Asesor** | Atiende clientes, agenda visitas, actualiza etapas. | Operativo (sus solicitudes y agenda; consulta de inmuebles) |
| **Analista** (rol funcional del Administrador) | Consulta el módulo analítico y exporta resultados. | Lectura de analítica |
| *Cliente* | Persona interesada en comprar o arrendar. **No es usuario del sistema**: es un dato registrado. | — |

## 3. Requerimientos funcionales

Prioridad con MoSCoW: **M** (debe), **S** (debería), **C** (podría). Sprint = en cuál se implementa.

### 3.1 Autenticación y usuarios
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-01 | El sistema permite iniciar y cerrar sesión con usuario y contraseña. | M | 3 |
| RF-02 | El administrador crea, edita y desactiva usuarios asesores. | M | 3 |
| RF-03 | Los permisos se restringen por rol (Administrador / Asesor). | M | 3 |

### 3.2 Inmuebles
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-10 | Registrar, editar, consultar y desactivar inmuebles (casas y apartamentos) con: tipo de inmueble, tipo de operación (venta/alquiler), dirección/ubicación, precio, área, habitaciones, descripción. | M | 3 |
| RF-11 | Cada inmueble tiene un estado: **Disponible, Reservado, Vendido, Arrendado**. | M | 3 |
| RF-12 | Cambiar el estado queda registrado (quién y cuándo). | S | 4 |
| RF-13 | Adjuntar y ver fotos del inmueble. | S | 3 |
| RF-14 | Buscar y filtrar inmuebles por estado, operación, precio y ubicación. | M | 3 |
| RF-15 | Un inmueble Vendido o Arrendado no puede ofrecerse en nuevas solicitudes ni visitas; el sistema avisa si aparece como disponible con una operación cerrada. | M | 4 |

### 3.3 Clientes y solicitudes
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-20 | Registrar, editar y consultar clientes (nombre, correo, teléfono). | M | 3 |
| RF-21 | Evitar clientes duplicados (por correo y/o teléfono) y avisar al intentar duplicar. | M | 3 |
| RF-22 | Registrar una **solicitud de atención** con cliente, tipo de interés (compra/alquiler), presupuesto e inmueble de interés (opcional). El sistema guarda automáticamente la **fecha y hora de llegada**. | M | 3 |
| RF-23 | Una solicitud pasa por los estados **En espera → En atención → Finalizado / Cancelado**, registrando la hora de inicio y fin de la atención. | M | 3 |
| RF-24 | Asignar un asesor a la solicitud. | M | 3 |
| RF-25 | Listar solicitudes pendientes y marcar las que llevan más de N días sin seguimiento (alerta). ⚠️ N por validar (E7). *Sube a M: 3 de 3 encuestadas han perdido solicitudes por falta de seguimiento.* | M | 4 |
| RF-26 | Recordatorios de seguimiento: cada asesor ve las solicitudes que le toca contactar hoy. | M | 4 |

### 3.4 Agenda de visitas
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-30 | Programar una visita: inmueble, cliente/solicitud, asesor, fecha, hora de inicio y duración. | M | 4 |
| RF-31 | El sistema **rechaza** una visita que se cruce en horario con otra del **mismo asesor**. | M | 4 |
| RF-32 | El sistema **rechaza** una visita que se cruce en horario con otra del **mismo inmueble**. | M | 4 |
| RF-33 | Reprogramar, cancelar y marcar una visita como realizada. | M | 4 |
| RF-34 | Ver la agenda por asesor y por día/semana. | S | 4 |
| RF-35 | Recordatorio de las visitas próximas al asesor (p. ej. del día siguiente). | S | 4 |
| RF-36 | Registrar el **horario semanal** de cada asesor. Una visita programada marca al asesor como **ocupado**; el sistema puede calcular cuántos asesores hay disponibles (c efectivo) por franja. | M | 2 (modelo) / 4 (uso) |

### 3.5 Seguimiento de etapas
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-40 | Cada solicitud tiene una etapa actual: **1 Consulta, 2 Visita, 3 Negociación, 4 Cierre, 5 Abandono**. | M | 4 |
| RF-41 | Cada cambio de etapa se guarda como transición (origen, destino, fecha y hora) y el historial es consultable. | M | 4 |
| RF-42 | Las etapas 4 y 5 son finales: no admiten más transiciones. | M | 4 |
| RF-43 | Al registrar un Cierre, se puede actualizar el estado del inmueble (Vendido/Arrendado/Reservado). | S | 4 |

### 3.6 Módulo analítico
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-50 | **Poisson:** estimar λ (clientes/hora) por franja horaria y día a partir de las llegadas registradas; mostrar P(X=k) y comparar con la frecuencia observada. | M | 5 |
| RF-51 | **Colas M/M/c:** a partir de λ, μ y c, calcular ρ, L, Lq, W y Wq; indicar si el sistema es estable (ρ < 1). | M | 5 |
| RF-52 | Estimar μ a partir de la duración de atención registrada. | M | 5 |
| RF-53 | Recomendar el número mínimo de asesores c para que el tiempo de espera Wq no supere un umbral configurable. ⚠️ Umbral por validar. | S | 5 |
| RF-54 | **Markov:** construir la matriz de transición P a partir de las transiciones registradas, con estados transitorios (1–3) y absorbentes (4–5). | M | 5 |
| RF-55 | Calcular la matriz fundamental N = (I − Q)⁻¹, las probabilidades de absorción (cierre vs. abandono) y el número esperado de pasos hasta la absorción. | M | 5 |
| RF-56 | Dashboard con tablas y gráficas (llegadas, colas, matriz P, probabilidades) y filtro por rango de fechas. | M | 5 |
| RF-57 | Advertir cuando no hay datos suficientes para estimar (p. ej. menos de un mínimo de observaciones). | S | 5 |
| RF-58 | Exportar resultados (CSV o PDF). | C | 5 |
| RF-59 | Presentar los resultados con **textos en lenguaje de negocio** junto a las cifras (p. ej. «de cada 10 clientes, 2 cierran», «con 2 asesores esperarías unos 29 min»). *La analítica fue lo menos valorado en la encuesta.* | M | 5 |
| RF-62 | **Indicadores por asesor**: solicitudes atendidas, visitas realizadas, cierres y tiempos de atención. *Pedido por una inmobiliaria.* | S | 5 |

### 3.7 Datos simulados y validación
| ID | Requerimiento | Prio | Sprint |
|---|---|---|---|
| RF-60 | Comando que genera datos simulados: llegadas con proceso de Poisson **con λ distinto por franja (picos de mañana y tarde)**, tiempos de atención exponenciales, **visitas de 30–120 min que ocupan al asesor** y trayectorias de Markov con una matriz P configurable. Parámetros por defecto de la ronda 1: 2–5 asesores, 9–12 h de atención, 4–20 llegadas/día. | M | 2 |
| RF-61 | Poder comparar los parámetros estimados con los parámetros usados para simular (λ, μ, P) para validar los modelos. | M | 6 |

## 4. Requerimientos no funcionales

| ID | Categoría | Requerimiento |
|---|---|---|
| RNF-01 | Corrección matemática | Los cálculos reproducen los ejemplos de la Propuesta: M/M/1 con λ=2, μ=3 → ρ≈0,67, L=2, W=1 h, Lq≈1,33, Wq≈0,67 h; matriz P del README → P(cierre desde Consulta)≈22,8 %, pasos esperados≈2,4. |
| RNF-02 | Calidad | Lógica estocástica en funciones puras con tests automáticos; CI verde antes de integrar a `main`. |
| RNF-03 | Integridad de datos | La BD impide por restricción (no solo por la interfaz) los cruces de agenda y los correos duplicados. |
| RNF-04 | Seguridad | Autenticación obligatoria; contraseñas con hash de Django; secretos fuera del repositorio; HTTPS en producción. |
| RNF-05 | Usabilidad | Interfaz en español (es-CO), utilizable por personal sin formación técnica; formularios con mensajes de error claros. |
| RNF-06 | Rendimiento | Listados y dashboard responden en < 3 s con hasta ~10 000 solicitudes. |
| RNF-07 | Zona horaria | Los datos se guardan en UTC y se muestran en America/Bogota; las franjas horarias del análisis usan hora local. |
| RNF-08 | Privacidad | Los datos personales de clientes se tratan conforme a la Ley 1581 de 2012 (habeas data); no se usan datos reales sin autorización de la inmobiliaria. ⚠️ Revisar con la inmobiliaria. |
| RNF-09 | Portabilidad | Ejecutable en local con Docker Compose y desplegable en AWS (Sprint 6). |
| RNF-10 | Mantenibilidad | Documentación de decisiones (ADR), tablero de sprints actualizado, commits convencionales. |

## 5. Historias de usuario (para el backlog)

Formato: *Como … quiero … para …* con criterios de aceptación (CA). Estas historias se convierten en issues en el #11.

**HU-01 · Gestionar inmuebles** (RF-10, 11, 14) — *Como asesor quiero registrar y buscar inmuebles con su estado para no ofrecer propiedades que ya no están disponibles.*
- CA1: puedo crear un inmueble con tipo, operación, dirección, precio, área y habitaciones.
- CA2: puedo filtrar por estado, operación y rango de precio.
- CA3: el estado solo toma los valores Disponible, Reservado, Vendido o Arrendado.

**HU-02 · Evitar ofrecer inmuebles cerrados** (RF-15) — *Como administrador quiero que el sistema bloquee o advierta cuando un inmueble vendido/arrendado se use en una solicitud o visita.*
- CA1: no puedo agendar una visita para un inmueble Vendido o Arrendado.
- CA2: al marcar un Cierre, el sistema propone actualizar el estado del inmueble.

**HU-03 · Registrar clientes sin duplicados** (RF-20, 21) — *Como asesor quiero registrar clientes y que el sistema detecte duplicados para mantener datos limpios.*
- CA1: al ingresar un correo ya existente, el sistema muestra el cliente existente y no crea otro.
- CA2: nombre, correo y teléfono son obligatorios y se validan.

**HU-04 · Registrar solicitudes con hora de llegada** (RF-22, 23, 24) — *Como asesor quiero registrar cada solicitud con su hora de llegada y de atención para que luego se puedan calcular λ y μ.*
- CA1: la hora de llegada se guarda automáticamente al crear la solicitud.
- CA2: al iniciar y finalizar la atención se registran las horas correspondientes.
- CA3: la hora de fin no puede ser anterior a la de inicio.

**HU-05 · Agendar visitas sin cruces** (RF-30–33) — *Como asesor quiero agendar visitas y que el sistema evite cruces para no dejar a un cliente esperando.*
- CA1: no puedo guardar una visita que se solape con otra del mismo asesor.
- CA2: no puedo guardar una visita que se solape con otra del mismo inmueble.
- CA3: puedo reprogramar y cancelar; las visitas canceladas no bloquean el horario.

**HU-06 · Seguir la etapa del cliente** (RF-40–42) — *Como asesor quiero registrar en qué etapa está cada cliente para saber qué falta y alimentar el análisis de Markov.*
- CA1: cada cambio de etapa queda con fecha y hora, y se ve el historial.
- CA2: una solicitud en Cierre o Abandono no admite más cambios.

**HU-07 · Ver demanda por franja horaria** (RF-50) — *Como administrador quiero ver λ por hora y día para saber cuándo llegan más clientes.*
- CA1: el dashboard muestra λ estimado por franja y día.
- CA2: se muestra la distribución de Poisson ajustada junto a la frecuencia observada.

**HU-08 · Dimensionar asesores** (RF-51–53) — *Como administrador quiero conocer ρ, Lq y Wq (explicados en lenguaje de negocio, RF-59) para decidir cuántos asesores necesito.*
- CA1: el sistema calcula ρ, L, Lq, W, Wq con λ, μ y c.
- CA2: si ρ ≥ 1 se muestra una advertencia de inestabilidad.
- CA3: se sugiere el menor c que cumple el umbral de espera.

**HU-09 · Conocer la probabilidad de cierre** (RF-54–55) — *Como administrador quiero saber qué porcentaje de clientes cierra, abandona y cuánto tarda el proceso.*
- CA1: se muestra la matriz P estimada con los datos registrados.
- CA2: se muestran P(cierre), P(abandono) y pasos esperados desde cada etapa inicial.

**HU-10 · Probar con datos simulados** (RF-60, 61) — *Como analista quiero generar datos simulados con parámetros conocidos para validar que los modelos los recuperan.*
- CA1: un comando genera N solicitudes con λ, μ y P configurables.
- CA2: el informe compara parámetros reales vs. estimados.

**HU-12 · No perder solicitudes ni visitas** (RF-25, 26, 35) — *Como asesor quiero ver cada mañana a quién debo contactar y qué visitas tengo para que ninguna solicitud se pierda por falta de seguimiento.*
- CA1: veo una lista de solicitudes con seguimiento pendiente, ordenada por antigüedad.
- CA2: las solicitudes sin movimiento más de N días aparecen marcadas.
- CA3: veo mis visitas del día y del siguiente.

**HU-13 · Evaluar el desempeño del equipo** (RF-62) — *Como administrador quiero ver indicadores por asesor para conocer la carga y los resultados de cada uno.*
- CA1: por asesor y rango de fechas: solicitudes atendidas, visitas realizadas, cierres y tiempo medio de atención.
- CA2: un asesor solo ve sus propios indicadores.

**HU-11 · Controlar accesos** (RF-01–03) — *Como administrador quiero que cada persona vea solo lo que le corresponde.*
- CA1: un asesor no puede administrar usuarios.
- CA2: sin iniciar sesión no se accede a ninguna pantalla de gestión.

## 6. Datos que el sistema debe capturar para los modelos

| Dato | Entidad / campo | Usado en |
|---|---|---|
| Hora de llegada de la solicitud | `SolicitudAtencion.timestamp_llegada` | λ, Poisson |
| Inicio y fin de la atención | `timestamp_inicio_atencion`, `timestamp_fin_atencion` | μ, colas |
| Asesores disponibles por franja | `HorarioAsesor` (turno semanal) menos las `Visita` programadas en la franja | c efectivo en M/M/c |
| Etapa origen, destino y fecha de cada transición | `SeguimientoEtapa` | Matriz P |
| Resultado final (cierre/abandono) | Etapa final de la solicitud | Absorción |

**Brechas del modelo (se cierran en el Sprint 2, issues #19 y #22):** modelo `Visita`; `HorarioAsesor` (disponibilidad); `Inmueble` con tipo, área, habitaciones y fotos; `SolicitudAtencion` con tipo de interés, presupuesto y etapa actual. **Pendiente de la ronda 2:** estados y autotransiciones de la cadena de Markov (ADR-002, #20).

## 7. Restricciones y supuestos

- **Académico:** alcance y fechas fijados por la asignatura; equipo de 4 personas con roles definidos en el README.
- **Tecnológicas:** Python/Django, PostgreSQL, NumPy/SciPy/Pandas, Chart.js o Matplotlib, Git/GitHub (ADR-001).
- **Supuestos estocásticos** (a verificar con datos): llegadas de Poisson homogéneo dentro de cada franja; tiempos de atención exponenciales; cadena de Markov homogénea y sin memoria. Si los datos reales no los cumplen, se documenta la limitación en el informe final.
- **Hallazgo de la ronda 1:** λ **no es constante** en el día (picos de mañana y tarde) y las visitas (30–120 min) sacan al asesor de la oficina. Por eso λ se estima por franja y c es el número de asesores *disponibles*, no el total. En 2 de 3 inmobiliarias el modelo M/M/c con λ diario predice esperas mucho menores a las reportadas.
- **Datos:** hasta obtener datos reales, se trabaja con datos simulados; los resultados no son conclusiones sobre el mercado de Montería.

## 8. Preguntas abiertas para la inmobiliaria

*Ronda 1 respondió las preguntas 2 y 3 en parte (asesores, horarios, duración de atención). Quedan para la **ronda 2** (con I02): 4 (etapas reales), 5 (N días y espera máxima), 7 (visitas grupales y varias solicitudes), y cómo registran un seguimiento que no cambia la etapa.*

1. ¿Cómo registran hoy inmuebles, clientes y visitas, y con qué herramientas?
2. ¿Cuántos asesores atienden y en qué horarios? ¿Atienden en oficina, por teléfono o por mensajes?
3. ¿Cuánto dura en promedio una atención o visita? ¿Cuántas visitas hace un asesor por día?
4. ¿Qué etapas reales tiene su proceso? ¿Coinciden con Consulta → Visita → Negociación → Cierre/Abandono?
5. ¿Con qué rapidez debería seguirse una solicitud (N días para alerta)? ¿Qué espera máxima es aceptable (umbral de Wq)?
6. ¿Qué informes necesita el administrador? ¿Hay datos históricos que se puedan usar y con qué autorización?
7. ¿Un inmueble puede tener varias visitas a la misma hora (visitas grupales)? ¿Y un cliente varias solicitudes?

## 9. Trazabilidad con las fases y sprints

| Fase | Sprint | Requerimientos cubiertos |
|---|---|---|
| F1 Requerimientos | 1 | Este documento, casos de uso (#9), encuesta (#10), backlog (#11) |
| F2 Diseño | 2 | Modelo de datos (sección 6), RF-60 |
| F3 Gestión | 3–4 | RF-01 a RF-43 (incluye RF-26, RF-35, RF-36) |
| F4 Analítica | 5 | RF-50 a RF-59 y RF-62 |
| F5–F6 Pruebas y entrega | 6 | RF-61, RNF-01, RNF-06, RNF-09 |

## 10. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-11-03 | Borrador inicial a partir de Propuesta, Estudio de Mercado y README. |
| 0.2 | 2026-11-07 | Ronda 1 de encuestas (n = 3): RF-25 a *debe*; añadidos RF-26 (recordatorios), RF-35 (recordatorio de visitas), RF-36 (horario y disponibilidad del asesor), RF-59 (lenguaje de negocio), RF-62 (indicadores por asesor), HU-12 y HU-13; RF-60 con picos y ocupación; supuestos y brechas actualizados. |
