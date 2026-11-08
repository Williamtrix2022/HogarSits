# HogarSits — Plan de movimiento

**Versión:** 1.0 · **Fecha:** 2026-11-08 · **Sprint:** 3 · **Issue:** #25
**Método:** skill `ui-animation` (marco de decisión y pasada de descubrimiento). Implementación en `static/css/tokens.css`, `static/css/app.css`, `static/css/login.css` y `static/js/nav.js`.

## 1. Principio
HogarSits es una herramienta de trabajo que se usa todo el día. **El movimiento solo existe para dar respuesta, orientar o, en momentos raros, dar un toque de personalidad.** Lo que se hace decenas de veces al día no se anima; lo que ocurre pocas veces puede hacerlo, con poca duración.

## 2. Tokens de movimiento (`tokens.css`)
| Token | Valor | Uso |
|---|---|---|
| `--curva-entrada` | `cubic-bezier(0.22, 1, 0.36, 1)` | Pulsación y apariciones |
| `--curva-panel` | `cubic-bezier(0.25, 1, 0.5, 1)` | Paneles que se deslizan (menú móvil) |
| `--dur-hover` | 150 ms | Color al pasar el cursor |
| `--dur-pulsar` | 120 ms | Al **soltar** un botón (al pulsar es 0 ms) |
| `--dur-panel` | 240 ms | Panel del menú móvil y su fondo (misma duración y curva: se animan juntos) |
| `--dur-aviso` | 150 ms | Cierre de un aviso |

Reglas: solo `transform`, `opacity` y color; **nunca** `transition: all` ni propiedades de layout (`width`, `height`, `top`, `left`, `margin`, `padding`). Un test lo verifica en las hojas de estilo.

## 3. Pasada de descubrimiento (qué se anima y qué no)

### Se anima
| # | Dónde | Propósito | Frecuencia | Valores |
|---|---|---|---|---|
| 1 | Panel del menú móvil (`.menu`) y su fondo (`.scrim`) | Orientación: entra desde el borde del que sale el botón | Ocasional (algunas veces por sesión, solo en móvil) | `transform: translateX`, 240 ms, `--curva-panel`; el fondo se atenúa con la misma duración y curva |
| 2 | Botones (`.boton`) | Respuesta: se confirma que el toque llegó | Muy frecuente, pero imperceptible | Al pulsar `scale(.98)` en **0 ms**; al soltar vuelve en 120 ms |
| 3 | Cierre de un aviso | Respuesta: el aviso se va en el sitio donde se pulsó | Ocasional | `opacity` 150 ms y se retira del documento |
| 4 | Color de ítems de menú y botones | Respuesta al cursor | Frecuente | Solo color, 150 ms, **solo con ratón** (`@media (hover: hover) and (pointer: fine)`) |
| 5 | Plano de la pantalla de acceso | Un toque de personalidad en un momento raro | Una vez por navegador | Muros se dibujan, luego los detalles, al final se abre la puerta de entrada (única pieza en cobre); ver §5 |

### No se anima (y por qué)
| Candidato | Pregunta que lo descarta |
|---|---|
| Transición entre pantallas | Se navega más de 100 veces al día: «No animar. Nunca». |
| Revelado al hacer scroll (listas, tarjetas) | Es interfaz de producto, no una página de marketing: un efecto de scroll aquí estorba. |
| Menú desplegable del usuario | No hace falta: el nombre y «Salir» están siempre visibles. |
| Resaltado de fila de tabla | Se recorre decenas de veces al día: cambia el fondo al instante, sin transición. |
| Filtros, resultados y paginación de las listas | Se usan decenas de veces al día: el resultado cambia al instante, sin transición. |
| Aparición de los avisos al cargar la página | Aparecen por una acción del usuario; moverlos sería ruido. Se leen de inmediato. |
| Cambio de color del ítem activo del menú | Navegar es de alta frecuencia: el estado nuevo es inmediato. |

## 4. Accesibilidad del movimiento
- **`prefers-reduced-motion: reduce`:** el panel móvil aparece sin deslizarse (solo cambio de estado), el fondo se atenúa en 100 ms, la pulsación no escala. El plano del login se muestra ya dibujado, con la puerta abierta.
- **Hover solo con puntero fino:** en pantallas táctiles el hover se repetiría al tocar.
- **Foco y teclado inmediatos:** abrir el panel mueve el foco al primer enlace; `Esc` lo cierra y devuelve el foco al botón «Menú»; mientras está abierto, el contenido de atrás queda `inert`. Cerrar con el botón «Cerrar menú», con el fondo o con `Esc`.
- **Mejora progresiva:** sin JavaScript el menú queda visible en el flujo de la página y los avisos siguen leyéndose.
- Las pulsaciones son **transiciones** (no `@keyframes`), así que se interrumpen y cambian de destino sin reiniciarse.

## 5. Corrección sobre el login (#63)
La skill indica que los adornos de login **no deben repetirse en cada visita**. El plano se animaba siempre; ahora solo la primera vez por navegador (marca `hs-plano-visto` en `localStorage`). Las visitas siguientes lo muestran completo al instante. Verificado con capturas: primera visita a 0,7 s con los muros a medio dibujar; segunda visita con el plano completo.

## 6. Validación (evidencia)
- `tests/test_navegacion.py`: sin `transition: all` ni propiedades de layout; presencia de `prefers-reduced-motion`, hover con puntero fino y pulsación a 0 ms; el plano solo se anima la primera vez.
- Capturas con Edge: menú móvil cerrado y abierto (con botón de cerrar), primera y segunda visita al login.
- **Pendiente de verificar a mano** (no se puede automatizar aquí): ralentizar al 10 % en el panel de Animaciones de DevTools para revisar `transform-origin` y orden; abrir y cerrar el menú varias veces seguidas para confirmar que cambia de destino sin reiniciarse; probar el panel en un teléfono real.
