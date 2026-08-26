let contadorPreguntas =
    document.querySelectorAll(".pregunta-card").length;

function opcionesResultados(selectedValue = "") {

    const resultados =
        document.querySelectorAll('input[name="resultado_nombre[]"]');

    return Array.from(resultados).map((input, index) => {

        const value = String(index + 1);
        const nombre = input.value.trim() || `Resultado ${value}`;
        const selected = value === String(selectedValue) ? "selected" : "";

        return `<option value="${value}" ${selected}>Resultado ${value} - ${nombre}</option>`;

    }).join("");

}

function refrescarSelectsResultados() {

    document.querySelectorAll(".resultado-select").forEach(select => {

        const valorActual = select.value;

        select.innerHTML = opcionesResultados(valorActual);

    });

}

function agregarResultado() {

    const index =
        document.querySelectorAll(".resultado-item").length;

    document
        .getElementById("resultados-container")
        .insertAdjacentHTML(
            "beforeend",
            `
            <div class="resultado-item">

                <input type="hidden" name="resultado_id[]" value="">

                <input
                    type="text"
                    name="resultado_nombre[]"
                    class="form-control"
                    placeholder="Nombre resultado"
                    required>

                <textarea
                    name="resultado_descripcion[]"
                    class="form-control"
                    rows="3"
                    placeholder="Descripción"
                    required></textarea>

                <input
                    type="file"
                    name="resultado_imagen_${index}"
                    class="form-control">

            </div>
            `
        );

    refrescarSelectsResultados();
    actualizarBotonesEliminar();

}

function agregarPregunta() {

    contadorPreguntas++;

    document
        .getElementById("preguntas-container")
        .insertAdjacentHTML(
            "beforeend",
            `
            <div class="pregunta-card">

                <h4>Pregunta ${contadorPreguntas}</h4>

                <input
                    type="text"
                    name="pregunta[]"
                    class="form-control"
                    placeholder="Escriba la pregunta"
                    required>

                <div id="opciones-${contadorPreguntas}">

                    <div class="opcion-item">

                        <input
                            type="text"
                            name="opcion_${contadorPreguntas}[]"
                            class="form-control"
                            placeholder="Texto opción"
                            required>

                        <select
                            name="resultado_${contadorPreguntas}[]"
                            class="form-control resultado-select"
                            required>
                            ${opcionesResultados()}
                        </select>

                    </div>

                </div>

                <button
                    type="button"
                    class="btn btn-secondary"
                    onclick="agregarOpcion(${contadorPreguntas})">
                    + Agregar opción
                </button>

            </div>
            `
        );

    actualizarBotonesEliminar();

}

function agregarOpcion(idPregunta) {

    document
        .getElementById(`opciones-${idPregunta}`)
        .insertAdjacentHTML(
            "beforeend",
            `
            <div class="opcion-item">

                <input
                    type="text"
                    name="opcion_${idPregunta}[]"
                    class="form-control"
                    placeholder="Texto opción"
                    required>

                <select
                    name="resultado_${idPregunta}[]"
                    class="form-control resultado-select"
                    required>
                    ${opcionesResultados()}
                </select>

            </div>
            `
        );

    actualizarBotonesEliminar();

}

function actualizarBotonesEliminar() {

    document.querySelectorAll(".resultado-item").forEach((item, index) => {

        let boton = item.querySelector(".btn-remove-resultado");

        if (index === 0) {

            if (boton) {
                boton.remove();
            }

            return;

        }

        if (!boton) {

            item.insertAdjacentHTML(
                "afterbegin",
                `
                <button
                    type="button"
                    class="btn-remove btn-remove-resultado"
                    onclick="eliminarResultado(this)"
                    title="Eliminar resultado">
                    &times;
                </button>
                `
            );

        }

    });

    document.querySelectorAll(".pregunta-card").forEach((card, index) => {

        let boton = card.querySelector(".btn-remove-pregunta");

        if (index === 0) {

            if (boton) {
                boton.remove();
            }

            return;

        }

        if (!boton) {

            card.insertAdjacentHTML(
                "afterbegin",
                `
                <button
                    type="button"
                    class="btn-remove btn-remove-pregunta"
                    onclick="eliminarPregunta(this)"
                    title="Eliminar pregunta">
                    &times;
                </button>
                `
            );

        }

    });

    document.querySelectorAll('[id^="opciones-"]').forEach(contenedor => {

        contenedor.querySelectorAll(".opcion-item").forEach((item, index) => {

            let boton = item.querySelector(".btn-remove-opcion");

            if (index === 0) {

                if (boton) {
                    boton.remove();
                }

                return;

            }

            if (!boton) {

                item.insertAdjacentHTML(
                    "beforeend",
                    `
                    <button
                        type="button"
                        class="btn-remove btn-remove-opcion"
                        onclick="eliminarOpcion(this)"
                        title="Eliminar opción">
                        &times;
                    </button>
                    `
                );

            }

        });

    });

}

function eliminarResultado(btn) {

    btn.closest(".resultado-item").remove();

    reindexarResultados();
    refrescarSelectsResultados();
    actualizarBotonesEliminar();

}

function eliminarPregunta(btn) {

    btn.closest(".pregunta-card").remove();

    reindexarPreguntas();
    actualizarBotonesEliminar();

}

function eliminarOpcion(btn) {

    btn.closest(".opcion-item").remove();

    actualizarBotonesEliminar();

}

function reindexarResultados() {

    document.querySelectorAll(".resultado-item").forEach((item, index) => {

        const inputImagen =
            item.querySelector('input[type="file"]');

        if (inputImagen) {
            inputImagen.name = `resultado_imagen_${index}`;
        }

    });

}

function reindexarPreguntas() {

    document.querySelectorAll(".pregunta-card").forEach((card, index) => {

        const numero = index + 1;

        const titulo =
            card.querySelector("h4");

        if (titulo) {
            titulo.textContent = `Pregunta ${numero}`;
        }

        const opcionesContainer =
            card.querySelector('[id^="opciones-"]');

        if (opcionesContainer) {
            opcionesContainer.id = `opciones-${numero}`;
        }

        card.querySelectorAll('input[name^="opcion_"]').forEach(input => {
            input.name = `opcion_${numero}[]`;
        });

        card.querySelectorAll('select[name^="resultado_"]').forEach(select => {
            select.name = `resultado_${numero}[]`;
        });

        const botonAgregarOpcion =
            card.querySelector('button[onclick^="agregarOpcion"]');

        if (botonAgregarOpcion) {
            botonAgregarOpcion.setAttribute(
                "onclick",
                `agregarOpcion(${numero})`
            );
        }

    });

    contadorPreguntas =
        document.querySelectorAll(".pregunta-card").length;

}

document.addEventListener("input", function (e) {

    if (e.target.matches('input[name="resultado_nombre[]"]')) {
        refrescarSelectsResultados();
    }

});

document.querySelectorAll(".btn-eliminar").forEach(btn => {

    btn.addEventListener("click", function (e) {

        e.preventDefault();

        const url = this.href;

        Swal.fire({
            title: "¿Eliminar test?",
            text: "Esta acción no se puede deshacer.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar"
        }).then((result) => {

            if (result.isConfirmed) {
                window.location.href = url;
            }

        });

    });

});

function mostrarError(input, mensaje) {

    input.classList.add("input-error");

    const error = document.createElement("span");

    error.className = "error-text";
    error.innerText = mensaje;

    input.insertAdjacentElement("afterend", error);

}

function limpiarErrores() {

    document.querySelectorAll(".error-text").forEach(error => {
        error.remove();
    });

    document.querySelectorAll(".input-error").forEach(input => {
        input.classList.remove("input-error");
    });

}

const formulario = document.getElementById("formTest");

if (formulario) {

    refrescarSelectsResultados();
    actualizarBotonesEliminar();

    formulario.addEventListener("submit", function (e) {

        e.preventDefault();

        let valido = true;

        limpiarErrores();

        const campos =
            formulario.querySelectorAll(
                "input[required], textarea[required], select[required]"
            );

        campos.forEach(campo => {

            if (campo.value.trim() === "") {

                mostrarError(campo, "Este campo es obligatorio.");
                valido = false;

            }

        });

        const titulo =
            formulario.querySelector('input[name="titulo"]');

        if (titulo && titulo.value.trim().length < 5) {
            mostrarError(titulo, "Debe tener mínimo 5 caracteres.");
            valido = false;
        }

        const categoria =
            formulario.querySelector('input[name="categoria"]');

        if (categoria && categoria.value.trim().length < 3) {
            mostrarError(categoria, "Debe tener mínimo 3 caracteres.");
            valido = false;
        }

        const descripcion =
            formulario.querySelector('textarea[name="descripcion"]');

        if (descripcion && descripcion.value.trim().length < 20) {
            mostrarError(descripcion, "Debe tener mínimo 20 caracteres.");
            valido = false;
        }

        document
            .querySelectorAll('input[name="pregunta[]"]')
            .forEach(pregunta => {

                if (pregunta.value.trim().length < 10) {
                    mostrarError(
                        pregunta,
                        "La pregunta debe tener al menos 10 caracteres."
                    );

                    valido = false;
                }

            });

        document
            .querySelectorAll('input[name^="opcion_"]')
            .forEach(opcion => {

                if (opcion.value.trim().length < 2) {
                    mostrarError(opcion, "Ingrese una opción válida.");
                    valido = false;
                }

            });

        document
            .querySelectorAll('select[name^="resultado_"]')
            .forEach(resultado => {

                if (
                    resultado.value.trim() === "" ||
                    Number(resultado.value) <= 0
                ) {
                    mostrarError(resultado, "Seleccione un resultado válido.");
                    valido = false;
                }

            });

        document
            .querySelectorAll('input[name="resultado_nombre[]"]')
            .forEach(resultado => {

                if (resultado.value.trim().length < 3) {
                    mostrarError(resultado, "Debe tener mínimo 3 caracteres.");
                    valido = false;
                }

            });

        document
            .querySelectorAll('textarea[name="resultado_descripcion[]"]')
            .forEach(resultado => {

                if (resultado.value.trim().length < 10) {
                    mostrarError(
                        resultado,
                        "La descripción debe tener al menos 10 caracteres."
                    );

                    valido = false;
                }

            });

        const imagen =
            formulario.querySelector('input[name="imagen"]');

        const editando =
            formulario.dataset.editando === "true";

        if (imagen && imagen.files.length > 0) {

            const archivo = imagen.files[0];

            const tiposPermitidos = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];

            if (!tiposPermitidos.includes(archivo.type)) {
                mostrarError(
                    imagen,
                    "Solo se permiten imágenes JPG, PNG o WEBP."
                );

                valido = false;
            }

            if (archivo.size > 2 * 1024 * 1024) {
                mostrarError(imagen, "La imagen no puede superar los 2 MB.");
                valido = false;
            }

        }

        if (!editando && imagen && imagen.files.length === 0) {
            mostrarError(imagen, "Debes seleccionar una imagen.");
            valido = false;
        }

        if (!valido) {

            Swal.fire({
                icon: "error",
                title: "Formulario con errores",
                text: "Corrige los campos marcados antes de continuar."
            });

            return;

        }

        Swal.fire({
            title: editando ? "¿Actualizar test?" : "¿Guardar test?",
            text: editando
                ? "Se actualizará la información."
                : "Se guardará el nuevo test.",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Sí",
            cancelButtonText: "Cancelar"
        }).then((result) => {

            if (result.isConfirmed) {
                this.submit();
            }

        });

    });

}