/* Gráficos del panel de análisis (Chart.js, copiado en static/js/vendor/).
 *
 * Los datos llegan ya calculados desde el servidor (json_script): aquí solo se dibujan.
 * Colores: los de la marca, leídos de los tokens CSS. Cada gráfico tiene una tabla equivalente
 * en el «Detalle técnico», así que nada depende solo de poder ver el color o el dibujo.
 */
(function () {
  "use strict";
  if (typeof Chart === "undefined") return;
  var nodo = document.getElementById("datos-graficas");
  if (!nodo) return;
  var datos = JSON.parse(nodo.textContent);

  var css = getComputedStyle(document.documentElement);
  function token(nombre, respaldo) {
    var v = css.getPropertyValue(nombre).trim();
    return v || respaldo;
  }
  var NAVY = token("--hs-navy", "#001F5B");
  var NAVY_100 = token("--hs-navy-100", "#E6EBF4");
  var COBRE = token("--hs-copper", "#B87333");
  var PIZARRA = token("--hs-slate", "#4A4A4A");

  var sinMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  Chart.defaults.font.family = token("--font-body", "system-ui, sans-serif");
  Chart.defaults.color = PIZARRA;
  Chart.defaults.animation = sinMovimiento ? false : { duration: 400 };
  Chart.defaults.plugins.legend.display = true; // la leyenda siempre visible
  Chart.defaults.maintainAspectRatio = false;

  function lienzo(id) {
    var el = document.getElementById(id);
    return el ? el.getContext("2d") : null;
  }
  function eje(titulo, extra) {
    return Object.assign({ title: { display: true, text: titulo }, grid: { color: NAVY_100 } }, extra || {});
  }

  // 1. Demanda: λ por hora. Las barras con pocos datos van claras (no son confiables).
  var d = datos.demanda;
  var c1 = lienzo("graf-demanda");
  if (d && c1) {
    new Chart(c1, {
      type: "bar",
      data: {
        labels: d.horas,
        datasets: [{
          label: "Clientes que llegan por hora (promedio)",
          data: d.lam,
          backgroundColor: d.suficiente.map(function (ok) { return ok ? NAVY : NAVY_100; }),
          borderColor: NAVY,
          borderWidth: 1,
        }],
      },
      options: { scales: { x: eje("Hora del día"), y: eje("Clientes por hora", { beginAtZero: true }) } },
    });
  }

  // 2. Ajuste de Poisson en la hora pico: frecuencia observada frente a la teórica.
  var a = datos.ajuste;
  var c2 = lienzo("graf-ajuste");
  if (a && c2) {
    new Chart(c2, {
      data: {
        labels: a.ks.map(String),
        datasets: [
          { type: "bar", label: "Observada (%)", data: a.observada, backgroundColor: NAVY },
          { type: "line", label: "Poisson (%)", data: a.esperada, borderColor: COBRE,
            backgroundColor: COBRE, borderWidth: 2, pointRadius: 4, tension: 0 },
        ],
      },
      options: {
        scales: {
          x: eje("Llegadas en la hora (" + a.hora + ")"),
          y: eje("% de las horas", { beginAtZero: true }),
        },
      },
    });
  }

  // 3. Espera media según el número de asesores. Sin punto = carga inestable.
  var q = datos.colas;
  var c3 = lienzo("graf-colas");
  if (q && c3) {
    // Un valor enorme (p. ej. 150 min con un solo asesor) aplastaría el resto: se recorta el
    // eje y esos puntos se dibujan como triángulos en el tope; el valor real va en el tooltip.
    var tope = Math.max(q.umbral * 5, 60);
    var recortado = q.wq_min.map(function (v) { return v !== null && v > tope; });
    var visibles = q.wq_min.map(function (v) { return v === null ? null : Math.min(v, tope); });
    new Chart(c3, {
      type: "line",
      data: {
        labels: q.c.map(String),
        datasets: [
          { label: "Espera media (min)", data: visibles, borderColor: COBRE, backgroundColor: COBRE,
            borderWidth: 2, spanGaps: false, tension: 0,
            pointRadius: recortado.map(function (r) { return r ? 8 : 5; }),
            pointStyle: recortado.map(function (r) { return r ? "triangle" : "circle"; }) },
          { label: "Espera aceptable (" + q.umbral + " min)", data: q.c.map(function () { return q.umbral; }),
            borderColor: PIZARRA, borderDash: [6, 4], borderWidth: 2, pointRadius: 0 },
        ],
      },
      options: {
        scales: {
          x: eje("Asesores disponibles"),
          y: eje("Minutos (tope " + Math.round(tope) + ")", { beginAtZero: true, max: tope }),
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (ctx.datasetIndex !== 0) return ctx.dataset.label;
                var real = q.wq_min[ctx.dataIndex];
                return "Espera media: " + (real === null ? "inestable" : real + " min");
              },
            },
          },
        },
      },
    });
  }

  // 4. Probabilidad de cierre y de abandono según la etapa en que está el cliente.
  var k = datos.cierre;
  var c4 = lienzo("graf-cierre");
  if (k && c4) {
    new Chart(c4, {
      type: "bar",
      data: {
        labels: k.etapas,
        datasets: [
          { label: "Termina cerrando (%)", data: k.cierre, backgroundColor: NAVY },
          { label: "Termina abandonando (%)", data: k.abandono, backgroundColor: PIZARRA },
        ],
      },
      options: {
        indexAxis: "y",
        scales: { x: eje("% de los clientes", { stacked: true, max: 100 }), y: { stacked: true } },
      },
    });
  }
})();
