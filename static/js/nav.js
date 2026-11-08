// Mejora progresiva: sin JavaScript el menú sigue visible y los avisos siguen leyéndose.
(() => {
  const raiz = document.querySelector("[data-pagina]");
  const boton = document.querySelector("[data-menu-boton]");
  const menu = document.getElementById("menu-principal");
  const contenido = document.getElementById("contenido");
  const scrim = document.querySelector("[data-menu-scrim]");
  const movil = window.matchMedia("(max-width: 900px)");

  if (raiz && boton && menu) {
    const abierto = () => raiz.dataset.menuAbierto === "true";
    const fijar = (valor) => {
      raiz.dataset.menuAbierto = String(valor);
      boton.setAttribute("aria-expanded", String(valor));
      // Mientras el panel está abierto, lo que queda detrás no recibe foco ni lectura.
      if (contenido) contenido.inert = valor;
      if (valor) menu.querySelector("a")?.focus();
    };

    boton.addEventListener("click", () => fijar(!abierto()));
    scrim?.addEventListener("click", () => fijar(false));
    document.querySelector("[data-menu-cerrar]")?.addEventListener("click", () => {
      fijar(false);
      boton.focus();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && abierto()) {
        fijar(false);
        boton.focus();
      }
    });
    // Al pasar a escritorio el panel deja de existir: se restablece el estado.
    movil.addEventListener("change", () => fijar(false));
  }

  // Tras un envío fallido, el foco va al resumen de errores (enlaza cada error con su campo).
  document.querySelector("[data-resumen-errores]")?.focus();

  // Cierre de avisos: fundido breve y se retira del documento.
  document.querySelectorAll("[data-aviso-cerrar]").forEach((cerrar) => {
    cerrar.addEventListener("click", () => {
      const aviso = cerrar.closest(".aviso");
      if (!aviso) return;
      const retirar = () => aviso.remove();
      aviso.classList.add("saliendo");
      aviso.addEventListener("transitionend", retirar, { once: true });
      setTimeout(retirar, 300); // respaldo si no hay transición (movimiento reducido)
    });
  });
})();
