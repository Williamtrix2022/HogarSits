> **Documento histórico (17-nov-2026).** Describe el avance de ese día (152 pruebas, Sprint 3) y ya no es vigente. Para la sustentación use [`GUION_SUSTENTACION.md`](GUION_SUSTENTACION.md) y el sitio `site/`; el estado real está en `docs/sprints/SPRINTS.md` y `docs/pruebas/INFORME_DE_PRUEBAS.md`.

# HogarSits — Guion de exposición de avance

**Verificado el 17-nov-2026** (código sin cambios desde el 8-nov): 152 pruebas pasan, el lint está limpio, las migraciones están al día y el servidor arranca. Repositorio: https://github.com/Williamtrix2022/HogarSits

## 1. En 30 segundos
HogarSits es un sistema web para una inmobiliaria con **dos pilares**: (1) **gestión** de inmuebles, clientes, solicitudes y visitas, y (2) **análisis estocástico** de la atención (Poisson para las llegadas, colas M/M/c para los asesores, cadenas de Markov para el avance del cliente). Llevamos construida **la base de gestión y un simulador de datos para validar los modelos**; el módulo analítico es el siguiente tramo.

## 2. Dónde vamos
**Por calendario** propuesto, hoy estamos en el **Sprint 1** (16 al 29 de noviembre). **Por trabajo realizado** nos adelantamos: hay avances hasta el **Sprint 3**.

| Sprint | Fase | Estado | Qué contiene |
|---|---|---|---|
| 0 Fundaciones | — | ✅ 7/7 | Proyecto Django ordenado, PostgreSQL con Docker, CI, tablero de sprints |
| 1 Requerimientos | F1 | 5/7 | Requerimientos, casos de uso, encuesta, backlog. **Faltan** el Budget de AWS y la 2.ª ronda de entrevistas |
| 2 Diseño | F2 | 4/5 | Modelo de datos, wireframes, identidad visual, datos simulados. **Falta** el ADR de Markov |
| 3 Gestión (entrega 1) | F3 | 3/8 | Acceso con roles, interfaz base, inmuebles. **Faltan** clientes, solicitudes, fotos y 2 mejoras de seguridad |
| 4 Gestión (entrega 2) | F3 | ⏳ | Agenda sin cruces, seguimiento de etapas |
| 5 Analítica | F4 | ⏳ | Poisson, M/M/c, Markov y dashboard |
| 6 Pruebas, AWS, entrega | F5-F6 | ⏳ | Validación, informe, despliegue |

## 3. Lo que ya está hecho
**Investigación.** Documento de requerimientos (RF/RNF, 13 historias de usuario), casos de uso y reglas de negocio, instrumento de encuesta y **primera ronda con 3 inmobiliarias**. Hallazgos: las 3 trabajan con Excel y WhatsApp y las 3 han perdido solicitudes por falta de seguimiento; lo que más valoran es el inventario y la agenda, **lo menos valorado fue la analítica**; dos de las tres esperarían pagar entre $50.000 y $100.000 al mes.

**Diseño.** Modelo entidad-relación con las reglas **garantizadas por la base de datos** (no solo por la pantalla): una visita no puede cruzarse con otra del mismo asesor o inmueble, los tiempos deben cumplir `llegada ≤ inicio ≤ fin`, una venta no puede quedar «Arrendada», el correo de un cliente es único, Cierre y Abandono no tienen salida. 14 wireframes, identidad visual con contrastes AA y plan de movimiento.

**Software que funciona hoy.**
- Inicio de sesión con roles **Administrador** y **Asesor**; toda pantalla exige sesión por defecto.
- Administración de usuarios (crear, editar, activar y desactivar) con salvaguardas.
- **Gestión de inmuebles:** lista con búsqueda y filtros (estado, operación, tipo, rango de precio), paginación, alta y edición con el precio escrito como en Colombia (`240.000.000`), **historial de cada cambio de estado**, desactivar en lugar de borrar.
- Interfaz con la marca: menú lateral que **muestra solo las secciones que ya existen**, avisos, formularios accesibles, modo móvil.
- **Generador de datos simulados** (llegadas Poisson con picos de mañana y tarde, atención con varios asesores, visitas que ocupan al asesor, cadena de Markov): sus pruebas recuperan los valores de la Propuesta (**22,8 % de cierre y 2,4 pasos** hasta la absorción).

**Calidad y proceso.** 152 pruebas automáticas contra PostgreSQL real; CI en GitHub Actions en cada cambio; `main` protegida (todo entra por Pull Request con CI verde); 17 PR mergeados, 49 issues, más de 25 documentos con índice.

## 4. Cifras
| | |
|---|---|
| Commits en `main` | 18 |
| Pull Requests mergeados | 17 |
| Issues | 19 cerrados, 30 abiertos (el resto del backlog, ya planificado) |
| Pruebas automáticas | **152** (todas pasan) |
| Código de aplicación / de pruebas | ~1.900 / ~1.400 líneas de Python |
| Modelos / migraciones | 4 apps con modelos / 9 migraciones |
| Encuestas | 3 inmobiliarias de Montería (meta: 8 a 15) |

## 5. Cómo correr el proyecto (antes de exponer)
1. **Enciende Docker Desktop** y espera a que diga «Engine running».
2. En la terminal de VS Code, dentro de la carpeta del proyecto:

```powershell
venv\Scripts\Activate.ps1
docker compose up -d db                  # PostgreSQL (puerto 5433)
python manage.py migrate                 # no hace nada si ya está al día
python manage.py runserver               # deja esta terminal abierta
```
3. Abre **http://localhost:8000/ingresar/**.
4. **Usuario:** `williammoya` (también existe `William`). **Contraseña:** la que definiste. Si no la recuerdas, en otra terminal: `python manage.py changepassword williammoya`.

Tu base local ya tiene **datos de demostración**: 40 inmuebles, 286 clientes, 310 solicitudes, 607 transiciones de etapa y 167 visitas simulados. *No ejecutes `seed_datos_simulados --limpiar` antes de exponer: los borra.*

Si algo falla: Docker apagado → enciéndelo y repite el paso 2; puerto 8000 ocupado → `python manage.py runserver 8001`; la pantalla se ve sin estilos → recarga con `Ctrl + F5`; las fuentes necesitan internet (sin conexión se ven con la tipografía del sistema, funciona igual).

## 6. Demostración sugerida (7 a 8 minutos)
| Min | Qué mostrar | Qué decir |
|---|---|---|
| 0-1 | **Inicio de sesión** | El plano de la casa se dibuja y se abre la puerta (solo la primera vez por navegador). Toda pantalla exige sesión. |
| 1-2 | **Hogar y menú** | El menú solo muestra lo que existe: cada sprint «enciende» su sección sola. |
| 2-4 | **Inmuebles** | 40 inmuebles; filtrar por `Venta` y precio desde `100.000.000`; buscar «mocarí». Crear uno con precio `240.000.000`. Probar el error: precio `0` → aparece el **resumen de errores** con enlaces a cada campo. Cambiar el estado a «Reservado» y mostrar el **historial** al final de la ficha. |
| 4-5 | **Roles** | Administración → crear un asesor nuevo (por ejemplo `demo1`; ya existe `Asesor1`, úsalo solo si recuerdas su contraseña). En una ventana privada entrar como ese asesor: no ve «Administración», y si abre `/administracion/usuarios/` a mano recibe «solo para administradores». |
| 5-6 | **Calidad** | `pytest tests/test_simulacion.py -q`: el simulador recupera 22,8 % y 2,4 pasos de la Propuesta. Mostrar el CI verde en GitHub. |
| 6-8 | **GitHub y documentación** | Tablero de milestones, un PR con su CI, `docs/README.md`, el diagrama ER y los wireframes. |

## 7. Lo que falta (decirlo con claridad)
- **El núcleo analítico aún no está implementado:** las funciones de Poisson (λ por franja), colas M/M/c (ρ, L, Lq, W, Wq) y Markov (matriz fundamental) son el **Sprint 5**. Hoy existen el simulador, los modelos de datos que los alimentan y los valores de referencia ya verificados.
- Clientes, solicitudes de atención, agenda de visitas y seguimiento de etapas (Sprints 3 y 4).
- **Muestra pequeña:** n = 3, así que los hallazgos orientan pero no generalizan. Falta la 2.ª ronda y datos reales (el desarrollo usa datos simulados).
- AWS: hay cuenta con MFA y usuario IAM; **falta el Budget de 1 USD** antes de crear recursos. El despliegue es el Sprint 6.
- Seguridad: falta limitar los intentos fallidos de inicio de sesión y que cada usuario cambie su contraseña.

## 8. Preguntas probables
- **¿Por qué datos simulados?** Todavía no hay datos reales autorizados. El simulador usa parámetros conocidos (λ, μ, P) para **validar que los modelos los recuperan** antes de usarlos con una inmobiliaria.
- **¿Cómo se sabe que los modelos estarán bien?** Hay valores de referencia de la Propuesta (M/M/1 con λ=2, μ=3 → ρ≈0,67; P de cierre 22,8 %) y el simulador ya los reproduce; el Sprint 5 los implementa con las mismas pruebas.
- **¿Por qué PostgreSQL y no SQLite?** Las reglas de agenda (sin cruces) se garantizan con una restricción de PostgreSQL; además es lo que se usará en AWS.
- **¿Qué hallaron en la encuesta que cambió el diseño?** Que las visitas **sacan al asesor de la oficina**: por eso modelamos su horario y su disponibilidad, y no solo el número de asesores.
- **¿El modelo de colas funciona con datos reales?** Con 3 inmobiliarias acertó en una (29 min estimados frente a 30 reportados) y no en las otras dos; lo documentamos como limitación y lo revisaremos con la 2.ª ronda.
- **¿Qué herramientas usaron?** Django y PostgreSQL, Docker Compose, GitHub (issues, milestones, Pull Requests y Actions para el CI) y Claude Code con skills de diseño para la interfaz.
- **¿Cómo se organiza el trabajo?** Sprints de 2 semanas ligados a las 6 fases de la Propuesta, con el tablero en `docs/sprints/` y los issues en GitHub.
