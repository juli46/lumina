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

  // --------------------------------------------------
  // CONTADOR DE CARACTERES DEL MENSAJE
  // --------------------------------------------------
  const textarea = document.getElementById("recomendacion");
  const contador = document.getElementById("recomendacionCount");

  if (textarea && contador) {
    const actualizarContador = () => {
      contador.textContent = textarea.value.length;
    };

    textarea.addEventListener("input", actualizarContador);

    // Por si el modal se abre en modo edición con texto ya cargado
    actualizarContador();
  }

  // --------------------------------------------------
  // VALIDACIÓN DE PRESUPUESTO MIN / MAX
  // --------------------------------------------------
  const form = document.getElementById("recomendacionForm");
  const presupuestoMin = document.getElementById("presupuesto_min");
  const presupuestoMax = document.getElementById("presupuesto_max");
  const presupuestoError = document.getElementById("presupuesto-error");

  function presupuestoValido() {
    if (!presupuestoMin || !presupuestoMax) return true;

    const min = parseFloat(presupuestoMin.value);
    const max = parseFloat(presupuestoMax.value);

    if (Number.isNaN(min) || Number.isNaN(max) || max < min) {
      if (presupuestoError) presupuestoError.hidden = false;
      presupuestoMin.classList.add("input-error");
      presupuestoMax.classList.add("input-error");
      return false;
    }

    if (presupuestoError) presupuestoError.hidden = true;
    presupuestoMin.classList.remove("input-error");
    presupuestoMax.classList.remove("input-error");
    return true;
  }

  if (presupuestoMin && presupuestoMax) {
    presupuestoMin.addEventListener("input", presupuestoValido);
    presupuestoMax.addEventListener("input", presupuestoValido);
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      if (!presupuestoValido()) {
        e.preventDefault();
        presupuestoError?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    });
  }
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

  const contador = document.getElementById("recomendacionCount");
  if (contador) contador.textContent = "0";

  const presupuestoError = document.getElementById("presupuesto-error");
  if (presupuestoError) presupuestoError.hidden = true;

  document
    .querySelectorAll("#presupuesto_min, #presupuesto_max")
    .forEach((input) => input.classList.remove("input-error"));

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

  const contador = document.getElementById("recomendacionCount");
  if (contador) contador.textContent = (recomendacionTexto || "").length;

  const presupuestoError = document.getElementById("presupuesto-error");
  if (presupuestoError) presupuestoError.hidden = true;

  document
    .querySelectorAll("#presupuesto_min, #presupuesto_max")
    .forEach((input) => input.classList.remove("input-error"));

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