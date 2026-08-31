document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("recomendacionModal");
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) cerrarFormulario();
    });
  } else {
    console.error(
      "[recomendaciones.js] No se encontró #recomendacionModal en el DOM."
    );
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrarFormulario();
  });

  // Si tu plantilla base tiene un script genérico que cierra cualquier
  // modal/dropdown al detectar un click "fuera" de él, ese click en el
  // botón (que está fuera del overlay) le llega también a ese listener
  // global y cierra el modal en el mismo instante que se abre. Frenamos
  // la propagación desde el botón mismo para evitarlo.
  document
    .querySelectorAll(
      '[onclick^="abrirFormulario"], [onclick^="editarRecomendacion"]'
    )
    .forEach((btn) => {
      btn.addEventListener("click", (e) => e.stopPropagation());
    });
});

function abrirFormulario() {
  const form = document.getElementById("recomendacionForm");
  if (form) form.reset();

  const campoId = document.getElementById("recomendacion_id");
  if (campoId) campoId.value = "";

  const titulo = document.getElementById("modalTitulo");
  if (titulo) titulo.textContent = "Nueva recomendación";

  const eyebrow = document.getElementById("modalEyebrow");
  if (eyebrow) eyebrow.textContent = "✨ CONFIGURACIÓN";

  const textoGuardar = document.getElementById("textoGuardar");
  if (textoGuardar) textoGuardar.textContent = "Guardar recomendación";

  document
    .querySelectorAll(".kit-checkbox, .producto-checkbox")
    .forEach((cb) => (cb.checked = false));

  const activa = document.getElementById("activa");
  if (activa) activa.checked = true;

  mostrarModal();
}

function editarRecomendacion(
  id,
  nombre,
  presupuestoMin,
  presupuestoMax,
  productoInteres,
  plataforma,
  recomendacionTexto,
  activa,
  kitsIds,
  productosIds
) {
  document.getElementById("recomendacion_id").value = id;
  document.getElementById("nombre").value = nombre;
  document.getElementById("presupuesto_min").value = presupuestoMin;
  document.getElementById("presupuesto_max").value = presupuestoMax;
  document.getElementById("producto_interes").value = productoInteres || "";
  document.getElementById("plataforma").value = plataforma || "";
  document.getElementById("recomendacion").value = recomendacionTexto || "";
  document.getElementById("activa").checked = !!activa;

  document.querySelectorAll(".kit-checkbox").forEach((cb) => {
    cb.checked = kitsIds.includes(parseInt(cb.value, 10));
  });
  document.querySelectorAll(".producto-checkbox").forEach((cb) => {
    cb.checked = productosIds.includes(parseInt(cb.value, 10));
  });

  document.getElementById("modalTitulo").textContent = "Editar recomendación";
  document.getElementById("modalEyebrow").textContent = "✨ EDITANDO";
  document.getElementById("textoGuardar").textContent = "Guardar cambios";

  mostrarModal();
}

function mostrarModal() {
  const overlay = document.getElementById("recomendacionModal");
  if (!overlay) return;
  overlay.classList.add("open");
  overlay.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function cerrarFormulario() {
  const overlay = document.getElementById("recomendacionModal");
  if (!overlay) return;
  overlay.classList.remove("open");
  overlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function confirmarEliminacion(event) {
  const ok = window.confirm(
    "¿Seguro que quieres eliminar esta recomendación? Esta acción no se puede deshacer."
  );
  if (!ok) event.preventDefault();
  return ok;
}