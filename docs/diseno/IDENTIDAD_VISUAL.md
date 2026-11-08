# HogarSits — Identidad visual y guía de UI

**Versión:** 0.1 · **Fecha:** 2026-11-07 · **Sprint:** 2 · **Fuente:** `docs/IDENTIDAD VISUAL/`
(`Identidad_Visual_HogarSist.jpeg` = hoja de marca; `Logo_HogarSits_horizontal.jpeg` = logo con lema «Gestión y Análisis Inmobiliario»).

Concepto: una casa cuyo techo se convierte en una **flecha ascendente sobre una línea de datos**: gestión inmobiliaria + analítica. Sobrio, confiable y cercano.

## 1. Paleta

| Token | Nombre | Hex | Uso |
|---|---|---|---|
| `--hs-navy` | Deep Navy Blue | `#001F5B` | Marca, títulos, botón primario, menú activo |
| `--hs-copper` | Warm Copper | `#B87333` | Acentos, iconos, gráficas, elementos grandes |
| `--hs-slate` | Slate Grey | `#4A4A4A` | Texto secundario, bordes, estados cerrados |
| `--hs-white` | Clean White | `#FFFFFF` | Superficies y tarjetas |
| `--hs-error` | Error (**aprobado 2026-11-08**, no está en la hoja de marca) | `#B3261E` | Errores de validación: borde del campo, texto del mensaje y avisos de bloqueo. Siempre con texto o icono, nunca solo color |
| `--hs-bg` | Fondo cálido (de la hoja de marca) | `#F4F2EE` | Fondo de la aplicación (aprox.) |

Tonos derivados (propuestos, no vienen en la hoja; validar con el equipo): `--hs-navy-100: #E6EBF4`, `--hs-navy-500: #2A4A82`, `--hs-copper-100: #F3E6DA`, **`--hs-copper-text: #8F5622`**, `--hs-line: #DAD6CE` (bordes y líneas suaves).

### Contraste (WCAG 2.1 AA; texto normal ≥ 4,5:1, texto grande/iconos ≥ 3:1)
| Combinación | Ratio | Veredicto |
|---|---|---|
| Navy sobre blanco | 15,6 | ✅ cualquier uso |
| Slate sobre blanco | 8,9 | ✅ |
| Navy sobre fondo cálido | 13,9 | ✅ |
| Cobre `#B87333` sobre blanco | **3,8** | ⚠️ solo texto grande (≥ 24 px, o 19 px negrita), iconos, gráficas |
| Blanco sobre cobre | **3,8** | ⚠️ solo botones con texto grande/negrita |
| Navy sobre cobre | 4,1 | ⚠️ no usar para texto pequeño |
| `#8F5622` (cobre oscuro) sobre blanco | 6,0 | ✅ **usar para texto cobre pequeño** |
| `#B3261E` (error) sobre blanco | 6,5 | ✅ texto y bordes de error |
| `#B3261E` (error) sobre fondo cálido | 5,9 | ✅ |

**Reglas:** el botón primario es **navy con texto blanco**; el cobre nunca es color de texto pequeño (usar `--hs-copper-text`); el estado no se comunica solo con color (siempre texto + punto/icono).

## 2. Tipografía
| Rol | Fuente de la marca | Propuesta web | Pesos |
|---|---|---|---|
| Títulos | Avenir o similar | **Nunito Sans** (Google Fonts, gratuita; Avenir es de pago) | Bold, SemiBold, Regular |
| Cuerpo | Open Sans o similar | **Open Sans** (Google Fonts) | Regular, Light |

Light solo para texto grande (≥ 18 px); en tablas y formularios usar Regular.

## 3. Componentes (de la hoja de marca)
- **Menú de navegación:** Hogar · Inmuebles · Clientes · Análisis (iconos de línea; ítem activo con fondo `--hs-navy-100` y texto navy). Se ampliará con Solicitudes, Agenda y Seguimiento.
- **Estado de inmueble (chip con punto + texto):** Disponible = punto verde; Reservado = punto cobre; Vendido/Arrendado = punto gris. Texto en navy/slate.
- **Panel de etapas del cliente:** Consulta → Visita → Negociación → Cierre; Cierre y Abandono como destinos finales.
- **Gráficas:** serie principal navy, secundaria cobre, terciaria gris pizarra; leyenda y etiquetas siempre visibles.
- **Formularios:** campos blancos con borde fino gris, botón primario navy («Agendar visita»).
- **Tarjetas:** blanco, esquinas redondeadas, sombra suave.
- **Icono de app:** casa + flecha sobre fondo claro con esquinas redondeadas.

## 4. Tokens CSS (se implementan en la plantilla base, issue #25)
```css
:root {
  --hs-navy: #001F5B;   --hs-navy-500: #2A4A82;  --hs-navy-100: #E6EBF4;
  --hs-copper: #B87333; --hs-copper-text: #8F5622; --hs-copper-100: #F3E6DA;
  --hs-slate: #4A4A4A;  --hs-white: #FFFFFF;     --hs-bg: #F4F2EE;
  --hs-ok: #2F8F4E;     --hs-closed: #6B6B6B;  --hs-error: #B3261E;
  --font-head: "Nunito Sans", "Avenir", system-ui, sans-serif;
  --font-body: "Open Sans", system-ui, sans-serif;
}
```

## 5. Pantalla de acceso (implementada, #24)

Primera pantalla con diseño propio; sirve de referencia para el resto. Archivos: `templates/cuentas/login.html`, `static/css/login.css`, `static/js/login.js`, `static/img/logo-hogarsits.png` (recorte del logo horizontal).

- **Idea:** entrar a la plataforma es entrar a una casa. El panel azul marino dibuja un **plano de casa** (cotas y rótulo de plano incluidos) una sola vez al cargar y, al final, se abre la puerta de entrada.
- **El cobre se usa una sola vez** en toda la pantalla: la puerta de entrada (hoja y arco de giro). El resto es azul marino, blanco y pizarra.
- **Formulario** sobre blanco, alineado a la izquierda, sin tarjeta ni sombra; etiquetas visibles, «Mostrar/Ocultar» contraseña (mejora progresiva), mensaje de error que dice qué hacer, y una nota honesta de qué hacer si no puede entrar.
- **Evitado a propósito:** tarjeta centrada sobre degradado, ilustraciones genéricas, etiquetas en mayúsculas, flechas en botones, iconos decorativos.
- **Accesibilidad:** contrastes AA, foco visible, objetivos de 44–50 px, el plano es `aria-hidden`, el logo tiene `alt`, con error los campos llevan `aria-invalid` y el foco pasa a la contraseña, y con `prefers-reduced-motion` el plano aparece ya dibujado y con la puerta abierta.
- **Responsive:** por debajo de 900 px se oculta el plano y queda el formulario con una franja azul superior.

## 6. Interfaz base (implementada, #25)

Archivos: `templates/base.html`, `templates/componentes/` (icono, aviso, estado vacío, sprite de iconos), `static/css/app.css`, `static/js/nav.js`, `apps/cuentas/navegacion.py`. Catálogo vivo en la pantalla **Administración → `/administracion/componentes/`** (solo administradores). Movimiento: [`MOVIMIENTO.md`](MOVIMIENTO.md).

**Método.** Se usaron las skills `ui-ux-pro-max` (sistema de diseño y guías de UX) y `ui-animation` (movimiento). Las recomendaciones se verificaron antes de aplicarlas, como exige la skill:

| Recomendación de la skill | Decisión | Motivo |
|---|---|---|
| Estilo *Minimalism & Swiss* | **Adoptado** | La propia skill lo indica para dashboards y herramientas profesionales: rejilla, espacio, alto contraste. |
| Iconos Phosphor de línea, decorativos con `aria-hidden` | **Adoptado** | Coincide con los iconos de la hoja de marca (casa, edificio, personas, barras). Licencia MIT en `static/img/LICENCIA-phosphor-icons.txt`. |
| Pautas UX: estado activo visible, saltar al contenido, tablas con desplazamiento, 44 px, foco visible | **Adoptado** | Ver lista abajo. |
| Patrón «Hero-Centric» | Descartado | Es para páginas de aterrizaje; esto es una aplicación interna. |
| Paleta verde azulada y tipografía Cinzel/Josefin | Descartado | La marca ya define paleta y tipografías; la decisión del cliente prevalece. |
| Scroll reveal | Descartado | Es un antipatrón en interfaz de producto (ver `MOVIMIENTO.md`). |

**Estructura.** Barra superior blanca con el logo, el usuario y «Salir»; menú lateral de 232 px; contenido de hasta 1120 px sobre el fondo cálido; encabezado de página con título y acciones (`{% block titulo_pagina %}` y `{% block acciones %}`). Por debajo de 900 px el menú es un panel lateral con su botón «Menú»; sin JavaScript queda visible en la página.

**Menú que se completa solo.** `navegacion.py` declara todos los destinos previstos y el menú **muestra únicamente los que ya existen**; cada sprint «enciende» su sección al registrar la URL. Contrato de nombres: `inmuebles:lista` (#26), `clientes:lista` (#28), `seguimiento:cola` (#29), `agenda:semana` (Sprint 4), `analitica:inicio` (Sprint 5, solo administrador). El ítem activo se marca con fondo, barra lateral y `aria-current="page"`, no solo con color.

**Componentes:** botones (primario, secundario, peligro), estados con punto y texto, avisos de cuatro tipos (cerrables; los errores usan `role="alert"`, el resto `role="status"`), formularios con etiqueta visible y error junto al campo (enlazado con `aria-describedby`), tablas con contenedor desplazable, estado vacío, iconos en un sprite SVG **en línea** (no depende de otro origen cuando los estáticos pasen a S3 o CloudFront).

**Lista de entrega (de la skill) verificada:** sin emojis como iconos · `cursor: pointer` en lo clicable · hover con transición suave (150 ms) y solo con puntero fino · contraste mínimo 4,5:1 · foco visible · `prefers-reduced-motion` respetado · responsive a 500 px y 1440 px (capturas) · objetivos táctiles de 44 px · enlace «Saltar al contenido» · tablas sin romper el diseño en móvil.

**Pendiente de comprobar a mano:** 375 px y 768 px reales (Edge headless no baja de 500 px), lector de pantalla y navegación solo con teclado en un navegador real.

## 7. Pendientes
- [ ] Logo en SVG (los archivos actuales son JPEG; para favicon y cabecera conviene vectorial o PNG con fondo transparente).
- [ ] Confirmar los tonos derivados y la fuente alternativa a Avenir.
- [ ] Modo oscuro: fuera de alcance por ahora.
