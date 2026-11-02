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

* **Sprints:** [`docs/sprints/SPRINTS.md`](docs/sprints/SPRINTS.md) (tablero) · [Milestones en GitHub](https://github.com/Williamtrix2022/HogarSits/milestones)
* **Decisiones de arquitectura:** [`docs/decisiones/`](docs/decisiones/) · **Notas de aprendizaje:** [`docs/aprendizaje/`](docs/aprendizaje/)
* **Convenciones para Claude Code:** [`CLAUDE.md`](CLAUDE.md)

### Puesta en marcha local

```bash
cp .env.example .env                    # y edita SECRET_KEY
python -m venv venv && venv\Scripts\activate    # Windows
pip install -r requirements/dev.txt
docker compose up -d db                 # PostgreSQL
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver              # http://localhost:8000/admin/
```

Calidad: `ruff check .` · `pytest`. Todo cambio entra por Pull Request con CI verde.

### Estructura

`config/` (settings por entorno) · `apps/{inmuebles,clientes,seguimiento,agenda,analitica}` · `apps/analitica/services/` (Poisson, colas, Markov) · `docs/` · `tests/`
