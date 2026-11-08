// Mejora progresiva: sin JavaScript el formulario funciona igual (la contraseña queda oculta).
document.querySelectorAll("[data-ver-clave]").forEach((boton) => {
  const campo = document.getElementById(boton.getAttribute("aria-controls"));
  if (!campo) return;
  boton.addEventListener("click", () => {
    const visible = campo.type === "text";
    campo.type = visible ? "password" : "text";
    boton.textContent = visible ? "Mostrar" : "Ocultar";
    boton.setAttribute("aria-pressed", String(!visible));
    campo.focus();
  });
});
