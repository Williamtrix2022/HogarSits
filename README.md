# Instrucciones del Proyecto: HogarSits

**Sistema de gestión y análisis de ventas y alquiler de inmuebles para una inmobiliaria**  
*Asignatura: Procesos Estocásticos — Universidad de Córdoba (2026)*

---

## 📋 Resumen del Proyecto

**HogarSits** es una plataforma orientada a resolver la gestión operativa de una inmobiliaria (inmuebles, clientes, citas y transacciones) combinándola con herramientas analíticas avanzadas basadas en **Procesos Estocásticos**. 

El sistema cuenta con dos pilares:
1. **Módulo de Gestión:** Centraliza la base de datos de propiedades, clientes, agendas de visitas y estados de venta/alquiler.
2. **Módulo Analítico:** Aplica modelos estocásticos (Procesos de Poisson, Teoría de Colas y Cadenas de Markov) para estimar la demanda, calcular la capacidad optima del personal de ventas y predecir tasas de conversión de clientes.

---

## 🎯 Objetivos de Desarrollo

1. **Gestión Operativa:** Implementar un CRUD completo para inmuebles, clientes, solicitudes y agendamientos sin duplicidad ni solapamientos de horario.
2. **Modelación de Llegadas (Poisson):** Estimar el parámetro $\lambda$ (llegadas/hora) para analizar los flujos de clientes por franjas horarias.
3. **Teoría de Colas ($M/M/c$):** Determinar la utilización del sistema ($\rho$), la cantidad de clientes en espera ($L_q$) y el tiempo medio de espera ($W_q$) para optimizar la asignación de asesores.
4. **Cadenas de Markov:** Construir matrices de transición $P$ con estados discretos ($\text{Consulta} \to \text{Visita} \to \text{Negociación} \to \text{Cierre} / \text{Abandono}$) y calcular la matriz fundamental $N = (I - Q)^{-1}$ para predecir probabilidades de absorción y tiempo esperado de cierre.

---

## 🛠️ Stack Tecnológico Recomendado

* **Lenguaje Principal:** Python 3.10+
* **Framework Web:** Django (Backend / ORM / Admin)
* **Base de Datos:** PostgreSQL o MySQL
* **Librerías Científicas y Analíticas:** NumPy, SciPy, Pandas
* **Visualización de Datos:** Chart.js / Matplotlib
* **Frontend:** HTML5, CSS3 (Tailwind CSS o Bootstrap), JavaScript
* **Control de Versiones:** Git & GitHub

---

## 👥 Roles y Responsabilidades del Equipo

| Rol | Integrante | Responsabilidades Clave |
| :--- | :--- | :--- |
| **Líder de Proyecto** | William Moya Santana | Coordinar entregables, cronograma y coherencia del sistema. |
| **Analista de Requerimientos** | Natalia Durango | Entrevistas con la inmobiliaria, levantamiento de casos de uso y documentación. |
| **Desarrollador Software / BD** | Camilo Diaz | Modelado Entidad-Relación, desarrollo backend/frontend e integración de la BD. |
| **Analista Estocástico** | Elizabeth Camaño | Construcción de modelos matemáticos (Poisson, Colas, Markov) y validación de parámetros ($\lambda, \mu, P$). |
| **Encargado de Pruebas** | *Equipo Compartido* | Diseño de pruebas funcionales, validación de modelos con datos simulados/reales e informe final. |

---

## 🚀 Guía de Fases e Instrucciones de Trabajo

### Fase 1: Levantamiento e Información
* Realizar entrevistas preliminares para documentar la dinámica actual de atención y ventas de la inmobiliaria.
* Entregable: **Documento de Requerimientos**.

### Fase 2: Diseño de Arquitectura y Base de Datos
* Diseñar el Diagrama Entidad-Relación (ER) incluyendo tablas para: `Inmuebles`, `Clientes`, `Solicitudes`, `Visitas` y `SeguimientoEtapas`.
* Definir las variables clave a capturar en base de datos para los modelos matemáticos (ej. `timestamp_llegada`, `duracion_atencion`, `estado_actual`).
* Entregable: **Diagrama ER y Prototipos UI (Wireframes)**.

### Fase 3: Desarrollo del Módulo de Gestión
* Implementar registro y control de estados de propiedades: *Disponible, Reservado, Vendido, Arrendado*.
* Programar validación lógica en la agenda para evitar solapamientos de asesor e inmueble.
* Entregable: **Módulo de Gestión Funcional (CRUD)**.

### Fase 4: Implementación del Módulo Analítico
* **Proceso de Poisson:** Implementar algoritmos para calcular $\lambda$ histórico y ajustar las curvas de probabilidad $P(X = k) = \frac{e^{-\lambda t}(\lambda t)^k}{k!}$.
* **Teoría de Colas ($M/M/c$):** Calcular las métricas de rendimiento:
  $$\rho = \frac{\lambda}{c\mu}$$
  $$L, L_q, W, W_q$$
* **Cadena de Markov:** 
  1. Construir la matriz $P$ a partir de la frecuencia histórica de transición entre estados: $\{1: \text{Consulta}, 2: \text{Visita}, 3: \text{Negociación}, 4: \text{Cierre}, 5: \text{Abandono}\}$.
  2. Implementar el cálculo de la matriz fundamental $N = (I - Q)^{-1}$ y las probabilidades de absorción.
* Entregable: **Dashboard Analítico con Gráficos e Indicadores**.

### Fase 5: Pruebas, Validación y Documentación
* Ejecutar pruebas con datasets simulados y datos reales.
* Validar la precisión de las estimaciones estocásticas frente a los tiempos/tasas reales observados.
* Entregable: **Informe Final de Pruebas y Sustentación del Proyecto**.

---

## 📐 Especificación de la Cadena de Markov (Ejemplo Modelo)

$$\mathbf{P} = \begin{pmatrix} 
0.20 & 0.50 & 0.00 & 0.00 & 0.30 \\ 
0.00 & 0.15 & 0.45 & 0.00 & 0.40 \\ 
0.00 & 0.00 & 0.20 & 0.55 & 0.25 \\ 
0.00 & 0.00 & 0.00 & 1.00 & 0.00 \\ 
0.00 & 0.00 & 0.00 & 0.00 & 1.00 
\end{pmatrix}$$

* **Estados Transitorios:** Consulta (1), Visita (2), Negociación (3).
* **Estados Absorbentes:** Cierre (4), Abandono (5).
---

## 🧭 Desarrollo y seguimiento

### Estado del proyecto (8-nov-2026)

| Sprint | Fase | Estado |
|---|---|---|
| 0 Fundaciones | — | ✅ Cerrado (7/7) |
| 1 Requerimientos | F1 | 🚧 5/7. Faltan el Budget de AWS (#14) y la segunda ronda de entrevistas (#55) |
| 2 Diseño | F2 | 🚧 4/5. Falta el ADR de Markov (#20), que espera la segunda ronda |
| 3 Gestión, entrega 1 | F3 | 🚧 3/8. Siguen clientes (#28), solicitudes (#29), fotos en S3 (#27) y seguridad del login (#60, #61) |
| 4 a 6 | F3 a F6 | ⏳ Agenda y seguimiento, analítica (Poisson, M/M/c, Markov), pruebas y despliegue en AWS |

**Ya funciona:** inicio de sesión con roles (Administrador y Asesor), administración de usuarios, gestión de inmuebles (lista con búsqueda y filtros, alta, edición, historial de estado, desactivar), generador de datos simulados y una interfaz con la identidad visual de HogarSits.
**En construcción:** clientes, solicitudes de atención, agenda de visitas, seguimiento de etapas y el módulo analítico.
**Calidad:** 152 pruebas automáticas sobre PostgreSQL; el CI de GitHub las corre en cada Pull Request.

### Documentación

Todo está indexado en [`docs/README.md`](docs/README.md). Lo principal:

* **Tablero de sprints:** [`docs/sprints/SPRINTS.md`](docs/sprints/SPRINTS.md) y [milestones en GitHub](https://github.com/Williamtrix2022/HogarSits/milestones)
* **Requerimientos y estado de implementación:** [`docs/requerimientos/REQUERIMIENTOS.md`](docs/requerimientos/REQUERIMIENTOS.md)
* **Diseño:** [modelo de datos](docs/diseno/ER.md) · [wireframes](docs/diseno/WIREFRAMES.md) · [identidad visual](docs/diseno/IDENTIDAD_VISUAL.md)
* **Decisiones de arquitectura:** [`docs/decisiones/`](docs/decisiones/README.md) · **Aprendizaje:** [`docs/aprendizaje/`](docs/aprendizaje/README.md)
* **Convenciones para Claude Code:** [`CLAUDE.md`](CLAUDE.md)

### Puesta en marcha local

Requiere Python 3.14, Docker Desktop y Git.

```powershell
copy .env.example .env                  # y edita SECRET_KEY
python -m venv venv
venv\Scripts\Activate.ps1               # PowerShell (en cmd: venv\Scripts\activate)
pip install -r requirements/dev.txt
docker compose up -d db                 # PostgreSQL en el puerto 5433 del equipo
python manage.py migrate
python manage.py createsuperuser        # será tu usuario Administrador
python manage.py seed_datos_simulados   # opcional: datos de prueba (--limpiar los borra)
python manage.py runserver              # http://localhost:8000/ingresar/
```

> El contenedor usa el puerto **5433** porque el 5432 suele estar ocupado por un PostgreSQL instalado en el equipo. Las pruebas necesitan que la base esté encendida (`docker compose up -d db`).

### Calidad y flujo de trabajo

```powershell
ruff check .                                 # estilo
pytest                                       # pruebas (necesitan PostgreSQL)
python manage.py makemigrations --check --dry-run
```

`main` está protegida: todo cambio entra por **Pull Request** con el CI en verde, una rama por historia (`feature/<n>-descripcion`) y `Closes #n` en la descripción.

### Estructura

* `config/`: configuración por entorno (`base`, `dev`, `prod`)
* `apps/cuentas` (acceso, roles, menú) · `apps/comun` (utilidades compartidas) · `apps/inmuebles` · `apps/clientes` · `apps/seguimiento` · `apps/agenda` · `apps/analitica` (con `services/` para Poisson, colas y Markov)
* `templates/` y `static/`: interfaz (componentes en `templates/componentes/`; guía viva en `/administracion/componentes/`)
* `docs/` documentación · `tests/` pruebas
