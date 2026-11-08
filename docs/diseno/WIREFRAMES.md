# HogarSits — Wireframes y flujos de navegación

**Versión:** 0.1 · **Fecha:** 2026-11-08 · **Sprint:** 2 · **Issue:** #21
**Insumos:** [`REQUERIMIENTOS.md`](../requerimientos/REQUERIMIENTOS.md) v0.2 (HU-01 a HU-13), [`CASOS_DE_USO.md`](../requerimientos/CASOS_DE_USO.md), [`IDENTIDAD_VISUAL.md`](IDENTIDAD_VISUAL.md), [`RESULTADOS_ENCUESTA.md`](../investigacion/resultados/RESULTADOS_ENCUESTA.md).

Son **bocetos de baja fidelidad** hechos con Mermaid (se ven en GitHub y se versionan con el código). Muestran **estructura, contenido y acciones**, no el aspecto final: colores, tipografía y espaciado se definen al implementar con la guía de identidad visual (#25).

## 1. Principios de diseño (salen de la encuesta)

| Hallazgo | Decisión de interfaz |
|---|---|
| 3/3 han perdido solicitudes por falta de seguimiento | La **pantalla de inicio es «a quién contactar hoy»**, no un menú. |
| El inventario es lo más valioso; la agenda, lo segundo | «Inmuebles» y «Agenda» son accesos de primer nivel y se pueden usar sin pasar por Análisis. |
| La analítica fue lo menos valorado | Cada cifra de **Análisis** lleva una frase en lenguaje de negocio (RF-59); nada de «λ» o «P» sin explicación. |
| «Fácil de usar, sin conocimientos técnicos» | Un objetivo por pantalla, formularios cortos, mensajes de error que dicen **qué hacer**. |
| Escala pequeña (2–5 asesores, 27–80 inmuebles) | Listas con filtros simples; sin paginación compleja ni tableros recargados. |
| El estado no se comunica solo con color | Chips con **punto + texto** (Disponible · Reservado · Vendido/Arrendado). |

**Convenciones de los bocetos:** bloque azul oscuro = marca / acción primaria · bloque beige = aviso · bloque blanco = contenido · borde rojo = error. Los textos de ejemplo son ficticios.

## 2. Estructura general (todas las pantallas)

```mermaid
block-beta
  columns 5
  top["HogarSits (logo) · Buscar · Asesor ▾"]:5
  block:nav:1
    columns 1
    n1["Hogar"]
    n2["Inmuebles"]
    n3["Clientes"]
    n4["Solicitudes"]
    n5["Agenda"]
    n6["Análisis"]
    n7["Administración (solo admin)"]
  end
  main["Área de contenido: título de la pantalla, acciones primarias a la derecha, filtros arriba, contenido debajo"]:4
  style top fill:#001F5B,color:#ffffff,stroke:#001F5B
  style n1 fill:#E6EBF4,color:#001F5B,stroke:#001F5B
  style main fill:#ffffff,stroke:#4A4A4A
```
- Menú lateral fijo en escritorio; en teléfono se colapsa en un botón. El ítem activo se resalta.
- El asesor **no ve** «Administración» ni los indicadores de otros asesores (RF-03, HU-13).

## 3. Mapa del sitio y roles

```mermaid
flowchart LR
    L[Iniciar sesión] --> H[Hogar: a quién contactar hoy]
    H --> I[Inmuebles]
    H --> C[Clientes]
    H --> S[Solicitudes]
    H --> A[Agenda]
    H --> AN[Análisis]
    H --> AD[Administración]

    I --> I1[Lista y filtros]
    I1 --> I2[Ficha / formulario del inmueble]
    I2 --> I3[Fotos]
    I2 --> I4[Historial de estado]

    C --> C1[Lista y búsqueda]
    C1 --> C2[Ficha del cliente y sus solicitudes]

    S --> S1[Cola de atención]
    S --> S2[Nueva solicitud]
    S1 --> S3[Detalle: seguimiento y etapas]
    S3 --> A2[Nueva visita]

    A --> A1[Agenda semanal por asesor]
    A1 --> A2

    AN --> AN1[Demanda por hora]
    AN --> AN2[Asesores y esperas]
    AN --> AN3[Probabilidad de cierre]
    AN --> AN4[Indicadores por asesor]

    AD --> AD1[Usuarios]
    AD --> AD2[Horarios de asesores]

    classDef solo_admin fill:#F3E6DA,stroke:#8F5622,color:#4A4A4A
    class AD,AD1,AD2,AN1,AN2,AN3 solo_admin
```

| Zona | Administrador | Asesor |
|---|---|---|
| Hogar, Inmuebles, Clientes, Solicitudes, Agenda | ✅ | ✅ (Agenda: la propia y la de consulta) |
| Análisis: demanda, asesores, probabilidad de cierre | ✅ | — |
| Análisis: indicadores por asesor | todos | solo los propios |
| Administración (usuarios, horarios) | ✅ | — |

## 4. Flujos clave

### 4.1 Del cliente que llega a la solicitud atendida (CU-04, CU-05, CU-06)
```mermaid
flowchart TD
    A([Llega un cliente]) --> B[Nueva solicitud: buscar cliente por correo o teléfono]
    B --> C{¿Ya existe?}
    C -- Sí --> D[Seleccionar cliente existente]
    C -- No --> E[Crear cliente: nombre, correo, teléfono]
    E --> F{¿Correo duplicado?}
    F -- Sí --> G[Aviso: mostrar el cliente existente] --> D
    F -- No --> H
    D --> H[Interés compra/alquiler, presupuesto, inmueble opcional]
    H --> I{¿Inmueble vendido o arrendado?}
    I -- Sí --> J[Error: elegir otro inmueble] --> H
    I -- No --> K[Guardar: queda EN ESPERA, la hora de llegada la pone el sistema]
    K --> L[Cola de atención]
    L --> M[Asesor pulsa Tomar: EN ATENCIÓN]
    M --> N[Asesor pulsa Finalizar: FINALIZADO]
    L --> O[Cliente se va: CANCELADO]
```

### 4.2 Agendar una visita sin cruces (CU-07)
```mermaid
sequenceDiagram
    actor Asesor
    participant UI as Formulario Nueva visita
    participant SV as Servicio de agenda
    participant BD as PostgreSQL
    Asesor->>UI: elige solicitud, inmueble, fecha, hora y duración
    UI->>SV: validar (inmueble disponible, asesor libre)
    alt hay cruce o inmueble cerrado
        SV-->>UI: mensaje con el horario en conflicto y alternativas
        UI-->>Asesor: aviso en beige, sin perder lo escrito
    else todo libre
        SV->>BD: guardar visita
        alt otra persona reservó ese hueco un instante antes
            BD-->>SV: rechaza por restricción de cruce
            SV-->>UI: mismo aviso de conflicto
        else guardada
            BD-->>UI: visita PROGRAMADA
            UI-->>Asesor: confirmación y recordatorio creado
        end
    end
```

### 4.3 Cambio de etapa (CU-08)
```mermaid
flowchart LR
    C[Consulta] --> V[Visita] --> N[Negociación] --> Z[Cierre]
    C --> X[Abandono]
    V --> X
    N --> X
    Z -.-> P[Propone marcar el inmueble Vendido o Arrendado]
    classDef final fill:#E6EBF4,stroke:#001F5B,color:#001F5B
    class Z,X final
```
Solo se ofrecen en pantalla las etapas permitidas desde la actual; Cierre y Abandono no admiten más cambios. *(Cómo se registra «seguir en la misma etapa» depende de ADR-002, pendiente de la ronda 2.)*

## 5. Pantallas

### W1 · Inicio de sesión — RF-01
```mermaid
block-beta
  columns 3
  space logo["Logo HogarSits · Gestión y Análisis Inmobiliario"] space
  space card["Iniciar sesión"] space
  space user["Usuario"] space
  space pass["Contraseña"] space
  space err["Usuario o contraseña incorrectos. Revise e intente de nuevo."] space
  space btn["Entrar"] space
  style logo fill:#ffffff,stroke:#ffffff
  style card fill:#ffffff,stroke:#001F5B
  style err fill:#ffffff,stroke:#B3261E,color:#B3261E
  style btn fill:#001F5B,color:#ffffff
```
Acciones: *Entrar*. Sin sesión no se accede a ninguna otra pantalla. El mensaje de error no revela si falló el usuario o la contraseña.

### W2 · Hogar: a quién contactar hoy — HU-12, RF-25, RF-26, RF-35
```mermaid
block-beta
  columns 3
  title["Hogar · Buenos días, Ana"]:3
  k1["En espera: 2"] k2["Visitas hoy: 3"] k3["Sin seguimiento: 5"]
  block:izq:2
    columns 1
    l0["A quién contactar hoy"]
    l1["Pedro R. · Consulta · sin respuesta hace 4 días · Llamar"]
    l2["María G. · Visita · sin respuesta hace 6 días · Escribir"]
    l3["Luis F. · Negociación · hace 3 días · Llamar"]
    l4["Ver las 5 pendientes"]
  end
  block:der:1
    columns 1
    v0["Mis visitas"]
    v1["Hoy 10:00 · Casa 12, Cantaclaro"]
    v2["Hoy 15:30 · Apto 4, Centro"]
    v3["Mañana 09:00 · Casa 7, Mocarí"]
  end
  style title fill:#001F5B,color:#ffffff
  style k3 fill:#F3E6DA,stroke:#8F5622
  style l0 fill:#E6EBF4,color:#001F5B
  style v0 fill:#E6EBF4,color:#001F5B
```
Datos: solicitudes del asesor con seguimiento pendiente ordenadas por antigüedad; marca beige las que superan N días (N configurable, pendiente de E7). Acciones: abrir la solicitud, registrar el contacto. Vacío: «Todo al día. No tiene seguimientos pendientes.» El administrador ve el total del equipo y puede filtrar por asesor.

### W3 · Inmuebles: lista y filtros — HU-01, RF-14
```mermaid
block-beta
  columns 4
  title["Inmuebles"]:3 add["+ Nuevo inmueble"]
  f1["Buscar: título, dirección o barrio"] f2["Estado ▾"] f3["Operación ▾"] f4["Precio: de — a"]
  h1["Inmueble"] h2["Operación / Tipo"] h3["Precio"] h4["Estado"]
  r1["Casa 12 · Cantaclaro"] r2["Venta · Casa"] r3["$ 240.000.000"] r4["● Disponible"]
  r5["Apto 4 · Centro"] r6["Alquiler · Apartamento"] r7["$ 1.300.000"] r8["● Reservado"]
  r9["Casa 7 · Mocarí"] r10["Venta · Casa"] r11["$ 310.000.000"] r12["● Vendido"]
  style title fill:#001F5B,color:#ffffff
  style add fill:#001F5B,color:#ffffff
  style h1 fill:#E6EBF4,color:#001F5B
  style h2 fill:#E6EBF4,color:#001F5B
  style h3 fill:#E6EBF4,color:#001F5B
  style h4 fill:#E6EBF4,color:#001F5B
```
Chips de estado: punto verde (Disponible), cobre (Reservado), gris (Vendido/Arrendado), siempre con texto. Los inmuebles desactivados no aparecen salvo con el filtro «Incluir inactivos». Vacío: «No hay inmuebles con esos filtros. Quite algún filtro o cree uno nuevo.»

### W4 · Ficha / formulario de inmueble — RF-10, RF-11, RF-12, RF-13
```mermaid
block-beta
  columns 4
  title["Inmueble: Casa 12 · Cantaclaro"]:3 save["Guardar"]
  a["Título"] b["Tipo ▾: Casa / Apartamento"] c["Operación ▾: Venta / Alquiler"] d["Precio"]
  e["Dirección"]:2 f["Barrio"] g["Área m²"]
  h["Habitaciones"] i["Estado ▾"] j["Activo ☑"] space
  k["Descripción"]:4
  l["Fotos: [ + Agregar ]   [foto 1]  [foto 2]  [foto 3]"]:4
  m["Historial de estado: 02-nov Disponible → Reservado (Ana) · 05-nov Reservado → Vendido (Luis)"]:4
  style title fill:#001F5B,color:#ffffff
  style save fill:#001F5B,color:#ffffff
  style m fill:#ffffff,stroke:#4A4A4A
```
Reglas visibles: un alquiler no puede quedar «Vendido» ni una venta «Arrendada» (el estado solo ofrece opciones coherentes); el precio debe ser mayor que 0; «Desactivar» reemplaza a «Eliminar» (el historial se conserva). Cada cambio de estado queda en el historial con usuario y fecha.

### W5 · Nueva solicitud (con búsqueda y control de duplicados) — HU-03, HU-04
```mermaid
block-beta
  columns 3
  title["Nueva solicitud de atención"]:3
  s1["1. Cliente: buscar por correo o teléfono"]:2 s2["Buscar"]
  dup["Ya existe un cliente con ese correo: Pedro Ramírez (300 123 4567). ¿Usar este cliente?"]:3
  c1["Nombre"] c2["Correo"] c3["Teléfono"]
  p1["2. Interés ▾: Compra / Alquiler"] p2["Presupuesto (opcional)"] p3["Inmueble de interés (opcional) ▾"]
  note["La hora de llegada se registra automáticamente al guardar."]:3
  cancel["Cancelar"] save["Guardar solicitud"]:2
  style title fill:#001F5B,color:#ffffff
  style dup fill:#F3E6DA,stroke:#8F5622
  style save fill:#001F5B,color:#ffffff
```
El aviso beige aparece al detectar un correo existente (sin distinguir mayúsculas). El inmueble solo lista los **no vendidos/arrendados**. Al guardar: solicitud *En espera* y etapa *Consulta*.

### W6 · Cola de atención — HU-04
```mermaid
block-beta
  columns 3
  title["Solicitudes · Cola de atención"]:2 add["+ Nueva solicitud"]
  tabs["En espera (2) · En atención (1) · Finalizadas · Canceladas"]:3
  h1["Cliente / interés"] h2["Llegó · espera"] h3["Acción"]
  r1["Pedro R. · Compra · Casa 12"] r2["10:05 · 12 min"] r3["Tomar"]
  r4["Sofía M. · Alquiler"] r5["10:12 · 5 min"] r6["Tomar"]
  r7["Camilo D. · Compra (atiende Ana)"] r8["inició 09:50"] r9["Finalizar"]
  style title fill:#001F5B,color:#ffffff
  style add fill:#001F5B,color:#ffffff
  style r3 fill:#001F5B,color:#ffffff
  style r6 fill:#001F5B,color:#ffffff
  style r9 fill:#001F5B,color:#ffffff
```
*Tomar* asigna el asesor y guarda la hora de inicio; *Finalizar* guarda la hora de fin (debe ser posterior al inicio). La espera se calcula sola (inicio − llegada) y alimenta el análisis de colas.

### W7 · Agenda semanal por asesor — RF-34
```mermaid
block-beta
  columns 6
  title["Agenda"]:4 week["◀ Semana 2–8 mar ▶"] add["+ Nueva visita"]
  filt["Asesor ▾: Ana"]:6
  hh["Hora"] d1["Lun"] d2["Mar"] d3["Mié"] d4["Jue"] d5["Vie"]
  h9["09:00"] a1["Casa 12 · Pedro R."] a2["—"] a3["—"] a4["Apto 4 · Sofía M."] a5["—"]
  h10["10:00"] b1["Casa 12 · Pedro R."] b2["Casa 7 · Luis F."] b3["—"] b4["—"] b5["—"]
  h15["15:00"] c1["—"] c2["—"] c3["Casa 3 · Ana L."] c4["—"] c5["Apto 9 · Raúl P."]
  style title fill:#001F5B,color:#ffffff
  style add fill:#001F5B,color:#ffffff
  style a1 fill:#E6EBF4,stroke:#001F5B
  style b1 fill:#E6EBF4,stroke:#001F5B
```
Muestra también los turnos del asesor (horas fuera de turno en gris). Las visitas canceladas no ocupan casilla. Clic en una visita: ver, reprogramar, cancelar o marcar como realizada.

### W8 · Nueva visita con aviso de cruce — HU-05, RN-01, RN-02
```mermaid
block-beta
  columns 3
  title["Nueva visita"]:3
  a["Solicitud ▾: Pedro R. · Casa 12"] b["Asesor ▾: Ana"] c["Inmueble ▾"]
  d["Fecha"] e["Hora de inicio"] f["Duración ▾: 30 · 45 · 60 · 90 · 120 min"]
  err["No se puede agendar: Ana ya tiene una visita de 10:00 a 11:00 (Casa 12 con Pedro R.). Pruebe a las 11:00 o elija otro asesor."]:3
  alt["Horarios libres hoy para Ana: 11:00 · 11:30 · 15:00"]:3
  cancel["Cancelar"] save["Guardar visita"]:2
  style title fill:#001F5B,color:#ffffff
  style err fill:#ffffff,stroke:#B3261E,color:#B3261E
  style alt fill:#F3E6DA,stroke:#8F5622
  style save fill:#001F5B,color:#ffffff
```
El mensaje dice **qué choca y qué hacer**; conserva lo ya escrito. Una visita que empieza justo cuando otra termina **sí** se permite. Si la ronda 2 confirma visitas grupales, el aviso por cruce de *inmueble* se relaja.

### W9 · Detalle de solicitud: seguimiento y etapas — HU-06, CU-08
```mermaid
block-beta
  columns 4
  title["Solicitud #124 · Pedro Ramírez · Compra · Casa 12"]:4
  e1["1 Consulta ✓"] e2["2 Visita ● actual"] e3["3 Negociación"] e4["4 Cierre / 5 Abandono"]
  next["Cambiar etapa: [ Pasar a Negociación ]  [ Marcar Abandono ]"]:4
  hist["Historial: 02-nov Consulta → Visita (Ana) · 28-oct Consulta → Consulta «sin avance» · 25-oct creada"]:2 vis["Visitas: 02-nov 10:00 Casa 12 · Realizada"]:2
  note["Nota de contacto"]:3 reg["Registrar contacto"]
  style title fill:#001F5B,color:#ffffff
  style e2 fill:#E6EBF4,stroke:#001F5B,color:#001F5B
  style reg fill:#001F5B,color:#ffffff
```
Solo se ofrecen las etapas permitidas desde la actual. En Cierre/Abandono el panel queda en solo lectura. Al elegir Cierre se pregunta: «¿Marcar la Casa 12 como Vendida?». *(La fila «sin avance» es provisional hasta ADR-002.)*

### W10 · Análisis: demanda por hora — HU-07, RF-50, RF-59
```mermaid
block-beta
  columns 3
  title["Análisis · Demanda"]:2 range["Del 1 al 31 de oct ▾"]
  chart["Gráfica: llegadas de clientes por hora, promedio por día de la semana (picos de mañana y tarde)"]:3
  txt["En promedio llegan 12 clientes por día. Las horas más ocupadas son 10:00–11:00 y 16:00–17:00 (unos 2 clientes por hora)."]:3
  tech["Detalle técnico ▸ tasa λ por franja, ajuste de Poisson y prueba de bondad"]:3
  warn["Pocos datos: solo 14 llegadas entre 12:00 y 13:00. La estimación no es confiable."]:3
  style title fill:#001F5B,color:#ffffff
  style txt fill:#E6EBF4,stroke:#001F5B
  style warn fill:#F3E6DA,stroke:#8F5622
```
La frase en lenguaje de negocio va **arriba**; la técnica (λ, P(X = k)) en un panel plegable. La advertencia aparece cuando hay menos observaciones que el mínimo (RN-40). Solo administrador.

### W11 · Análisis: asesores y esperas — HU-08, RF-51 a RF-53, RF-59
```mermaid
block-beta
  columns 4
  title["Análisis · Asesores y esperas"]:3 range["Del 1 al 31 de oct ▾"]
  k1["Asesores disponibles (promedio): 2"] k2["Espera media: 29 min"] k3["Atención media: 45 min"] k4["Ocupación: 63 %"]
  txt["Con 2 asesores disponibles, un cliente espera en promedio unos 29 minutos. Con 3 esperaría menos de 5 minutos."]:4
  rec["Recomendación: al menos 3 asesores disponibles en las horas pico para esperar menos de 20 min."]:3 lim["Umbral de espera: 20 min ▾"]
  tech["Detalle técnico ▸ ρ, L, Lq, W, Wq del modelo M/M/c"]:4
  stab["Aviso: con esta carga el sistema es inestable, la fila crecería sin límite. Hace falta más personal."]:4
  style title fill:#001F5B,color:#ffffff
  style txt fill:#E6EBF4,stroke:#001F5B
  style rec fill:#E6EBF4,stroke:#001F5B
  style stab fill:#F3E6DA,stroke:#8F5622
```
«Asesores disponibles» descuenta a quienes están en visita (el hallazgo de la ronda 1). El aviso de inestabilidad (ρ ≥ 1) sustituye a las cifras L, Lq, W, Wq. Solo administrador.

### W12 · Análisis: probabilidad de cierre — HU-09, RF-54, RF-55, RF-59
```mermaid
block-beta
  columns 3
  title["Análisis · Probabilidad de cierre"]:2 range["Últimos 3 meses ▾"]
  txt["De cada 10 clientes que consultan, unos 2 terminan cerrando y 8 abandonan. Un cliente tarda en promedio 2,4 pasos en llegar a un resultado."]:3
  f1["Consulta → cierre: 23 %"] f2["Visita → cierre: 36 %"] f3["Negociación → cierre: 69 %"]
  flow["Panel de etapas: Consulta → Visita → Negociación → Cierre / Abandono con la probabilidad de cada salto"]:3
  mx["Detalle técnico ▸ matriz de transición P, matriz fundamental N, probabilidades de absorción"]:3
  warn["Faltan datos: Negociación tiene solo 12 transiciones registradas."]:3
  style title fill:#001F5B,color:#ffffff
  style txt fill:#E6EBF4,stroke:#001F5B
  style warn fill:#F3E6DA,stroke:#8F5622
```
Los valores de la figura son ilustrativos y coinciden con la matriz de ejemplo del README (23 %, 36 % y 69 %; 2,4 pasos desde Consulta). En W11, las cifras de espera (29 min con 2 asesores, unos 4 con 3) salen del modelo M/M/c con λ = 20 clientes/12 h y μ = 1 cliente/45 min. El panel de etapas reutiliza el componente visual de W9.

### W13 · Indicadores por asesor — HU-13, RF-62
```mermaid
block-beta
  columns 5
  title["Análisis · Indicadores por asesor"]:3 range["Octubre ▾"] exp["Exportar CSV"]
  h1["Asesor"] h2["Solicitudes atendidas"] h3["Visitas realizadas"] h4["Cierres"] h5["Atención media"]
  r1["Ana"] r2["58"] r3["31"] r4["9"] r5["24 min"]
  r6["Luis"] r7["49"] r8["27"] r9["6"] r10["29 min"]
  r11["Camilo"] r12["35"] r13["12"] r14["3"] r15["22 min"]
  style title fill:#001F5B,color:#ffffff
  style h1 fill:#E6EBF4,color:#001F5B
  style h2 fill:#E6EBF4,color:#001F5B
  style h3 fill:#E6EBF4,color:#001F5B
  style h4 fill:#E6EBF4,color:#001F5B
  style h5 fill:#E6EBF4,color:#001F5B
```
El asesor ve solo su fila. Cifras ilustrativas. Pedida expresamente por una de las inmobiliarias entrevistadas.

### W14 · Administración: usuarios y horarios — RF-02, RF-36
```mermaid
block-beta
  columns 4
  title["Administración"]:3 add["+ Nuevo usuario"]
  tabs["Usuarios · Horarios de asesores"]:4
  h1["Usuario"] h2["Rol"] h3["Estado"] h4["Acción"]
  r1["ana"] r2["Asesor"] r3["Activo"] r4["Editar · Desactivar"]
  r5["luis"] r6["Asesor"] r7["Activo"] r8["Editar · Desactivar"]
  sch["Horario de Ana: Lun–Vie 08:00–12:00 y 14:00–18:00 · Sáb 08:00–13:00   [ + Agregar turno ]"]:4
  style title fill:#001F5B,color:#ffffff
  style add fill:#001F5B,color:#ffffff
  style h1 fill:#E6EBF4,color:#001F5B
  style h2 fill:#E6EBF4,color:#001F5B
  style h3 fill:#E6EBF4,color:#001F5B
  style h4 fill:#E6EBF4,color:#001F5B
```
Los usuarios se **desactivan**, no se borran (tienen historial). El horario semanal define cuántos asesores hay disponibles por franja (c) para el análisis de colas; el turno debe terminar después de empezar y no repetirse.

## 6. Estados y mensajes comunes

| Situación | Cómo se muestra |
|---|---|
| Lista vacía | Texto que explica y ofrece la acción siguiente («No hay… Cree uno nuevo»). |
| Error de validación | Borde rojo `#B3261E` en el campo + mensaje debajo que dice **cómo corregir**. |
| Aviso (cruce, duplicado, pocos datos) | Bloque beige con borde cobre oscuro; no bloquea el trabajo salvo que la regla lo exija. |
| Acción destructiva (desactivar, cancelar visita) | Confirmación en una frase; nunca borrado definitivo. |
| Cargando | Esqueleto gris en la zona de contenido, no pantalla en blanco. |
| Sin permiso | «Esta sección es solo para administradores» con enlace a Hogar. |

## 7. Trazabilidad

| Pantalla | Historias | Requerimientos | Sprint | Issue |
|---|---|---|---|---|
| W1 | HU-11 | RF-01 | 3 | #24 |
| W2 | HU-12 | RF-25, 26, 35 | 4 | #33, #52 |
| W3, W4 | HU-01, HU-02 | RF-10 a 15 | 3–4 | #26, #27, #31 |
| W5, W6 | HU-03, HU-04 | RF-20 a 24 | 3 | #28, #29 |
| W7, W8 | HU-05 | RF-30 a 34 | 4 | #30 |
| W9 | HU-06 | RF-40 a 43 | 4 | #32 |
| W10 a W12 | HU-07 a HU-09 | RF-50 a 59 | 5 | #35 a #38 |
| W13 | HU-13 | RF-62 | 5 | #54 |
| W14 | HU-11 | RF-02, RF-36 | 3–4 | #24, #53 |

## 8. Pendientes y puntos a validar
- [ ] **Color de error**: la paleta de marca no define uno; se propone `#B3261E` (contraste 6,5:1 sobre blanco). Añadir a `IDENTIDAD_VISUAL.md` al aprobarlo.
- [ ] Validar estos bocetos con **I02** (candidata a piloto) en la segunda ronda (#55): ¿«a quién contactar hoy» es lo primero que quiere ver? ¿Cuántos días sin respuesta marcan una solicitud (N)?
- [ ] Definir cómo se muestra en W9 la autotransición (depende de ADR-002, #20).
- [ ] Alta fidelidad con la marca al implementar (#25); revisar accesibilidad (contraste, foco con teclado, tamaño táctil ≥ 44 px).
- [ ] Decidir si «Clientes» necesita pantalla propia más allá de la búsqueda de W5 (ficha del cliente con sus solicitudes).
