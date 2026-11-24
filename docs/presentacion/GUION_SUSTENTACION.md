# HogarSits — Guion de sustentación

Duración sugerida: **12 minutos** de exposición + **5 de preguntas**. Apoyo visual: el sitio `site/` (navegar con ← →). Todas las cifras salen de `docs/pruebas/INFORME_DE_PRUEBAS.md`, `docs/diseno/VALIDACION_MODELOS.md` y `docs/investigacion/resultados/RESULTADOS_ENCUESTA.md`.

## Reparto sugerido
| Tramo | Min | Quién (según su rol) | Sección del sitio |
|---|---|---|---|
| Problema y encuesta | 2 | Natalia Durango | Problema |
| Qué hace el sistema + demo | 3 | Camilo Diaz | Qué hace |
| Modelos y validación | 4 | Elizabeth Camaño | Análisis, Matemática |
| Calidad, límites, siguientes pasos | 3 | William Moya Santana | Calidad, Límites |

## Guion
1. **(0:00) Portada.** «HogarSits: gestión y análisis para inmobiliarias, con tres modelos estocásticos.»
2. **(0:30) Problema.** Tres inmobiliarias entrevistadas, las tres con Excel y WhatsApp, las tres han perdido solicitudes por falta de seguimiento. *Decir:* es una muestra por conveniencia de 3; son conteos, no porcentajes.
3. **(2:00) Demo en vivo** (con `seed_datos_simulados`, entrando como administrador). Orden: inicio «A quién contactar hoy» → detalle de una solicitud → agenda (intentar crear una visita que se cruce: el sistema la rechaza) → asesores disponibles. *Decir:* los datos son simulados.
4. **(5:00) Análisis.** Mostrar el panel: demanda (barras claras = pocos datos), esperas, probabilidad de cierre. Leer en voz alta una de las frases en lenguaje de negocio.
5. **(7:00) Matemática.** Ejemplos de referencia (M/M/1 λ=2, μ=3; M/M/c con 20 clientes en 12 h y 45 min de servicio: 28,8 min con 2 asesores, 4,0 con 3; Markov 22,748 %, 2,3989 pasos).
6. **(9:00) Validación y hallazgo incómodo.** Parámetros recuperados con 1–2 % de error; P(cierre) 2,6–6,5 %; las esperas de M/M/c solo son orden de magnitud.
7. **(10:30) Límites** (leerlos sin esconderlos) y **siguientes pasos**.

## Preguntas probables y respuesta honesta
- **¿Con datos reales funciona?** No lo sabemos: se probó con datos simulados. La ronda 2 de entrevistas está preparada (`GUION_RONDA_2.md`) pero no se hizo. Con 30 días de datos el error de P(cierre) ronda 10 %; con 300 días, 2 %.
- **¿Por qué la espera del modelo no coincide con la simulada?** M/M/c supone asesores siempre presentes; las visitas (30–120 min) los sacan de la oficina, así que c cambia durante el día. Se aproxima con c efectivo por hora, pero solo acierta en orden de magnitud y el panel lo avisa.
- **¿Por qué 22,748 % si la Propuesta dice 22,8 %?** La Propuesta redondeó dos veces (22,748 → 22,75 → 22,8). Las pruebas afirman el valor exacto.
- **¿Qué es un «paso» de Markov?** Un seguimiento registrado (ADR-002); quedarse en la misma etapa también cuenta.
- **¿Está desplegado en AWS?** No. La imagen Docker de producción se construye y se probó localmente (salud, redirección HTTPS, base caída y recuperada). La subida a ECR, el despliegue y S3 real no se han verificado contra una cuenta de AWS.
- **¿Qué falla hoy?** El historial de etapas no es inmutable (RN-33, 4 pruebas `xfail` lo declaran) y el estado de un inmueble no tiene restricción en la base de datos (1 `xfail`).
- **¿Cobertura 98,2 % significa que no hay errores?** No; por eso se revisaron las líneas sin cubrir y se documentó lo que no se puede probar (concurrencia real, usabilidad).
- **¿Se probó con usuarios?** No todavía; falta el piloto.

## Antes de presentar
- [ ] `docker compose up -d db`, `python manage.py seed_datos_simulados` y entrar como administrador.
- [ ] Abrir el sitio (GitHub Pages o `site/index.html` local) y probar ← →.
- [ ] Ensayar con cronómetro; no pasar de 12 minutos.
