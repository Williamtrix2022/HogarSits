// Mejora progresiva: el servidor ya valida que una venta no quede «Arrendada» ni un alquiler
// «Vendido»; aquí solo se evita ofrecer la opción incoherente según la operación elegida.
(() => {
  const operacion = document.getElementById("id_operacion");
  const estado = document.getElementById("id_estado");
  if (!operacion || !estado) return;

  const incoherente = { VENTA: "ARRENDADO", ALQUILER: "VENDIDO" };

  const ajustar = () => {
    const prohibido = incoherente[operacion.value];
    Array.from(estado.options).forEach((opcion) => {
      opcion.disabled = opcion.value === prohibido;
      opcion.hidden = opcion.value === prohibido;
    });
    if (estado.value === prohibido) estado.value = "DISPONIBLE";
  };

  operacion.addEventListener("change", ajustar);
  ajustar();
})();
