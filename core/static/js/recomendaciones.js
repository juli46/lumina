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

  // --------------------------------------------------
  // ELIMINAR RECOMENDACIÓN (SweetAlert)
  // Form real por cada recomendación (clase
  // .form-eliminar-recomendacion). SweetAlert solo confirma
  // antes de enviarlo; la URL, el CSRF y el POST los maneja
  // el propio <form>.
  // --------------------------------------------------
  document
    .querySelectorAll(".form-eliminar-recomendacion")
    .forEach((formularioEliminar) => {
      formularioEliminar.addEventListener("submit", function (event) {
        event.preventDefault();

        const nombre =
          formularioEliminar.dataset.nombre || "esta recomendación";

        if (!window.Swal) {
          if (
            window.confirm(
              `¿Eliminar "${nombre}"? Esta acción no se puede deshacer.`
            )
          ) {
            formularioEliminar.submit();
          }
          return;
        }

        Swal.fire({
          icon: "warning",
          title: "¿Eliminar recomendación?",
          html: `Se eliminará <strong>${nombre}</strong>.<br>Esta acción no se puede deshacer.`,
          showCancelButton: true,
          confirmButtonText: "Sí, eliminar",
          cancelButtonText: "Cancelar",
          confirmButtonColor: "#e11d48",
          cancelButtonColor: "#8b8593",
          reverseButtons: true,
        }).then((resultado) => {
          if (resultado.isConfirmed) {
            // Evita doble envío si el usuario alcanza a
            // hacer clic dos veces.
            const boton = formularioEliminar.querySelector(
              'button[type="submit"]'
            );
            if (boton) boton.disabled = true;

            formularioEliminar.submit();
          }
        });
      });
    });

  // --------------------------------------------------
  // SELECCIÓN DE KITS / PRODUCTOS: buscador, filtro por
  // categoría (solo aplica donde exista el <select> de
  // categoría, ej. productos), contador, "todos" /
  // "ninguno". Todo con delegación de eventos (un solo
  // listener por lista) para que no se ponga lento aunque
  // haya cientos de kits/productos.
  // --------------------------------------------------
  inicializarSelector("kits");
  inicializarSelector("productos");

  // --------------------------------------------------
  // CHIPS COLAPSABLES DENTRO DE CADA TARJETA
  // Si una recomendación tiene muchos kits o productos
  // asociados, solo se muestran los primeros LIMITE_CHIPS
  // y el resto queda oculto detrás de un botón "+X más".
  // --------------------------------------------------
  inicializarChipsColapsables();

  function inicializarChipsColapsables() {
    const LIMITE_CHIPS = 6;

    document
      .querySelectorAll(".recommendation-card .related-section .chips")
      .forEach((wrapper) => {
        const chips = Array.from(
          wrapper.querySelectorAll(".chip-kit, .chip-product")
        );
        if (chips.length <= LIMITE_CHIPS) return;

        const extra = chips.slice(LIMITE_CHIPS);
        extra.forEach((chip) => (chip.hidden = true));

        const restantes = extra.length;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "chip chip-toggle";
        btn.textContent = `+${restantes} más`;
        btn.dataset.expanded = "false";

        btn.addEventListener("click", () => {
          const expandido = btn.dataset.expanded === "true";
          extra.forEach((chip) => (chip.hidden = expandido));
          btn.textContent = expandido ? `+${restantes} más` : "Ver menos";
          btn.dataset.expanded = String(!expandido);
        });

        wrapper.appendChild(btn);
      });
  }

  function inicializarSelector(grupo) {
    const lista = document.getElementById(`${grupo}SelectionList`);
    if (!lista) return;

    const contadorEl = document.getElementById(`${grupo}SelectedCount`);
    const sinResultados = lista.querySelector(".selection-no-results");
    const items = Array.from(lista.querySelectorAll(".selection-item"));

    const actualizarContador = () => {
      if (!contadorEl) return;
      const marcados = lista.querySelectorAll(
        "input[type=checkbox]:checked"
      ).length;
      contadorEl.textContent =
        marcados === 1 ? "1 seleccionado" : `${marcados} seleccionados`;
    };

    // Delegación: un solo listener cubre todos los checkboxes,
    // incluso los que se agreguen/edite después.
    lista.addEventListener("change", (e) => {
      if (e.target.matches('input[type="checkbox"]')) {
        actualizarContador();
      }
    });

    actualizarContador();

    // Buscador de texto en vivo.
    const buscador = document.querySelector(
      `.selection-filter-input[data-target="${grupo}"]`
    );

    // Filtro por categoría (dropdown). Solo existe en grupos que lo
    // tengan definido en el template (ej. productos); en kits será
    // null y el resto del código lo maneja sin errores.
    const filtroCategoria = document.querySelector(
      `.selection-categoria-filter[data-target="${grupo}"]`
    );

    if (buscador) {
      let filtroTimeout = null;
      buscador.addEventListener("input", () => {
        clearTimeout(filtroTimeout);
        filtroTimeout = setTimeout(aplicarFiltros, 100);
      });
    }

    if (filtroCategoria) {
      filtroCategoria.addEventListener("change", aplicarFiltros);
    }

    // Combina texto + categoría: un item solo queda visible si pasa
    // AMBOS filtros (si alguno está vacío, ese filtro no descarta nada).
    function aplicarFiltros() {
      const termino = (buscador?.value || "").trim().toLowerCase();
      const categoria = filtroCategoria?.value || "";
      let visibles = 0;

      items.forEach((item) => {
        const coincideTexto =
          !termino || item.dataset.search.includes(termino);
        const coincideCategoria =
          !categoria || item.dataset.categoria === categoria;
        const mostrar = coincideTexto && coincideCategoria;

        item.hidden = !mostrar;
        if (mostrar) visibles += 1;
      });

      if (sinResultados) {
        sinResultados.hidden = visibles !== 0;
      }
    }

    // Botones "Todos" / "Ninguno": solo afectan lo que está
    // visible según los filtros actuales (texto + categoría).
    document
      .querySelectorAll(`[data-select-all="${grupo}"]`)
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          items.forEach((item) => {
            if (item.hidden) return;
            const cb = item.querySelector('input[type="checkbox"]');
            if (cb) cb.checked = true;
          });
          actualizarContador();
        });
      });

    document
      .querySelectorAll(`[data-select-none="${grupo}"]`)
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          items.forEach((item) => {
            if (item.hidden) return;
            const cb = item.querySelector('input[type="checkbox"]');
            if (cb) cb.checked = false;
          });
          actualizarContador();
        });
      });

    // Expuesto para que abrirFormulario()/editarRecomendacion()
    // puedan refrescar el contador y limpiar los filtros.
    lista._refrescarSelector = () => {
      actualizarContador();
      if (buscador) buscador.value = "";
      if (filtroCategoria) filtroCategoria.value = "";
      aplicarFiltros();
    };
  }

  // --------------------------------------------------
  // BUSCADOR + PAGINACIÓN DE RECOMENDACIONES (tarjetas ya
  // creadas). Filtra por nombre, producto, mensaje, kits y
  // productos asociados (todo va en data-search), más un
  // filtro de estado (activa/inactiva), y solo muestra de a
  // PAGE_SIZE tarjetas por vez con el botón "Ver más".
  // --------------------------------------------------
  inicializarBuscadorRecomendaciones();

  function inicializarBuscadorRecomendaciones() {
    const grid = document.getElementById("recomendacionesGrid");
    if (!grid) return;

    const PAGE_SIZE = 9; // cuántas tarjetas mostrar por tanda
    let mostrando = PAGE_SIZE;

    const buscador = document.getElementById("buscadorRecomendaciones");
    const filtroEstado = document.getElementById("filtroEstadoRecomendacion");
    const sinResultados = document.getElementById(
      "recomendacionesSinResultados"
    );
    const contadorVisible = document.getElementById(
      "recomendacionesVisibleCount"
    );
    const loadMoreWrap = document.getElementById("recomendacionesLoadMore");
    const shownCountEl = document.getElementById("recomendacionesShownCount");
    const totalCountEl = document.getElementById("recomendacionesTotalCount");
    const btnVerMas = document.getElementById("btnVerMasRecomendaciones");
    const tarjetas = Array.from(
      grid.querySelectorAll(".recommendation-card")
    );

    function aplicarFiltros() {
      const termino = (buscador?.value || "").trim().toLowerCase();
      const estado = filtroEstado?.value || "";

      const coincidentes = tarjetas.filter((tarjeta) => {
        const coincideTexto =
          !termino || (tarjeta.dataset.search || "").includes(termino);
        const coincideEstado =
          !estado || tarjeta.dataset.estado === estado;
        return coincideTexto && coincideEstado;
      });

      const total = coincidentes.length;
      const aMostrar = Math.min(mostrando, total);

      tarjetas.forEach((tarjeta) => (tarjeta.hidden = true));
      coincidentes.slice(0, aMostrar).forEach((tarjeta) => {
        tarjeta.hidden = false;
      });

      if (contadorVisible) contadorVisible.textContent = total;
      if (sinResultados) sinResultados.hidden = total !== 0;

      if (loadMoreWrap) {
        const hayMas = aMostrar < total;
        loadMoreWrap.hidden = total === 0;
        if (btnVerMas) btnVerMas.hidden = !hayMas;
        if (shownCountEl) shownCountEl.textContent = aMostrar;
        if (totalCountEl) totalCountEl.textContent = total;
      }
    }

    if (buscador) {
      let filtroTimeout = null;
      buscador.addEventListener("input", () => {
        mostrando = PAGE_SIZE; // reinicia la paginación al buscar
        clearTimeout(filtroTimeout);
        filtroTimeout = setTimeout(aplicarFiltros, 120);
      });
    }

    if (filtroEstado) {
      filtroEstado.addEventListener("change", () => {
        mostrando = PAGE_SIZE; // reinicia la paginación al cambiar el filtro
        aplicarFiltros();
      });
    }

    if (btnVerMas) {
      btnVerMas.addEventListener("click", () => {
        mostrando += PAGE_SIZE;
        aplicarFiltros();
      });
    }

    // Expuesto para el botón "Limpiar búsqueda" del estado vacío.
    window.limpiarBusquedaRecomendaciones = () => {
      if (buscador) buscador.value = "";
      if (filtroEstado) filtroEstado.value = "";
      mostrando = PAGE_SIZE;
      aplicarFiltros();
      buscador?.focus();
    };

    aplicarFiltros(); // aplica la paginación inicial al cargar la página
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

  refrescarSelectores();
  mostrarModal();
}

function editarRecomendacion(
  id,
  nombre,
  presupuestoMin,
  presupuestoMax,
  productoInteres,
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

  refrescarSelectores();
  mostrarModal();
}

function refrescarSelectores() {
  ["kits", "productos"].forEach((grupo) => {
    const lista = document.getElementById(`${grupo}SelectionList`);
    if (lista && typeof lista._refrescarSelector === "function") {
      lista._refrescarSelector();
    }
  });
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