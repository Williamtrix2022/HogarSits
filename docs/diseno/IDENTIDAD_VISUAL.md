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
| `--hs-bg` | Fondo cálido (de la hoja de marca) | `#F4F2EE` | Fondo de la aplicación (aprox.) |

Tonos derivados (propuestos, no vienen en la hoja; validar con el equipo): `--hs-navy-100: #E6EBF4`, `--hs-navy-500: #2A4A82`, `--hs-copper-100: #F3E6DA`, **`--hs-copper-text: #8F5622`**.

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
  --hs-ok: #2F8F4E;     --hs-closed: #6B6B6B;
  --font-head: "Nunito Sans", "Avenir", system-ui, sans-serif;
  --font-body: "Open Sans", system-ui, sans-serif;
}
```

## 5. Pendientes
- [ ] Logo en SVG (los archivos actuales son JPEG; para favicon y cabecera conviene vectorial o PNG con fondo transparente).
- [ ] Confirmar los tonos derivados y la fuente alternativa a Avenir.
- [ ] **Color de error** (la hoja de marca no lo define): propuesta `#B3261E` (contraste 6,5:1 sobre blanco), usado en los wireframes.
- [ ] Modo oscuro: fuera de alcance por ahora.
