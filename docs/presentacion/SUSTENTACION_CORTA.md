# HogarSits — Sustentación (versión corta)

**Sistema en vivo:** https://hogarsits.onrender.com/ · **Sitio de presentación:** https://williamtrix2022.github.io/HogarSits/ · **Código:** https://github.com/Williamtrix2022/HogarSits

## Antes de empezar (5 min antes)
- [ ] **Abra el sistema en vivo y espere a que cargue:** si estaba dormido (capa gratuita) tarda hasta 1 minuto.
- [ ] Entre con `administradora` y compruebe que ve el **Análisis**. (Contraseñas: las que definió al desplegar; no están en el repositorio.)
- [ ] Deje abierta en otra pestaña la sesión de `asesor_demo`, para mostrar los dos roles.
- [ ] Abra el sitio de presentación en una tercera pestaña.

## Qué es (30 s)
Sistema web para una inmobiliaria con **dos pilares**: **gestión** (inmuebles, clientes, solicitudes, agenda sin cruces, etapas) y **análisis estocástico** (Poisson para las llegadas, colas M/M/c para los asesores, Markov para el cierre).

## Demo en vivo (4 min, en este orden)
1. **Inicio:** «A quién contactar hoy» (lo olvidado, primero).
2. **Solicitudes → Nueva solicitud:** la hora de llegada se guarda sola. Tomarla y registrar un seguimiento (una etapa a la vez).
3. **Agenda → Agendar visita:** repita la misma hora con el mismo asesor → **el sistema rechaza el cruce** y dice con cuál.
4. **Administración → Asesores disponibles:** un asesor en visita deja de contar como disponible.
5. **Análisis:** demanda por hora (barras claras = pocos datos), asesores y esperas, probabilidad de cierre. Lea una frase en lenguaje de negocio.
6. **Cambie a `asesor_demo`:** no ve Análisis ni Administración (permiso denegado).

## Matemática (1 min)
Verificada contra los ejemplos de la Propuesta **y** contra un segundo método: M/M/1 (λ=2, μ=3), M/M/c (28,8 min con 2 asesores, 4,0 con 3), Markov **22,748 %** y 2,3989 pasos.

## Calidad (30 s)
**700 pruebas** contra PostgreSQL real · **31/31 criterios** de aceptación · **98,2 %** de cobertura · pantalla más lenta **532 ms** con 10 262 solicitudes · CI obligatorio en cada cambio.

## Dicho con claridad (30 s)
- Los datos de la demo son **simulados**; no se probó con una inmobiliaria real (n = 3 entrevistas en la ronda 1).
- Las **esperas de M/M/c son de orden de magnitud**, no un pronóstico.
- El **historial de etapas aún no es inmutable** (RN-33).
- Despliegue: **demostración en Render** (gratuita). El despliegue en **AWS** (ECR, App Runner, RDS) no se ha verificado.

## Si preguntan
| Pregunta | Respuesta |
|---|---|
| ¿Funciona con datos reales? | No se ha probado; la ronda 2 de entrevistas está preparada pero no se hizo. |
| ¿Por qué 22,748 % y no 22,8 %? | La Propuesta redondeó dos veces; las pruebas usan el valor exacto. |
| ¿Qué es un «paso» de Markov? | Un seguimiento registrado; quedarse en la misma etapa también cuenta (ADR-002). |
| ¿Por qué falla M/M/c en esperas? | Las visitas sacan a los asesores de la oficina; el modelo supone que siempre están. |
| ¿Por qué no está en AWS? | Falta verificar con la cuenta del equipo; hay guías y una imagen Docker lista (`docs/aws/`). |
