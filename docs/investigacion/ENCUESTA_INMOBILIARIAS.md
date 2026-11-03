# HogarSits — Instrumento de validación con inmobiliarias de Montería

**Versión:** 0.1 (borrador listo para aplicar) · **Fecha:** 2026-11-03 · **Sprint:** 1 · **Issue:** #10
**Base:** Estudio de Mercado §10 y preguntas abiertas de [`REQUERIMIENTOS.md`](../requerimientos/REQUERIMIENTOS.md) §8 y [`CASOS_DE_USO.md`](../requerimientos/CASOS_DE_USO.md) §5.

Este documento es un **instrumento**: no contiene resultados. Las respuestas reales se guardarán aparte (ver §7).

## 1. Objetivos

1. **Validar la necesidad** (mercado): ¿las inmobiliarias sufren los problemas que HogarSits pretende resolver y pagarían por la solución?
2. **Obtener los parámetros operativos** que los modelos necesitan: número de asesores, horarios, duración de atenciones, etapas reales del proceso.
3. **Resolver las decisiones abiertas** de diseño (Sprint 2).
4. **Conseguir acceso a una inmobiliaria piloto** y a datos históricos autorizados.

Muestra exploratoria: **8 a 15 inmobiliarias** (no representativa de todo Montería; sirve para detectar patrones).

## 2. Modalidad y logística

| Elemento | Definición |
|---|---|
| Quién aplica | Natalia Durango (analista de requerimientos) con apoyo de un integrante más; William registra. |
| Con quién | Dueño, gerente o coordinador comercial de la inmobiliaria. Opcional: un asesor. |
| Formato | Entrevista corta de 20–30 min (presencial o por llamada) siguiendo §5; el cuestionario de §4 se llena durante la entrevista o se envía por formulario. |
| Herramienta | Google Forms o similar para §4; hoja de cálculo para §6. |
| Antes de empezar | Leer y obtener el consentimiento de §3. |

## 3. Presentación y consentimiento (leer al inicio)

> Somos estudiantes de Ingeniería de Sistemas de la Universidad de Córdoba. Estamos desarrollando **HogarSits**, un proyecto académico de la asignatura Procesos Estocásticos: un sistema para organizar inmuebles, clientes y visitas, y analizar la atención. **No vendemos ningún producto** ni esta conversación es un compromiso. Queremos entender cómo trabajan para diseñar mejor el sistema.
>
> - La participación es **voluntaria** y puede parar cuando quiera.
> - Anotaremos sus respuestas **sin datos personales de sus clientes**. Si luego aceptan compartir datos históricos, solo será con su autorización escrita y anonimizados.
> - Los resultados se usarán **únicamente con fines académicos**. Puede pedirnos que su inmobiliaria aparezca de forma anónima.
> - Sus datos de contacto se usarán solo para este proyecto, conforme a la Ley 1581 de 2012 (protección de datos personales).

☐ La persona entrevistada acepta participar y que se registren sus respuestas.
☐ Acepta que se cite el nombre de la inmobiliaria · ☐ Prefiere anonimato.

## 4. Cuestionario breve (cerrado)

Marque una opción por pregunta salvo que se indique lo contrario. Las preguntas P1–P6 son las del Estudio de Mercado; P7–P12 se añaden para parametrizar el sistema.

**Perfil**
- **P0.** Tamaño: nº de asesores ____ · nº aproximado de inmuebles en cartera ____ · ¿Venta, alquiler o ambos? ☐ Venta ☐ Alquiler ☐ Ambos

**Situación actual**
- **P1. ¿Cómo registra hoy los inmuebles y sus estados?** ☐ Cuadernos/archivos físicos ☐ Excel o Google Sheets ☐ Software especializado (¿cuál? ____) ☐ Combinación
- **P2. ¿Cómo registra y hace seguimiento a los clientes?** ☐ Manual, principalmente por WhatsApp ☐ Hojas de cálculo ☐ CRM o software ☐ No hay un proceso estandarizado
- **P3. ¿Con qué frecuencia tiene problemas para actualizar inmuebles o hacer seguimiento?** ☐ Nunca o casi nunca ☐ Algunas veces ☐ Frecuentemente ☐ No se mide
- **P4 (nueva). En los últimos 6 meses, ¿le ha pasado alguno de estos casos?** (varias opciones)
  ☐ Ofrecer un inmueble ya vendido/arrendado ☐ Dos visitas cruzadas (mismo asesor o mismo inmueble) ☐ Perder una solicitud sin seguimiento ☐ Clientes esperando mucho por falta de asesores ☐ Ninguno

**Interés en HogarSits**
- **P5. ¿Qué función sería más útil?** (ordene 1 = más útil)  ___ Inventario centralizado ___ Agenda y alertas de seguimiento ___ Reportes de atención y desempeño ___ Probabilidad de cierre
- **P6. ¿Estaría dispuesto a probar un prototipo?** ☐ Sí ☐ Tal vez, según las funciones ☐ No
- **P7. ¿Pagaría por una herramienta que resolviera sus principales necesidades?** ☐ Sí ☐ Depende del precio y las funciones ☐ No ☐ Necesito conocer el producto primero
- **P8 (nueva). Si pagaría, ¿cuánto sería razonable al mes?** ☐ Menos de $50.000 ☐ $50.000–$100.000 ☐ $100.000–$180.000 ☐ Más de $180.000 ☐ Prefiero no decir
  *(Referencia del Estudio: competidores entre ~$100.000 y ~$180.000 COP/mes; verificar precios vigentes.)*

**Parámetros operativos** (alimentan λ, μ, c y las etapas)
- **P9. ¿Cuántos clientes nuevos llegan en un día típico?** ____ · ¿En qué horas hay más? ☐ Mañana ☐ Mediodía ☐ Tarde ☐ Noche ☐ Fines de semana
- **P10. ¿Cuánto dura en promedio una primera atención (consulta)?** ☐ <10 min ☐ 10–30 min ☐ 30–60 min ☐ >60 min · ¿Y una visita a un inmueble? ____ min
- **P11. ¿Cuántos asesores atienden en un día típico y en qué horario?** ____ asesores · Horario: ____ a ____
- **P12. ¿Cuánto suele esperar un cliente antes de ser atendido y cuánto es lo máximo aceptable?** Típico ____ min · Máximo aceptable ____ min

## 5. Guion de entrevista (preguntas abiertas)

Preguntas para conversar; anotar palabras textuales cuando sea posible. Cada una indica qué decisión alimenta.

| # | Pregunta | Alimenta |
|---|---|---|
| E1 | Cuéntenos cómo es un día normal: desde que llega un cliente hasta que cierra o se pierde. | Etapas (Markov), RF-40 |
| E2 | ¿Qué etapas tiene realmente su proceso? ¿Coinciden con *consulta → visita → negociación → cierre/abandono*? ¿Falta o sobra alguna? | Estados de la cadena |
| E3 | Cuando un cliente sigue en la misma etapa varios días, ¿cómo lo registran? ¿Hay seguimientos que no cambian la etapa? | Decisión abierta 1 (autotransiciones) |
| E4 | ¿Cuándo un inmueble pasa a *reservado*? ¿Cuánto dura una reserva? ¿Un arriendo vuelve a quedar disponible? | Máquina de estados del inmueble |
| E5 | ¿Un cliente puede tener varias solicitudes o varias visitas? ¿Se hacen visitas grupales al mismo inmueble? | RN-02, RN-10, decisión abierta 3 |
| E6 | ¿Cómo deciden hoy cuántos asesores tener? ¿Hay turnos? ¿Atienden por teléfono y WhatsApp además de presencial? | c, canales de llegada |
| E7 | ¿Con qué rapidez debería hacerse seguimiento a una solicitud? ¿A partir de cuántos días sin respuesta se considera perdida? | RN-13 (N días), RN-40 |
| E8 | ¿Qué informes le gustaría recibir y cada cuánto? ¿Qué decisiones tomaría con ellos? | Dashboard, HU-07 a HU-09 |
| E9 | ¿Qué le preocuparía de usar un sistema nuevo (costo, tiempo, datos de clientes, capacitación)? | Estrategia de adopción, RNF |
| E10 | ¿Tienen registros históricos (Excel, cuadernos, WhatsApp) de al menos 2–3 meses que puedan compartir de forma anónima? | Datos reales, §6 |
| E11 | ¿Aceptaría probar un prototipo con una parte de su operación y darnos retroalimentación? ¿Con quién coordinamos? | Piloto |

## 6. Ficha de datos históricos a solicitar (opcional, anonimizada)

Para estimar λ, μ y P con datos reales. **Sin nombres, correos ni teléfonos de clientes**: usar un código (C001, C002…).

| Columna | Ejemplo | Para qué |
|---|---|---|
| `codigo_solicitud` | S-0001 | Identificar |
| `fecha_hora_llegada` | 2026-03-04 10:25 | λ por franja |
| `fecha_hora_inicio_atencion` | 2026-03-04 10:40 | Espera |
| `fecha_hora_fin_atencion` | 2026-03-04 11:05 | μ |
| `asesor` (código) | A2 | c |
| `tipo_interes` | compra / alquiler | Segmentación |
| `etapa_y_fecha` (una fila por cambio) | Visita, 2026-03-06 | Matriz P |
| `resultado_final` | cierre / abandono / en curso | Absorción |

Mínimo útil: ~30 llegadas por franja y ~30 transiciones por etapa de origen (RN-40); si no hay tanto, se completa con datos simulados y se aclara en el informe.

## 7. Registro de contactos y respuestas

Mantener **fuera del repositorio público** los datos personales: usar una hoja de cálculo privada del equipo (Google Sheets). En el repo solo se guardan resultados agregados y anónimos en `docs/investigacion/resultados/`.

| Campo | Descripción |
|---|---|
| ID | I01, I02… (sin nombre) |
| Tipo de inmobiliaria | Pequeña / mediana / grande |
| Fecha, entrevistador, modalidad | |
| Consentimiento / anonimato | Sí-No |
| Respuestas P0–P12 | |
| Notas E1–E11 | |
| ¿Piloto? ¿Datos históricos? | Sí / No / Tal vez |

Candidatas de partida (tomadas del Estudio de Mercado, **no son clientes confirmados**): MYM Inmobiliaria Montería, Kayros Inmobiliaria, INMONTERIA Asesorías Inmobiliarias, Araújo y Segovia. Completar hasta 8–15 con inmobiliarias de distinto tamaño, incluyendo alguna con un solo asesor y alguna con varios.

## 8. Plan de análisis

1. **Tabular** P1–P8: porcentajes por opción (con n pequeño, reportar conteos, no solo %).
2. **Parámetros operativos** (P9–P12): rangos y medianas de llegadas/día, duración de atención y asesores; sirven para fijar los valores por defecto del generador de datos simulados (RF-60).
3. **Cualitativo** (E1–E11): agrupar respuestas por tema y contrastar con los supuestos de [`CASOS_DE_USO.md`](../requerimientos/CASOS_DE_USO.md) §5.
4. **Decisiones:** cada hallazgo se traduce en un cambio al documento de requerimientos (versión 0.2) o en un ADR.

| Resultado observado | Qué haríamos |
|---|---|
| La mayoría reporta problemas frecuentes (P3, P4) y quiere probar (P6) | Priorizar gestión + agenda; buscar piloto. |
| Casi nadie tiene colas ni quiere reportes de atención | Reforzar el valor del seguimiento y de Markov; documentar la limitación para Poisson/colas. |
| Etapas reales distintas a las 5 del modelo | Ajustar los estados de la cadena antes del Sprint 2. |
| Disposición a pagar baja | No fijar precios; enfocar el trabajo como prototipo académico. |

## 9. Limitaciones

- Muestra pequeña y por conveniencia: no permite generalizar a todo Montería.
- Respuestas autodeclaradas (duración, volumen) pueden ser imprecisas; se contrastan con datos históricos si se obtienen.
- La disposición a pagar declarada suele ser mayor que la real.

## 10. Checklist antes de salir a campo

- [ ] El equipo revisó y aprobó este instrumento (¿preguntas claras, tiempo ≤ 30 min?).
- [ ] Pasar el cuestionario a Google Forms y hacer una **prueba piloto** con 1–2 personas conocidas.
- [ ] Lista de inmobiliarias a contactar y reparto entre integrantes.
- [ ] Carta/mensaje corto de presentación (con el nombre de la universidad y de la asignatura).
- [ ] Hoja privada de registro creada y compartida solo con el equipo.
