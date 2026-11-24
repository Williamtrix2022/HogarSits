/* Cola M/M/c (Erlang C) para la calculadora del sitio.
 * Mismas fórmulas que apps/analitica/services/colas.py; tests/test_sitio.py las compara.
 * lambdaHora y muHora son tasas por hora; c es el número de asesores. */
(function (raiz) {
  "use strict";

  function colaMMc(lambdaHora, muHora, c) {
    var a = lambdaHora / muHora; // carga ofrecida, en asesores
    var rho = a / c;
    if (!(lambdaHora > 0) || !(muHora > 0) || c < 1) {
      return { estable: false, rho: rho, pEsperar: NaN, wqMin: NaN };
    }
    if (rho >= 1) {
      return { estable: false, rho: rho, pEsperar: 1, wqMin: Infinity };
    }
    var b = 1; // Erlang B por recursión: estable para c grande
    for (var k = 1; k <= c; k++) b = (a * b) / (k + a * b);
    var pEsperar = b / (1 - rho * (1 - b)); // Erlang C
    var wqHoras = pEsperar / (c * muHora - lambdaHora);
    return { estable: true, rho: rho, pEsperar: pEsperar, wqMin: wqHoras * 60 };
  }

  var api = { colaMMc: colaMMc };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.HogarSitsCola = api;
})(typeof window !== "undefined" ? window : this);
