/* Navegación con el teclado entre las secciones: ← → (o AvPág / RePág). El sitio es un documento
 * normal que funciona sin este archivo; el script solo añade comodidad para presentar. */
(function () {
  "use strict";
  var secciones = Array.prototype.slice.call(document.querySelectorAll("main .diapositiva"));
  var contador = document.getElementById("contador");
  if (!secciones.length) return;

  function actual() {
    var y = window.scrollY + window.innerHeight * 0.35;
    var elegida = 0;
    secciones.forEach(function (s, i) { if (s.offsetTop <= y) elegida = i; });
    return elegida;
  }
  function mostrar() {
    if (!contador) return;
    contador.hidden = false;
    contador.textContent = (actual() + 1) + " / " + secciones.length;
  }
  function ir(i) {
    var destino = secciones[Math.max(0, Math.min(secciones.length - 1, i))];
    destino.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    destino.setAttribute("tabindex", "-1");
    destino.focus({ preventScroll: true });
  }

  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var t = e.target;
    if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); ir(actual() + 1); }
    else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); ir(actual() - 1); }
  });
  window.addEventListener("scroll", mostrar, { passive: true });
  mostrar();
})();
