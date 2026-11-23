# HogarSits — Guion de la ronda 2 de entrevistas

**Versión:** 1.0 · **Fecha:** 2026-11-23 · **Issue:** #55 · **Instrumento base:** [`ENCUESTA_INMOBILIARIAS.md`](ENCUESTA_INMOBILIARIAS.md) · **Ronda 1:** [`resultados/RESULTADOS_ENCUESTA.md`](resultados/RESULTADOS_ENCUESTA.md)

Este documento es un **guion para aplicar**: no contiene resultados. Las respuestas reales se anotan en la plantilla de §4 *durante* la entrevista y se resumen, anónimas, en `resultados/`. **Si una pregunta no se hizo o no se supo la respuesta, se anota así; nunca se completa de memoria ni por suposición.** Para el trabajo mientras no hay respuestas, ver [`SUPUESTOS_DE_TRABAJO.md`](SUPUESTOS_DE_TRABAJO.md).

## 1. Qué se necesita y por qué
La ronda 1 (n = 3) dejó cinco decisiones sin datos (las notas no registraron E2 a E5) y abrió una pregunta nueva. Cada una bloquea o ajusta algo ya construido:

| # | Pregunta | Qué decide | Qué cambia en HogarSits |
|---|---|---|---|
| **E3** | Seguimientos sin cambio de etapa | Si el ADR-002 se mantiene | La estimación de la diagonal de la matriz P (#37) |
| **E7** | Días sin respuesta → seguimiento y → «perdida» | El valor de N | `DIAS_SIN_SEGUIMIENTO` (hoy 3, provisional) y RN-13 / RN-40 |
| **E2** | Etapas reales del proceso | Los estados de la cadena | Estados de Markov, RF-40 |
| **E4** | Reservas y retorno de arrendados | La máquina de estados del inmueble | Vencimiento de reserva; Arrendado → Disponible |
| **E5** | Varias solicitudes y visitas grupales | RN-02 y RN-10 | Cruces de agenda; unicidad del cliente |
| **V1 (nueva)** | Quién hace las visitas y cuántas por día | El `c` efectivo | Disponibilidad de asesores (#53) y el generador de datos |
| **I03** | ¿Qué pasó con esa encuesta? | Tamaño de la muestra | n de la ronda 1 |

## 2. Antes de empezar
- **Con quién:** prioridad a **I02** (piloto: 5 asesores, 80 inmuebles, notas detalladas). Después, las inmobiliarias nuevas hasta llegar a **8** (hoy hay 3; faltan 5).
- **Duración:** 20 a 25 min. Con I02, solo la parte A (§3) alcanza; con una inmobiliaria nueva, antes el cuestionario cerrado P0–P12 (§4 de `ENCUESTA_INMOBILIARIAS.md`) y luego la parte A.
- **Consentimiento:** leer y marcar el texto de §3 de `ENCUESTA_INMOBILIARIAS.md` (voluntario, académico, sin datos personales de clientes, anonimato si lo piden). **I04 pidió anonimato.**
- **Quién registra:** una persona pregunta y otra anota **textual** lo que dicen, entre comillas. Es la lección de la ronda 1: las notas no recogieron E2 a E5.
- **No llevar a la persona a la respuesta.** Pregunte abierto, escuche, y solo después ofrezca las opciones del recuadro «Si no sabe cómo responder».

## 3. Parte A: las preguntas (en este orden)

### E3 — Seguimientos que no cambian la etapa *(la más importante: decide el ADR-002)*
**Pregunte:** «Cuando usted o un asesor llama o escribe a un cliente y todo sigue igual, ¿lo anotan en algún lado? ¿Dónde y cómo?»
**Profundice:** ¿Anotan solo cuando hay un avance (visita, oferta) o también cuando «no contestó» o «dijo que lo piensa»? ¿Cuántas veces suelen contactar a un cliente antes de que avance o se pierda?
*Si no sabe cómo responder:* ☐ solo anotamos los avances ☐ anotamos todo contacto ☐ no anotamos nada, queda en la memoria o en WhatsApp.
**Qué anotar:** la frase textual y cuál de las tres describe su práctica.

### E7 — ¿Cuántos días?
**Pregunte:** «Si un cliente no responde, ¿a los cuántos días vuelve a contactarlo? ¿Y a los cuántos días sin respuesta da la solicitud por perdida?»
**Son dos números distintos:** el de **recontacto** (alimenta N, el umbral «sin seguimiento») y el de **pérdida** (cuándo pasa a Abandono). Anote los dos y si varían por tipo (compra / alquiler).
**Qué anotar:** días de recontacto: ____ · días para dar por perdida: ____ · ¿varía?: ____

### E2 — Las etapas reales
**Pregunte:** «Describa el camino de un cliente desde que llega hasta que cierra o se pierde.» *No muestre aún las 5 etapas.* Después: «Nosotros usamos Consulta → Visita → Negociación → Cierre o Abandono. ¿Falta alguna? ¿Sobra alguna?»
**Profundice:** ¿Hay una etapa de «reserva» o «separación» con anticipo? ¿Se visita más de una vez? ¿Se puede volver atrás (de Negociación a Visita)?
**Qué anotar:** las etapas en sus palabras, en orden, y qué le falta o le sobra a nuestro modelo.

### E4 — Reservas y arriendos
**Pregunte:** «¿Cuándo pasa un inmueble a “reservado”? ¿Cuánto dura una reserva? Cuando termina un arriendo, ¿el inmueble vuelve a ofrecerse?»
**Qué anotar:** qué la dispara (anticipo, palabra, contrato), duración en días, quién la libera si vence, y si un arrendado vuelve a Disponible (cuándo).

### E5 — Varias solicitudes y visitas grupales
**Pregunte:** «¿Un mismo cliente puede tener varias solicitudes a la vez? ¿Se hacen visitas con varios clientes al mismo inmueble a la misma hora?»
**Qué anotar:** sí/no/a veces, y un ejemplo. Una visita grupal es lo que hoy **la agenda rechaza** como cruce (RN-02).

### V1 — Quién hace las visitas *(nueva, del hallazgo del generador de datos)*
**Pregunte:** «Cuando hay que mostrar un inmueble, ¿quién va? ¿Cuántas visitas hacen en un día normal y en el más cargado? ¿La persona que visita es la misma que atiende en la oficina?»
**Profundice:** ¿Cuánto dura una visita contando el desplazamiento? Mientras ese asesor está fuera, ¿quién atiende a los clientes que llegan? ¿Hay alguien que solo hace visitas (asesor de campo, el dueño)?
**Qué anotar:** visitas por día (típico / máximo), duración total, **quién las hace**, y si la oficina queda con menos gente mientras tanto.
**Por qué importa:** con la matriz del README, ~6 de cada 10 clientes terminan agendando visita; si esa visita ocupa al mismo asesor que atiende, una oficina de 2 asesores se satura (ver `DATOS_SIMULADOS.md` §5). Si las hace otra persona, el modelo debe cambiar.

### I03 — Aclarar la encuesta faltante
Con el equipo, no con la inmobiliaria: ¿I03 se aplicó, se perdió o no se llegó a hacer? Anotar cuál de las tres y qué se decide (reaplicar, descartar y renumerar).

## 4. Plantilla de registro (copiar una por entrevista)
**Esta hoja va en el espacio privado del equipo (Drive).** En el repositorio público solo entran resultados agregados y anónimos (ver `RESULTADOS_ENCUESTA.md` §8).

```
ID: I__            Fecha: ____/____/2026      Modalidad: ☐ presencial ☐ llamada
Entrevistó: ______  Anotó: ______             Duración: ____ min
Tamaño: ____ asesores · ____ inmuebles · ☐ venta ☐ alquiler ☐ ambos
Consentimiento: ☐ sí  ·  ☐ puede citarse el nombre  ☐ anonimato

E3  Respuesta textual: "________________________________________"
    ☐ solo avances  ☐ todo contacto  ☐ nada se anota          ☐ NO SE PREGUNTÓ  ☐ NO SABE
E7  Días de recontacto: ____   Días para dar por perdida: ____   ¿Varía?: ______   ☐ NO SE PREGUNTÓ ☐ NO SABE
E2  Etapas (en sus palabras): ________________________________
    Falta: ________   Sobra: ________   ¿Se retrocede?: ____    ☐ NO SE PREGUNTÓ ☐ NO SABE
E4  Qué reserva el inmueble: ______  Duración: ____ días  ¿Arrendado vuelve a Disponible?: ____
                                                                ☐ NO SE PREGUNTÓ ☐ NO SABE
E5  ¿Varias solicitudes por cliente?: ____  ¿Visitas grupales?: ____  Ejemplo: ______
                                                                ☐ NO SE PREGUNTÓ ☐ NO SABE
V1  Quién visita: ______  Visitas/día (típico · máximo): ____ · ____  Duración total: ____ min
    ¿Es el mismo que atiende en oficina?: ____  ¿Quién cubre la oficina?: ______
                                                                ☐ NO SE PREGUNTÓ ☐ NO SABE
Citas textuales útiles: "____________________________________"
¿Piloto?: ☐ sí ☐ tal vez ☐ no     ¿Datos históricos anonimizados?: ☐ sí ☐ tal vez ☐ no
```
Las casillas **NO SE PREGUNTÓ / NO SABE** existen para que un hueco quede visible y no se rellene.

## 5. De la respuesta a la decisión
| Si la respuesta a… | Entonces |
|---|---|
| **E3** es «anotamos todo contacto» | El ADR-002 se mantiene: la diagonal se estima como está. |
| **E3** es «solo anotamos avances» o «nada» | Revisar el ADR-002: pasar a la opción C (cadena sin diagonal) o a la B (un trabajo diario). Un nuevo ADR reemplaza al actual. |
| **E7** da un recontacto distinto de 3 días | Fijar `DIAS_SIN_SEGUIMIENTO` a la **mediana** de las respuestas y registrar cuántas inmobiliarias la respaldan. |
| **E2** muestra una etapa que no tenemos (p. ej. «reserva») | Evaluar agregarla a la cadena **antes** de estimar P en el Sprint 5. |
| **E4** da una reserva con vencimiento | Agregar duración y liberación automática a las reservas de inmuebles. |
| **E5** dice que hay visitas grupales | Revisar RN-02: hoy la BD rechaza dos visitas al mismo inmueble a la misma hora. |
| **V1** dice que las visitas las hace otra persona | El `c` efectivo no debe restar esas visitas al asesor de oficina; ajustar `disponibilidad.py` y el generador. |
| **V1** dice que las hace el mismo asesor | Se mantiene el modelo actual; reportar la saturación de oficinas pequeñas como hallazgo. |

Con **n tan pequeño**, reporte **conteos** («2 de 5»), nunca porcentajes, y diga que la muestra es por conveniencia y no representa a todo Montería.

## 6. Cómo se cierra #55
- [ ] Entrevista con **I02** hecha, con la plantilla de §4 completa (o con los huecos marcados).
- [ ] Encuestas completadas hasta **8** inmobiliarias, o decisión escrita de cuántas se lograron y por qué (el issue dice «hasta 8»).
- [ ] **I03** aclarada.
- [ ] Resultados **agregados y anónimos** de la ronda 2 añadidos a `resultados/` (nuevo archivo `RESULTADOS_RONDA_2.md`), con n real.
- [ ] ADR-002 **confirmado o reemplazado** según E3, y N fijado según E7.
- [ ] `REQUERIMIENTOS.md` y `CASOS_DE_USO.md` §5 actualizados con las decisiones.

Si **no** se logran las entrevistas, #55 no se cierra con datos inventados: se cierra diciendo cuántas se hicieron, y el informe lo declara y usa los supuestos de `SUPUESTOS_DE_TRABAJO.md` **etiquetados como supuestos**.
