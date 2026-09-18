// =====================================
// HELPERS DE VALIDACIÓN VISUAL
// =====================================

function mostrarError(input, mensaje) {

    if (!input) return;

    input.classList.add("campo-invalido");

    const contenedorCampo = input.closest(".campo");

    if (contenedorCampo) {

        const errorEl = contenedorCampo.querySelector(".error-campo");

        if (errorEl) {
            errorEl.textContent = mensaje;
        }

    }

}

function limpiarError(input) {

    if (!input) return;

    input.classList.remove("campo-invalido");

    const contenedorCampo = input.closest(".campo");

    if (contenedorCampo) {

        const errorEl = contenedorCampo.querySelector(".error-campo");

        if (errorEl) {
            errorEl.textContent = "";
        }

    }

}

function limpiarErroresFormulario(form) {

    form.querySelectorAll(".error-campo").forEach(el => {
        el.textContent = "";
    });

    form.querySelectorAll(".campo-invalido").forEach(el => {
        el.classList.remove("campo-invalido");
    });

}


// =====================================
// AGREGAR TONOS DINÁMICAMENTE
// =====================================

let contadorTonos = document.querySelectorAll(".variante-box").length || 1;

const botonTono = document.getElementById("agregar-tono");

if (botonTono) {

    botonTono.addEventListener("click", function () {

        contadorTonos++;

        const contenedor = document.getElementById("contenedor-tonos");

        const caja = document.createElement("div");

        caja.classList.add("variante-box");

        caja.innerHTML = `

            <h5>
                Tono ${contadorTonos}
            </h5>

            <div class="grid-tonos">

                <div class="campo">

                    <label>
                        Nombre
                    </label>

                    <input
                        type="text"
                        name="nombre_tono[]"
                        placeholder="Ej: Natural"
                        required
                    >

                    <small class="error-campo"></small>

                </div>

                <div class="campo">

                    <label>
                        Código
                    </label>

                    <input
                        type="text"
                        name="codigo_tono[]"
                        placeholder="Ej: N01"
                    >

                    <small class="error-campo"></small>

                </div>

                <div class="campo">

                    <label>
                        SKU
                    </label>

                    <input
                        type="text"
                        name="sku[]"
                        placeholder="Ej: BASE-N01"
                        required
                    >

                    <small class="error-campo"></small>

                </div>

                <div class="campo">

                    <label>
                        Stock
                    </label>

                    <input
                        type="number"
                        name="stock[]"
                        min="2"
                        value="0"
                        required
                    >

                    <small class="error-campo"></small>

                </div>

            </div>

            <button
                type="button"
                class="eliminar-tono"
            >
                ❌ Quitar tono
            </button>

        `;

        contenedor.appendChild(caja);

    });

}


// =====================================
// ELIMINAR TONOS (con confirmación Swal)
// =====================================

document.addEventListener("click", function (e) {

    if (e.target.classList.contains("eliminar-tono")) {

        const caja = e.target.closest(".variante-box");

        Swal.fire({

            icon: "warning",
            title: "¿Quitar este tono?",
            text: "Se eliminará del formulario, pero el producto no se guardará hasta que envíes el formulario.",
            showCancelButton: true,
            confirmButtonText: "Sí, quitar",
            cancelButtonText: "Cancelar"

        }).then((resultado) => {

            if (resultado.isConfirmed) {
                caja.remove();
            }

        });

    }

});


// =====================================
// CARGAR COLECCIONES POR MARCA
// =====================================

const marca = document.getElementById("marca");
const coleccion = document.getElementById("coleccion");

if (marca && coleccion) {

    marca.addEventListener("change", function () {

        const idMarca = this.value;

        if (!idMarca) {

            coleccion.innerHTML = `
                <option value="">
                    Seleccione una marca primero
                </option>
            `;

            return;

        }

        fetch(`/dashboard/colecciones/?marca=${idMarca}`)

            .then(response => response.json())

            .then(data => {

                coleccion.innerHTML = `
                    <option value="">
                        Seleccione una colección
                    </option>
                `;

                data.forEach(item => {

                    const option = document.createElement("option");

                    option.value = item.id;

                    option.textContent = item.nombre;

                    coleccion.appendChild(option);

                });

            })

            .catch(error => {

                console.error(error);

                Swal.fire({
                    icon: "error",
                    title: "No se pudieron cargar las colecciones",
                    text: "Intenta nuevamente o recarga la página.",
                    timer: 3000,
                    showConfirmButton: false
                });

            });

    });

}


// =====================================
// TABS DE PRODUCTOS
// =====================================

document.querySelectorAll(".detalle-tabs").forEach(tabContainer => {

    tabContainer.addEventListener("click", function (e) {

        const boton = e.target.closest(".detalle-tab");

        if (!boton) return;

        const panelActivo = boton.dataset.tab;

        const contenedor = boton.closest(".detalle-contenido");

        contenedor.querySelectorAll(".detalle-tab").forEach(btn => {

            btn.classList.remove("activa");

        });

        boton.classList.add("activa");

        contenedor.querySelectorAll(".detalle-panel").forEach(panel => {

            panel.classList.add("oculto");

        });

        const panelMostrar = contenedor.querySelector(
            `[data-panel="${panelActivo}"]`
        );

        if (panelMostrar) {

            panelMostrar.classList.remove("oculto");

        }

    });

});


// =====================================
// CONFIRMAR ELIMINAR PRODUCTO (Swal)
// =====================================

document.querySelectorAll(".form-eliminar").forEach(form => {

    form.addEventListener("submit", function (e) {

        e.preventDefault();

        Swal.fire({

            icon: "warning",
            title: "¿Eliminar este producto?",
            text: "Esta acción no se puede deshacer.",
            showCancelButton: true,
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar",
            confirmButtonColor: "#d33"

        }).then((resultado) => {

            if (resultado.isConfirmed) {
                form.submit();
            }

        });

    });

});


// =====================================
// EVITAR DOBLE ENVÍO
// =====================================

const formulario = document.querySelector(
    "form[enctype='multipart/form-data']"
);

const botonGuardar = document.getElementById("btn-guardar");

const textoOriginalBoton = botonGuardar
    ? botonGuardar.innerHTML
    : "💾 Guardar Producto";

function bloquearBoton() {

    if (!botonGuardar) return;

    botonGuardar.disabled = true;

    botonGuardar.innerHTML = `⏳ Guardando producto...`;

}

function restaurarBoton() {

    if (!botonGuardar) return;

    botonGuardar.disabled = false;

    botonGuardar.innerHTML = textoOriginalBoton;

}


// =====================================
// MOSTRAR NOMBRES DE IMÁGENES
// =====================================

const inputImagenes = document.getElementById("imagenes");

if (inputImagenes) {

    const listaImagenes = document.createElement("div");

    listaImagenes.classList.add("lista-archivos");

    inputImagenes.parentNode.appendChild(listaImagenes);


    inputImagenes.addEventListener("change", function () {

        listaImagenes.innerHTML = "";

        limpiarError(inputImagenes);

        [...this.files].forEach(file => {

            const archivo = document.createElement("p");

            archivo.innerHTML = `📷 ${file.name}`;

            listaImagenes.appendChild(archivo);

        });

    });

}


// =====================================
// CONTADOR DE ETIQUETAS
// =====================================

const etiquetas = document.getElementById("id_etiquetas");

if (etiquetas) {

    const contador = document.createElement("small");

    contador.classList.add("contador-etiquetas");

    contador.textContent = "0 etiquetas seleccionadas";

    etiquetas.parentNode.appendChild(contador);

    etiquetas.addEventListener("change", function () {

        const total = [...this.options]
            .filter(option => option.selected)
            .length;

        contador.textContent =
            `${total} etiqueta${total !== 1 ? "s" : ""} seleccionada${total !== 1 ? "s" : ""}`;

        limpiarError(etiquetas);

    });

}


// =====================================
// LIMPIAR ERROR AL ESCRIBIR (nombre, descripción, costo)
// =====================================

["nombre", "descripcion", "costo_base"].forEach(nombreCampo => {

    const input = document.querySelector(`[name="${nombreCampo}"]`);

    if (input) {

        input.addEventListener("input", function () {
            limpiarError(input);
        });

    }

});


// =====================================
// CALCULAR PRECIOS POR RENTABILIDAD
// =====================================

const inputCostoBase = document.querySelector('[name="costo_base"]');

const preciosMargen = {
    40: document.getElementById("precio-margen-40"),
    30: document.getElementById("precio-margen-30"),
    25: document.getElementById("precio-margen-25"),
    20: document.getElementById("precio-margen-20")
};

function formatearMoneda(valor) {

    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0
    }).format(valor || 0);

}

function calcularPrecioVenta(costo, margen) {

    const precio = costo / (1 - margen / 100);

    return Math.ceil(precio / 100) * 100;

}

function actualizarPreciosRentabilidad() {

    const costo = parseFloat(inputCostoBase?.value || 0);

    Object.entries(preciosMargen).forEach(([margen, elemento]) => {

        if (!elemento) return;

        elemento.textContent = formatearMoneda(
            calcularPrecioVenta(costo, Number(margen))
        );

    });

}

if (inputCostoBase) {

    inputCostoBase.addEventListener("input", actualizarPreciosRentabilidad);
    actualizarPreciosRentabilidad();

}


// =====================================
// VALIDAR FORMULARIO PRODUCTO
// =====================================

if (formulario) {

    formulario.addEventListener("submit", function (e) {

        limpiarErroresFormulario(formulario);

        let hayErrores = false;
        let primerCampoInvalido = null;

        const inputNombre = document.querySelector('[name="nombre"]');
        const inputDescripcion = document.querySelector('[name="descripcion"]');
        const inputCosto = document.querySelector('[name="costo_base"]');

        const nombreRaw = inputNombre?.value || "";
        const descripcionRaw = inputDescripcion?.value || "";

        const nombre = nombreRaw.trim();
        const descripcion = descripcionRaw.trim();
        const costo = parseFloat(inputCosto?.value || 0);

        // =========================
        // NOMBRE
        // =========================

        if (/^\s/.test(nombreRaw)) {

            mostrarError(inputNombre, "El nombre no puede iniciar con espacios.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputNombre;

        } else if (!nombre) {

            mostrarError(inputNombre, "Debes ingresar el nombre del producto.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputNombre;

        } else if (nombre.length < 3) {

            mostrarError(inputNombre, "El nombre debe tener mínimo 3 caracteres.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputNombre;

        }

        // =========================
        // DESCRIPCIÓN
        // =========================

        if (/^\s/.test(descripcionRaw)) {

            mostrarError(inputDescripcion, "La descripción no puede iniciar con espacios.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputDescripcion;

        } else if (!descripcion) {

            mostrarError(inputDescripcion, "Debes ingresar una descripción.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputDescripcion;

        } else if (descripcion.length < 10) {

            mostrarError(inputDescripcion, "La descripción debe tener mínimo 10 caracteres.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputDescripcion;

        }

        // =========================
        // COSTO
        // =========================

        if (isNaN(costo) || costo <= 0) {

            mostrarError(inputCosto, "Ingresa un costo válido y positivo.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputCosto;

        }

        // =========================
        // CATEGORÍA / MARCA (obligatorias)
        // =========================

        const inputCategoria = document.querySelector('[name="categoria"]');
        const inputMarca = document.querySelector('[name="marca"]');

        if (inputCategoria && !inputCategoria.value) {

            mostrarError(inputCategoria, "Selecciona una categoría.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputCategoria;

        }

        if (inputMarca && !inputMarca.value) {

            mostrarError(inputMarca, "Selecciona una marca.");
            hayErrores = true;
            primerCampoInvalido = primerCampoInvalido || inputMarca;

        }

        // =========================
        // ETIQUETAS (obligatorio mínimo 1)
        // =========================

        if (etiquetas) {

            const totalSeleccionadas = [...etiquetas.options]
                .filter(o => o.selected)
                .length;

            if (totalSeleccionadas === 0) {

                mostrarError(etiquetas, "Debes seleccionar al menos 1 etiqueta.");
                hayErrores = true;
                primerCampoInvalido = primerCampoInvalido || etiquetas;

            }

        }

        
        // =========================
        // IMÁGENES
        // =========================

        if (inputImagenes) {

            for (const archivo of inputImagenes.files) {

                const pesoMB = archivo.size / 1024 / 1024;

                if (pesoMB > 10) {

                    mostrarError(inputImagenes, `La imagen "${archivo.name}" supera los 10 MB.`);
                    hayErrores = true;
                    primerCampoInvalido = primerCampoInvalido || inputImagenes;

                    break;

                }

            }

        }

        // =========================
        // VIDEOS
        // =========================

        const inputVideos = document.getElementById("videos");

        if (inputVideos) {

            for (const archivo of inputVideos.files) {

                const pesoMB = archivo.size / 1024 / 1024;

                if (pesoMB > 100) {

                    mostrarError(inputVideos, `El video "${archivo.name}" supera los 100 MB.`);
                    hayErrores = true;
                    primerCampoInvalido = primerCampoInvalido || inputVideos;

                    break;
                }

            }

        }

        // =========================
        // CORTE SI HAY ERRORES
        // =========================

        if (hayErrores) {

            e.preventDefault();

            restaurarBoton();

            Swal.fire({
                icon: "error",
                title: "Revisa el formulario",
                text: "Hay campos con errores, corrígelos antes de guardar.",
                confirmButtonText: "Entendido"
            });

            if (primerCampoInvalido) {

                primerCampoInvalido.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

                if (typeof primerCampoInvalido.focus === "function") {
                    primerCampoInvalido.focus();
                }

            }

            return;

        }

        // Todo válido: bloquear botón para evitar doble envío

        bloquearBoton();

    });

}


// =====================================
// BUSCADOR EN TIEMPO REAL (sin partial)
// =====================================

(() => {

    const inputBuscar = document.getElementById("input-buscar-productos");
    const contenedorLista = document.getElementById("lista-productos-container");
    const spinner = document.getElementById("buscador-spinner");

    if (!inputBuscar || !contenedorLista) return;

    let temporizador = null;

    function construirUrl(params) {

        const url = new URL(window.location.href);
        url.search = "";

        if (params.q) url.searchParams.set("q", params.q);
        if (params.page) url.searchParams.set("page", params.page);

        return url;

    }

    function buscarProductos(params) {

        const url = construirUrl(params);

        if (spinner) spinner.classList.remove("oculto");

        fetch(url.toString())

            .then(respuesta => respuesta.text())

            .then(html => {

                const parser = new DOMParser();
                const docNuevo = parser.parseFromString(html, "text/html");

                const nuevoContenedor = docNuevo.getElementById("lista-productos-container");

                if (nuevoContenedor) {
                    contenedorLista.innerHTML = nuevoContenedor.innerHTML;
                }

                window.history.pushState({}, "", url.toString());

            })

            .catch(error => {

                console.error("Error buscando productos:", error);

            })

            .finally(() => {

                if (spinner) spinner.classList.add("oculto");

            });

    }

    // Escribir en el input -> buscar con debounce

    inputBuscar.addEventListener("input", function () {

        clearTimeout(temporizador);

        const valor = this.value.trim();

        temporizador = setTimeout(() => {

            buscarProductos({ q: valor, page: 1 });

        }, 400);

    });

    // Botón "Limpiar"

    document.addEventListener("click", function (e) {

        if (e.target && e.target.id === "btn-limpiar-busqueda") {

            e.preventDefault();

            inputBuscar.value = "";

            buscarProductos({ q: "", page: 1 });

        }

    });

    // Clicks en paginación dentro del contenedor -> también en tiempo real

    contenedorLista.addEventListener("click", function (e) {

        const link = e.target.closest(".link-pagina");

        if (!link) return;

        e.preventDefault();

        const urlDestino = new URL(link.href);

        const page = urlDestino.searchParams.get("page");
        const q = urlDestino.searchParams.get("q") || "";

        buscarProductos({ q, page });

    });

})();

document.addEventListener("DOMContentLoaded", () => {
 
    const checks = document.querySelectorAll(".check-quitar-archivo");
 
    checks.forEach((check) => {
 
        check.addEventListener("change", () => {
 
            const item = check.closest(".archivo-actual-item");
 
            if (!item) return;
 
            item.classList.toggle("marcado-eliminar", check.checked);
 
        });
 
    });
 
});