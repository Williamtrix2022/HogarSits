# HogarSits — Informe final

**Sistema de gestión y análisis de ventas y alquiler de inmuebles**
Procesos Estocásticos · Universidad de Córdoba · 2026
**Equipo:** William Moya Santana (líder), Natalia Durango (requerimientos), Camilo Diaz (desarrollo y BD), Elizabeth Camaño (analista estocástico). Pruebas e informe: equipo compartido.
**Versión:** 0.9 (borrador para revisión del equipo) · **Fecha:** 24-nov-2026 · **Issue:** #43

> **Cómo leer este informe.** Todas las cifras se *midieron* en el repositorio (ver el anexo A para la fuente de cada una). Se distingue tres cosas: lo **demostrado** (pruebas y validaciones reproducibles), lo **simulado** (todo el análisis estocástico se probó con datos simulados) y lo **pendiente** (§9 y §12). La sección 7 está reservada a los resultados con datos reales, que **todavía no existen** porque la segunda ronda de entrevistas no se ha hecho.

---

## 1. Resumen ejecutivo

HogarSits es una aplicación web que une dos cosas: la **gestión diaria** de una inmobiliaria (inmuebles, clientes, solicitudes de atención, agenda de visitas, seguimiento por etapas) y un **análisis estocástico** de su atención: cuándo llegan los clientes (Poisson), cuántos asesores hacen falta (colas M/M/c) y qué porcentaje termina cerrando (cadenas de Markov).

**Qué se logró.**
- El sistema está construido y probado: **700 pruebas automáticas** contra PostgreSQL real (681 pasan, 5 defectos conocidos declarados como `xfail` estricto y 14 pruebas opcionales de rendimiento que pasan), **31 de 31 criterios de aceptación** de 13 historias de usuario con prueba y **98,2 % de cobertura** de código.
- Los tres modelos coinciden con los ejemplos de la Propuesta y con un segundo método de cálculo independiente, y **recuperan sus parámetros** al aplicarlos a datos simulados cuyos valores verdaderos se conocen (1 a 2 % de error en λ, μ y pasos esperados; 2,6 a 6,5 % en la probabilidad de cierre con 120 días).
- La pantalla más lenta responde en **532 ms** con 10 262 solicitudes (el requisito es 3 s).
- Hay una imagen Docker de producción probada en local, un manual de usuario y un sitio de presentación.

**Qué no se logró (y se dice con claridad).**
- **Nunca se probó con datos reales** de una inmobiliaria: la segunda ronda de entrevistas no se hizo. Con 3 inmobiliarias entrevistadas no se puede generalizar.
- **Las esperas que predice M/M/c solo son de orden de magnitud**: la validación mostró que se desvían mucho de la espera simulada porque las visitas sacan a los asesores de la oficina.
- **No está desplegado en AWS** (hay una **demostración en Render**, con datos simulados); no se verificó S3 con un bucket real ni la usabilidad con personas.
- El **historial de etapas no es inmutable** (regla RN-33) y el estado de un inmueble no tiene restricción en la base de datos.

**Conclusión.** Es un **prototipo académico funcional y bien verificado en el código**, cuyo valor para una inmobiliaria real **no está demostrado todavía**: falta el piloto con datos reales (§12).

---

## 2. Problema y contexto

### 2.1 Qué se encontró en la primera ronda (datos reales, n = 3)
Se encuestó a **3 inmobiliarias de Montería** (muestra por conveniencia: son conteos, no porcentajes representativos). Fuente: `docs/investigacion/resultados/RESULTADOS_ENCUESTA.md`.

| Hallazgo | Resultado (de 3) |
|---|---|
| Registran inmuebles en Excel o Hojas de cálculo | 3 |
| Hacen el seguimiento de clientes por WhatsApp manual | 2 (y 1 con hojas de cálculo) |
| Han perdido una solicitud por falta de seguimiento | **3** |
| Han ofrecido un inmueble ya vendido o arrendado | 2 |
| Han tenido visitas cruzadas | 2 |
| Han tenido clientes esperando por falta de asesores | 2 |
| Quieren probar un prototipo / un piloto | 3 / 3 |
| Pagarían sin condiciones | 0 (2 «depende del precio y las funciones», 1 «necesito conocer el producto») |

Carteras de 27 a 80 inmuebles y de 2 a 5 asesores: escala pequeña.

### 2.2 Lo que cambió en el diseño por esos hallazgos
- Como **todas** pierden solicitudes, la alerta «sin seguimiento» subió de prioridad y se construyó «**A quién contactar hoy**» y un recordatorio de visitas.
- Como la **analítica fue lo menos valorado** (el inventario y la agenda van primero), cada resultado del panel se escribe en **lenguaje de negocio**, con la parte técnica plegada.
- Como las visitas de 30 a 120 minutos sacan al asesor de la oficina, **λ se estima por franja horaria** y **c es el número de asesores disponibles** (turno menos los que están en visita), no el total.

---

## 3. Objetivos y su cumplimiento

| # | Objetivo (README) | Evidencia | Estado |
|---|---|---|---|
| 1 | **Gestión operativa** sin duplicidad ni solapamientos | CRUD de inmuebles, clientes, solicitudes y visitas; correo de cliente único; la agenda impide cruces con una restricción de exclusión de PostgreSQL además de la validación en pantalla; 31/31 criterios de aceptación con prueba | ✅ Cumplido |
| 2 | **Poisson:** estimar λ por franja | λ por hora con horas de cero llegadas incluidas, ajuste χ² con clases agrupadas, advertencia de pocos datos (RN-40); recupera λ con 1,7 a 1,9 % de error medio | ✅ Implementado y validado con datos **simulados** |
| 3 | **Colas M/M/c:** ρ, Lq, Wq y asesores recomendados | Erlang C, M/M/1 y M/M/c verificados contra los ejemplos de la Propuesta y contra una cadena de nacimiento y muerte; recomendación del mínimo de asesores | ⚠️ Correcto como matemática; **las esperas son de orden de magnitud** frente a la operación simulada (§6.3) |
| 4 | **Markov:** matriz P, N = (I − Q)⁻¹, absorción y pasos | P(cierre desde Consulta) = 22,748 %, 2,3989 pasos esperados; coincide con las potencias de P | ✅ Implementado y validado con datos **simulados** |

Fases del README: F2 (diseño) y F4 (analítica) **completas**; F1 (requerimientos) completa **salvo la segunda ronda de entrevistas**; F3 (gestión) completa **salvo verificar las fotos en un bucket real**; F5 (pruebas) **completa en lo automatizable**; F6 (despliegue y entrega) **parcial** (§11).

---

## 4. La solución

### 4.1 Funciones
- **Inmuebles:** estados Disponible → Reservado → Vendido/Arrendado, filtros, historial de estado, fotos. Un inmueble cerrado no se puede ofrecer.
- **Clientes y solicitudes:** sin duplicados; la hora de llegada la fija el sistema (de ahí salen las estadísticas); cola con estados En espera, En atención, Finalizado y Cancelado.
- **Seguimiento por etapas:** Consulta → Visita → Negociación → Cierre/Abandono, una etapa a la vez, con historial.
- **Agenda:** visitas sin cruces para el asesor ni para el inmueble; reprogramar y cancelar liberan el horario.
- **Roles:** Administrador y Asesor; el análisis y la administración son solo del administrador, y cada asesor ve únicamente sus indicadores.
- **Análisis:** demanda por hora, esperas según el número de asesores y probabilidad de cierre, con exportación a CSV y datos simulados siempre señalados.

### 4.2 Arquitectura
- **Django 6.1** monolítico en siete aplicaciones (`cuentas`, `comun`, `inmuebles`, `clientes`, `seguimiento`, `agenda`, `analitica`), **PostgreSQL 17**, plantillas con un catálogo de componentes accesibles, gráficos con Chart.js 4.4.7 servido desde el propio dominio.
- **La matemática estocástica son funciones puras** (sin importar Django) en `apps/analitica/services/`, lo que permite probarlas contra ejemplos conocidos sin base de datos (ADR-001).
- **Reglas de integridad en la base de datos**, no solo en pantalla (restricción de exclusión para la agenda, únicos, comprobaciones).
- **Seguridad:** toda vista exige sesión (`LoginRequiredMiddleware`; lo público se marca explícitamente), roles por grupos (ADR-004), bloqueo de 15 minutos tras 5 intentos fallidos, producción que exige HTTPS y rechaza arrancar sin los hosts permitidos.
- **Despliegue:** imagen Docker de producción (gunicorn, WhiteNoise, usuario sin privilegios, 145 MB comprimida) con comprobaciones de salud.

### 4.3 Decisiones de arquitectura
Cuatro ADR en `docs/decisiones/`: stack (001), **autotransiciones de Markov** (002: un «paso» es un seguimiento registrado, y quedarse en la misma etapa también cuenta), modelo de datos (003) y autenticación y roles (004).

---

## 5. Método de trabajo

- **Siete sprints de dos semanas (0 a 6)** con tablero (`docs/sprints/`), milestones e issues en GitHub. Están cerrados el 0, el 2, el 4 y el 5; el **1** y el **3** quedan abiertos por una tarea cada uno que depende de personas (#55, entrevistas; #27, bucket de fotos) y el 6 (pruebas, despliegue, informe y sustentación) está en curso. Los arranques se adelantaron respecto a las fechas propuestas.
- **Una rama y un PR por historia**, commits convencionales y `main` protegida: solo entra con CI verde (`ruff`, `makemigrations --check`, `pytest`, y la construcción de la imagen Docker).
- **Definición de hecho:** pruebas para la lógica nueva y la matemática verificada contra los ejemplos de la Propuesta.
- **Herramientas de apoyo con Claude Code:** un subagente `tester` (escribe pruebas y mantiene una matriz de cobertura de las reglas; encontró el defecto RN-33) y un subagente `revisor-estocastico` de solo lectura con la skill `modelo-estocastico` (segundo par de ojos para la matemática; sus hallazgos se verificaron en el código antes de corregirlos). Sus informes se trataron como datos a comprobar, no como verdad.

---

## 6. Modelos estocásticos: verificación y validación

Hay que distinguir **verificar** (¿el código calcula bien lo que dice?) de **validar** (¿el modelo describe la operación?). Aquí solo se pudo hacer lo primero con rigor, y lo segundo **frente a un simulador**, no frente a la realidad.

### 6.1 Verificación (el código calcula bien)
| Modelo | Ejemplo de referencia | Resultado | Segunda comprobación |
|---|---|---|---|
| M/M/1 | λ = 2, μ = 3 | ρ = 0,667; L = 2; W = 1 h; Lq = 1,333; Wq = 0,667 h | Cadena de nacimiento y muerte |
| M/M/c | 20 clientes en 12 h, 1 cada 45 min | 2 asesores: 28,8 min de espera; 3 asesores: 4,0 min | Cadena de nacimiento y muerte |
| Markov | Matriz P del README | P(cierre) = **22,748 %**; 2,3989 pasos | Potencias de P |

El «≈ 22,8 %» de la Propuesta es un **doble redondeo** (22,748 → 22,75 → 22,8): las pruebas afirman el valor exacto.

### 6.2 Validación frente al simulador
El simulador conoce λ, μ y P verdaderos; se corren sobre sus datos los mismos servicios que usa el panel y se mide el error (20 réplicas por escenario, 120 días; `docs/diseno/VALIDACION_MODELOS.md`).

| Parámetro | Error relativo medio |
|---|---|
| λ por día laboral | 1,5 a 1,9 % |
| μ (clientes/hora por asesor) | 1,6 a 1,7 % |
| Pasos esperados | 1,7 % |
| P(cierre desde Consulta) | **2,6 a 6,5 %** (hasta ~12 % en el percentil 95): la medida más ruidosa |

- **El error baja con más datos:** el de P(cierre) pasa de ~10 % con 30 días a ~5 % con 90 y ~2 % con 300.
- **Con 30 días solo ~51 % de las franjas horarias** tienen las 30 llegadas mínimas (RN-40): el panel avisa.
- **El χ² de Poisson está bien calibrado:** rechaza entre 3,8 y 5,5 % de las veces con datos que sí son Poisson (esperado 5 %).

### 6.3 El hallazgo principal: las esperas de M/M/c no se sostienen
La espera simulada fue de **9,7 min**; el modelo da **0,15, 1,6 o 12,3 min** según cómo se defina el número de asesores. Acierta la **dirección** (más asesores, menos espera), no la **magnitud**.

**Por qué:** M/M/c supone servidores siempre presentes y atención sin interrupciones; en la operación modelada, las visitas de 30 a 120 minutos sacan a los asesores de la oficina, así que c cambia durante el día. El enfoque de «c efectivo por hora» mejora el modelo pero solo lo acerca en un escenario y se vuelve inutilizable cuando alguna hora es inestable.

**Qué se hizo:** el panel presenta las esperas como «orden de magnitud, no un pronóstico», sirven para comparar escenarios («con un asesor más, ¿baja la espera?») y no para prometer minutos. Esto es coherente con la ronda 1: en 2 de las 3 inmobiliarias el modelo con λ diario predecía esperas mucho menores a las reportadas.

### 6.4 Salvedad que no se puede olvidar
La validación demuestra que **el código recupera los supuestos del simulador**. No demuestra que esos supuestos describan una inmobiliaria real. Esa pregunta solo la responden datos reales (§7).

---

## 7. Resultados con datos reales

> ### ⚠️ PENDIENTE — esta sección no se puede escribir todavía
> No hay datos reales de operación: la **segunda ronda de entrevistas** (issue #55) no se ha hecho y las inmobiliarias consultadas dijeron «tal vez» (2) o «no» (1) a compartir historial anonimizado. El guion y los supuestos de trabajo están listos (`docs/investigacion/GUION_RONDA_2.md`, `SUPUESTOS_DE_TRABAJO.md`).
>
> **No se rellena con datos simulados ni inventados.** Cuando existan, esta sección debe contener, como mínimo:
>
> | Qué reportar | Fuente | Cifra real |
> |---|---|---|
> | λ por franja (llegadas/hora) | registros de llegada de la inmobiliaria piloto | *por completar* |
> | μ y tiempo de atención medio | solicitudes finalizadas | *por completar* |
> | Matriz P y P(cierre) | historial de seguimientos | *por completar* |
> | ¿Coincide el modelo de esperas con la espera observada? | espera medida frente a Wq | *por completar* |
> | Usabilidad (tareas, tiempo, errores) | prueba con asesores reales | *por completar* |

---

## 8. Pruebas y calidad

Resumen; el detalle está en `docs/pruebas/INFORME_DE_PRUEBAS.md`.

| Medida | Resultado |
|---|---|
| Pruebas definidas | 700 (681 pasan, 5 `xfail` estrictos, 14 de rendimiento opcionales que pasan) |
| Criterios de aceptación con prueba | 31 de 31 (13 historias) |
| Cobertura | 98,2 % de 3 052 sentencias |
| Rendimiento (RNF-06) | peor pantalla 532 ms con 10 262 solicitudes (límite 3 s) |
| Prueba de punta a punta | jornada completa de 15 pasos por HTTP: **pasa** |

**Errores que las pruebas destaparon y se corrigieron:** reprogramar una visita fallaba con error 500; la búsqueda de teléfonos con espacios; los cierres se contaban por registro y no por solicitud; la exportación de indicadores devolvía 400; el panel creía que no había horarios; textos con gramática torpe; y una revisión independiente de la matemática encontró reservas sobre etiquetas y redondeos que se corrigieron. Un build de producción fallaba por un archivo de terceros. Todos están registrados en el informe de pruebas, con cómo se encontraron.

**La cobertura no es calidad:** se revisaron las líneas sin cubrir una a una y se escribieron pruebas solo donde había lógica real.

**Lo que no se probó:** usabilidad con personas, datos reales, concurrencia real, otros navegadores y dispositivos, despliegue en AWS, HTTPS real, S3 real, copias de seguridad.

---

## 9. Limitaciones y defectos conocidos

| Limitación | Estado | Qué falta |
|---|---|---|
| **Sin datos reales** | Todo el análisis se probó con simulados | Ronda 2 y piloto (§12) |
| **Esperas M/M/c de orden de magnitud** | Documentado en el panel y la validación | Un modelo que incorpore visitas, o aceptar el límite |
| **RN-33:** el historial de etapas se puede editar y borrar | 4 pruebas `xfail(strict)` | Un *trigger* de PostgreSQL (recomendado) |
| **El estado del inmueble no tiene `CHECK` en la BD** | 1 prueba `xfail(strict)` | Una restricción con su migración |
| **Fotos en S3 sin verificar** (#27) | Código probado con almacenamiento local y en memoria | Crear el bucket y correr `probar_almacenamiento` |
| **No está desplegado en AWS** (#45, #46, #47) | Imagen construida y probada en local; **demostración en Render** (capa gratuita, datos simulados, `render.yaml`; la base gratuita caduca a los 30 días) | Credenciales de AWS del equipo |
| **Muestra de entrevistas muy pequeña** | n = 3, por conveniencia | Hasta 8 encuestas (#55) |
| **Concurrencia no ejercitada** | Solo se simula con un parche | Prueba de carga real |

Las pruebas `xfail` son estrictas: cuando alguien arregle un defecto la suite falla hasta quitar la marca, así que **un defecto declarado no puede desaparecer en silencio**.

---

## 10. Lecciones aprendidas

Detalle en `docs/aprendizaje/README.md`. Las más útiles:

**De método**
- **Una expectativa que falla puede estar mal ella, no el código.** Se creyó que mezclar horas con picos siempre hace rechazar a Poisson; una prueba lo corrigió (el índice de dispersión depende de la variación de λ).
- **Verificar no es validar.** Que el código calcule bien M/M/c no significa que M/M/c describa la operación; el simulador lo demostró.
- **Cuatro pruebas por modelo:** ejemplo conocido, comprobación independiente, recuperación de parámetros desde una simulación y casos límite.
- **Redondear al final:** «22,8 %» venía de redondear dos veces.
- **Los informes de subagentes son datos, no verdad:** cada hallazgo se comprobó en el código antes de actuar.

**De proceso**
- **Una restricción en la base de datos no basta para la experiencia:** se detecta el cruce antes de guardar para nombrar la visita en conflicto, y la restricción queda como red de seguridad ante dos asesores simultáneos.
- **Un hallazgo no debe romper el CI:** las reglas aún sin cumplir se declaran `xfail(strict)`.
- **Las capturas reales descubren defectos que las pruebas no ven:** al fotografiar el manual apareció un texto en inglés («Select an option») en los formularios.
- **Un autocorrector necesita una lista explícita de qué toca:** `ruff --fix` modificó código de terceros hasta que se excluyó.
- **Una protección de rama que bloquea es una protección que funciona:** un PR con CI rojo no pudo entrar a `main`, como debía.

**De honestidad**
- Se prefirió **declarar un límite** (esperas, RN-33, sin datos reales) a esconderlo; y se rechazó **simular resultados de entrevistas** para cerrar una tarea.

---

## 11. Gestión del proyecto

- **Sprints 0, 2, 4 y 5 cerrados;** el 1 y el 3 con una tarea pendiente cada uno (#55 y #27) y el 6 en curso. Las fechas del tablero son una propuesta y se adelantaron.
- **Cumplido:** requerimientos, diseño, gestión completa, analítica completa, plan e informe de pruebas, manual de usuario, sitio y guion de sustentación, imagen Docker.
- **Depende de personas o de la cuenta de AWS del equipo:** #55 (entrevistas), #27 (bucket), #45 (subir imagen), #46 y #47 (despliegue y entrega continua), activar GitHub Pages y ensayar la sustentación (#44).

---

## 12. Trabajo futuro (en orden de valor)

1. **Segunda ronda de entrevistas y datos reales** (#55) y **piloto** con una inmobiliaria (la de mayor cartera y asesores): sin esto, el valor del análisis sigue sin demostrarse. Completar la §7.
2. **Hacer inmutable el historial de etapas** (RN-33) con un trigger de PostgreSQL; añadir el `CHECK` del estado del inmueble.
3. **Mejorar el modelo de esperas** incorporando las visitas (por ejemplo, una cola con servidores que se ausentan) y revalidarlo contra datos reales.
4. **Despliegue en AWS** con integración continua sin claves guardadas (OIDC), fotos en S3 verificadas, HTTPS y copias de seguridad.
5. **Usabilidad:** prueba con asesores reales (tiempo y errores en las tareas del manual).
6. **Concurrencia y carga:** prueba con usuarios simultáneos.

---

## Anexo A. Fuente de cada cifra

| Cifra | Documento |
|---|---|
| 700 pruebas, 31/31 criterios, 98,2 %, 532 ms | `docs/pruebas/INFORME_DE_PRUEBAS.md` |
| 1 a 2 %, 2,6 a 6,5 %, 9,7 min frente a 0,15 / 1,6 / 12,3, χ² | `docs/diseno/VALIDACION_MODELOS.md` |
| 3 de 3, 2 de 3, n = 3 | `docs/investigacion/resultados/RESULTADOS_ENCUESTA.md` |
| 22,748 %, 2,3989 pasos, M/M/1 y M/M/c | `docs/requerimientos/CASOS_DE_USO.md`, `tests/test_markov.py`, `tests/test_colas.py` |
| Equipo y objetivos | `README.md` |
| 145 MB, imagen de producción | `docs/aws/IMAGEN_DOCKER.md` |

## Anexo B. Índice de documentos del proyecto
- **Requerimientos:** `docs/requerimientos/` (requerimientos, casos de uso, cobertura de reglas).
- **Diseño:** `docs/diseno/` (ER, wireframes, identidad visual, datos simulados, validación de modelos).
- **Decisiones:** `docs/decisiones/` (ADR-001 a ADR-004).
- **Investigación:** `docs/investigacion/` (encuesta, resultados, guion de la ronda 2, supuestos de trabajo).
- **Pruebas:** `docs/pruebas/` (plan e informe).
- **Manual de usuario:** `docs/manual/MANUAL_DE_USUARIO.md`.
- **Presentación:** `site/` y `docs/presentacion/GUION_SUSTENTACION.md`.
- **Despliegue:** `docs/aws/` (imagen Docker, fotos en S3).
- **Seguimiento:** `docs/sprints/`, `docs/aprendizaje/README.md`.
