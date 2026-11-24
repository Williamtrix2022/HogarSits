/* Calculadora de asesores del sitio. El sitio es un documento normal que funciona sin este archivo;
 * el script solo vuelve interactiva la calculadora (usa HogarSitsCola, de erlang.js). */
(function () {
  "use strict";
  var form = document.getElementById("calculadora");
  var cola = window.HogarSitsCola;
  if (!form || !cola) return;

  var HORAS = 12; // horas de atención del ejemplo de la Propuesta
  var TOPE_MIN = 60; // escala de las barras
  var UMBRAL_MIN = 20; // espera aceptable por defecto del panel
  var coma = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  var entero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });

  var campos = form.elements;
  var barras = document.getElementById("calc-barras");
  var frase = document.getElementById("calc-frase");
  var espera = document.getElementById("calc-espera");
  var prob = document.getElementById("calc-prob");
  var ocupacion = document.getElementById("calc-ocupacion");

  function numero(campo, minimo, maximo, porDefecto) {
    var v = parseFloat(String(campo.value).replace(",", "."));
    if (!isFinite(v)) return porDefecto;
    return Math.min(maximo, Math.max(minimo, v));
  }
  function minutos(m) {
    return m < 1 ? "< 1 min" : coma.format(m) + " min";
  }

  function calcular() {
    var clientes = numero(campos.clientes, 1, 120, 20);
    var atencion = numero(campos.minutos, 5, 180, 45);
    var c = Math.round(numero(campos.asesores, 1, 6, 2));
    var lambda = clientes / HORAS;
    var mu = 60 / atencion;
    campos.cuantos.value = c;

    var r = cola.colaMMc(lambda, mu, c);
    ocupacion.textContent = entero.format(Math.min(r.rho, 9.99) * 100) + " %";
    if (r.estable) {
      espera.textContent = minutos(r.wqMin);
      prob.textContent = entero.format(r.pEsperar * 100) + " %";
      var ok = r.wqMin <= UMBRAL_MIN;
      frase.textContent = "Con " + c + (c === 1 ? " asesor" : " asesores") + ", un cliente espera en promedio " +
        minutos(r.wqMin) + (ok ? ": dentro de los " + UMBRAL_MIN + " minutos aceptables." : ": pasa de los " + UMBRAL_MIN + " minutos aceptables.");
    } else {
      espera.textContent = "sin límite";
      prob.textContent = "100 %";
      frase.textContent = "Con " + c + (c === 1 ? " asesor" : " asesores") + " no alcanza: llegan más clientes de los que se pueden atender y la fila crece sin límite.";
    }

    var html = "";
    for (var k = 1; k <= 6; k++) {
      var s = cola.colaMMc(lambda, mu, k);
      var clases = "barra-fila" + (k === c ? " elegida" : "") + (s.estable ? "" : " inestable");
      var ancho = s.estable ? Math.min(100, (s.wqMin / TOPE_MIN) * 100) : 100;
      var valor = s.estable ? (s.wqMin > TOPE_MIN ? "más de " + TOPE_MIN + " min" : minutos(s.wqMin)) : "sin límite";
      html += '<div class="' + clases + '"><span>' + k + (k === 1 ? " asesor" : " asesores") + '</span>' +
        '<span class="pista"><span class="relleno" style="width:' + ancho.toFixed(1) + '%"></span></span>' +
        '<span class="valor">' + valor + "</span></div>";
    }
    html += '<p class="calc-nota-umbral">La línea punteada marca los ' + UMBRAL_MIN + ' minutos de espera aceptable. Las barras rayadas son cargas que el sistema no puede atender.</p>';
    barras.innerHTML = html;
  }

  form.addEventListener("input", calcular);
  form.addEventListener("submit", function (e) { e.preventDefault(); });
  calcular();
})();
