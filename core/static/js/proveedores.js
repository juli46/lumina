document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("formProveedor");

    const marca = document.getElementById("marca");
    const encargado = document.getElementById("encargado");
    const telefono = document.getElementById("telefono");
    const correo = document.getElementById("correo");

    const tbody = document.getElementById("tablaProveedoresBody");
    const noResultados = document.getElementById("noResultados");
    const buscarInput = document.getElementById("buscarProveedor");
    const tablaCard = document.querySelector(".proveedores-table-card");


    /*
    ==================================================
    MOSTRAR / OCULTAR FORMULARIO
    ==================================================
    */

    window.mostrarFormulario = function () {

        const formulario = document.getElementById(
            "formularioProveedor"
        );

        const overlay = document.getElementById(
            "formOverlay"
        );

        if (formulario) {
            formulario.classList.add("active");

            formulario.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }

        if (overlay) {
            overlay.classList.add("active");
        }
    };


    window.ocultarFormulario = function () {

        const formulario = document.getElementById(
            "formularioProveedor"
        );

        const overlay = document.getElementById(
            "formOverlay"
        );

        if (formulario) {
            formulario.classList.remove("active");
        }

        if (overlay) {
            overlay.classList.remove("active");
        }
    };


    /*
    ==================================================
    CREAR ERROR DEBAJO DEL INPUT
    ==================================================
    */

    function mostrarError(input, mensaje) {

        if (!input) return;

        input.classList.add("input-error");

        const contenedor = input.closest(".form-group");

        if (!contenedor) return;

        let error = contenedor.querySelector(
            ".error-text"
        );

        if (!error) {

            error = document.createElement("small");

            error.className = "error-text";

            contenedor.appendChild(error);
        }

        error.textContent = mensaje;
    }


    /*
    ==================================================
    LIMPIAR ERROR
    ==================================================
    */

    function limpiarError(input) {

        if (!input) return;

        input.classList.remove("input-error");

        const contenedor = input.closest(".form-group");

        if (!contenedor) return;

        const error = contenedor.querySelector(
            ".error-text"
        );

        if (error) {
            error.remove();
        }
    }


    /*
    ==================================================
    VALIDAR MARCA
    ==================================================
    */

    function validarMarca() {

        if (!marca) return true;

        const valor = marca.value.trim();

        if (valor === "") {

            mostrarError(
                marca,
                "La marca es obligatoria."
            );

            return false;
        }

        if (valor.length < 2) {

            mostrarError(
                marca,
                "La marca debe tener al menos 2 caracteres."
            );

            return false;
        }

        if (valor.length > 100) {

            mostrarError(
                marca,
                "La marca no puede superar los 100 caracteres."
            );

            return false;
        }

        limpiarError(marca);

        return true;
    }


    /*
    ==================================================
    VALIDAR ENCARGADO
    ==================================================
    */

    function validarEncargado() {

        if (!encargado) return true;

        const valor = encargado.value.trim();

        if (valor === "") {

            mostrarError(
                encargado,
                "El nombre del encargado es obligatorio."
            );

            return false;
        }

        const regex =
            /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/;

        if (!regex.test(valor)) {

            mostrarError(
                encargado,
                "Solo se permiten letras y espacios."
            );

            return false;
        }

        if (valor.length < 2) {

            mostrarError(
                encargado,
                "El nombre debe tener al menos 2 caracteres."
            );

            return false;
        }

        if (valor.length > 100) {

            mostrarError(
                encargado,
                "El nombre no puede superar los 100 caracteres."
            );

            return false;
        }

        limpiarError(encargado);

        return true;
    }


    /*
    ==================================================
    VALIDAR TELÉFONO
    ==================================================
    */

    function validarTelefono() {

        if (!telefono) return true;

        const valor = telefono.value.trim();

        if (valor === "") {

            mostrarError(
                telefono,
                "El teléfono es obligatorio."
            );

            return false;
        }

        if (!/^[0-9]+$/.test(valor)) {

            mostrarError(
                telefono,
                "El teléfono solo puede contener números."
            );

            return false;
        }

        if (valor.length < 7) {

            mostrarError(
                telefono,
                "El teléfono debe tener mínimo 7 números."
            );

            return false;
        }

        if (valor.length > 10) {

            mostrarError(
                telefono,
                "El teléfono debe tener máximo 10 números."
            );

            return false;
        }

        limpiarError(telefono);

        return true;
    }


    /*
    ==================================================
    VALIDAR CORREO
    ==================================================
    */

    function validarCorreo() {

        if (!correo) return true;

        const valor = correo.value.trim();

        if (valor === "") {

            mostrarError(
                correo,
                "El correo electrónico es obligatorio."
            );

            return false;
        }

        const regex =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!regex.test(valor)) {

            mostrarError(
                correo,
                "Ingresa un correo electrónico válido."
            );

            return false;
        }

        limpiarError(correo);

        return true;
    }


    /*
    ==================================================
    VALIDACIÓN EN TIEMPO REAL
    ==================================================
    */

    if (marca) {

        marca.addEventListener(
            "input",
            validarMarca
        );

        marca.addEventListener(
            "blur",
            validarMarca
        );
    }


    if (encargado) {

        encargado.addEventListener(
            "input",
            validarEncargado
        );

        encargado.addEventListener(
            "blur",
            validarEncargado
        );
    }


    if (telefono) {

        telefono.addEventListener(
            "input",
            function () {

                /*
                Eliminar cualquier carácter
                que no sea número.
                */

                this.value =
                    this.value.replace(/\D/g, "");

                validarTelefono();
            }
        );

        telefono.addEventListener(
            "blur",
            validarTelefono
        );
    }


    if (correo) {

        correo.addEventListener(
            "input",
            validarCorreo
        );

        correo.addEventListener(
            "blur",
            validarCorreo
        );
    }


    /*
    ==================================================
    VALIDACIÓN FINAL DEL FORMULARIO
    ==================================================
    */

    if (form) {

        form.addEventListener(
            "submit",
            function (e) {

                const marcaValida =
                    validarMarca();

                const encargadoValido =
                    validarEncargado();

                const telefonoValido =
                    validarTelefono();

                const correoValido =
                    validarCorreo();


                /*
                ------------------------------------------
                SI EXISTE ALGÚN ERROR
                ------------------------------------------
                */

                if (
                    !marcaValida ||
                    !encargadoValido ||
                    !telefonoValido ||
                    !correoValido
                ) {

                    e.preventDefault();

                    Swal.fire({

                        icon: "error",

                        title: "No se puede guardar",

                        text:
                            "Revisa los campos marcados en rojo.",

                        confirmButtonText:
                            "Entendido",

                        confirmButtonColor:
                            "#df6d86"

                    });

                    return;
                }


                /*
                ------------------------------------------
                TODO CORRECTO
                ------------------------------------------
                */

                e.preventDefault();

                Swal.fire({

                    icon: "success",

                    title: "Todo está correcto",

                    text:
                        "Los datos del proveedor son válidos. ¿Deseas guardar la información?",

                    showCancelButton: true,

                    confirmButtonText:
                        "Sí, guardar",

                    cancelButtonText:
                        "Revisar",

                    confirmButtonColor:
                        "#df6d86",

                    cancelButtonColor:
                        "#8b8593",

                    reverseButtons:
                        true

                }).then(function (resultado) {

                    if (resultado.isConfirmed) {

                        form.submit();

                    }

                });

            }
        );
    }


    /*
    ==================================================
    CONFIRMACIÓN PARA ELIMINAR
    ==================================================
    */

    const formulariosEliminar =
        document.querySelectorAll(
            ".form-eliminar-proveedor"
        );


    formulariosEliminar.forEach(
        function (formulario) {

            formulario.addEventListener(
                "submit",
                function (e) {

                    e.preventDefault();

                    Swal.fire({

                        icon: "warning",

                        title:
                            "¿Eliminar proveedor?",

                        text:
                            "Esta acción no se puede deshacer.",

                        showCancelButton:
                            true,

                        confirmButtonText:
                            "Sí, eliminar",

                        cancelButtonText:
                            "Cancelar",

                        confirmButtonColor:
                            "#e11d48",

                        cancelButtonColor:
                            "#8b8593",

                        reverseButtons:
                            true

                    }).then(function (resultado) {

                        if (resultado.isConfirmed) {

                            formulario.submit();

                        }

                    });

                }
            );

        }
    );


    /*
    ==================================================
    MENSAJES DE DJANGO CON SWEETALERT
    ==================================================
    */

    const mensajes =
        document.querySelectorAll(
            ".django-message"
        );


    mensajes.forEach(
        function (mensaje) {

            const texto =
                mensaje.dataset.message;

            const tipo =
                mensaje.dataset.tag || "success";


            let icono = "success";
            let titulo = "¡Listo!";


            if (
                tipo.includes("error") ||
                tipo.includes("danger")
            ) {

                icono = "error";
                titulo = "Ha ocurrido un error";

            } else if (
                tipo.includes("warning")
            ) {

                icono = "warning";
                titulo = "Atención";

            } else if (
                tipo.includes("info")
            ) {

                icono = "info";
                titulo = "Información";
            }


            Swal.fire({

                icon: icono,

                title: titulo,

                text: texto,

                confirmButtonText:
                    "Aceptar",

                confirmButtonColor:
                    "#df6d86"

            });

        }
    );


    /*
    ==================================================
    ACTUALIZAR TARJETAS DE RESUMEN (TOTAL / ACTIVOS / INACTIVOS)
    ==================================================
    */

    function actualizarStats() {

        const filas = tbody
            ? Array.from(tbody.querySelectorAll("tr"))
            : [];

        const total = filas.length;

        let activos = 0;

        filas.forEach(function (fila) {

            if (fila.querySelector(".status-badge.activo")) {
                activos++;
            }

        });

        const inactivos = total - activos;

        const elTotal = document.getElementById("statTotal");
        const elActivos = document.getElementById("statActivos");
        const elInactivos = document.getElementById("statInactivos");

        if (elTotal) elTotal.textContent = total;
        if (elActivos) elActivos.textContent = activos;
        if (elInactivos) elInactivos.textContent = inactivos;
    }


    /*
    ==================================================
    BUSCADOR + PAGINACIÓN DE LA TABLA
    ==================================================
    */

    const FILAS_POR_PAGINA = 6;

    let paginaActual = 1;

    const filasOriginales = tbody
        ? Array.from(tbody.querySelectorAll("tr"))
        : [];


    function normalizar(texto) {

        return texto
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }


    function obtenerFilasFiltradas() {

        const termino = buscarInput
            ? normalizar(buscarInput.value.trim())
            : "";

        if (termino === "") {
            return filasOriginales;
        }

        return filasOriginales.filter(function (fila) {

            const marcaTexto = fila.querySelector(".marca-cell strong");
            const encargadoTexto = fila.querySelector(".contact-cell");

            const textoMarca = marcaTexto
                ? normalizar(marcaTexto.textContent)
                : "";

            const textoEncargado = encargadoTexto
                ? normalizar(encargadoTexto.textContent)
                : "";

            return (
                textoMarca.includes(termino) ||
                textoEncargado.includes(termino)
            );
        });
    }


    function obtenerContenedorPaginacion() {

        let contenedor = document.getElementById(
            "paginacionProveedores"
        );

        if (!contenedor && tablaCard) {

            contenedor = document.createElement("div");
            contenedor.id = "paginacionProveedores";
            contenedor.className = "paginacion";

            tablaCard.appendChild(contenedor);
        }

        return contenedor;
    }


    function renderPaginacion(totalPaginas, totalResultados) {

        const contenedor = obtenerContenedorPaginacion();

        if (!contenedor) return;

        contenedor.innerHTML = "";

        if (totalResultados === 0 || totalPaginas <= 1) {
            contenedor.style.display = "none";
            return;
        }

        contenedor.style.display = "flex";

        const btnAnterior = document.createElement("button");
        btnAnterior.type = "button";
        btnAnterior.className = "pagina-btn";
        btnAnterior.setAttribute("aria-label", "Página anterior");
        btnAnterior.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
        btnAnterior.disabled = paginaActual === 1;

        btnAnterior.addEventListener("click", function () {
            paginaActual--;
            renderTabla();
        });

        contenedor.appendChild(btnAnterior);

        for (let i = 1; i <= totalPaginas; i++) {

            const boton = document.createElement("button");
            boton.type = "button";
            boton.className =
                "pagina-btn" + (i === paginaActual ? " activa" : "");
            boton.textContent = i;

            boton.addEventListener("click", function () {
                paginaActual = i;
                renderTabla();
            });

            contenedor.appendChild(boton);
        }

        const btnSiguiente = document.createElement("button");
        btnSiguiente.type = "button";
        btnSiguiente.className = "pagina-btn";
        btnSiguiente.setAttribute("aria-label", "Página siguiente");
        btnSiguiente.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
        btnSiguiente.disabled = paginaActual === totalPaginas;

        btnSiguiente.addEventListener("click", function () {
            paginaActual++;
            renderTabla();
        });

        contenedor.appendChild(btnSiguiente);
    }


    function renderTabla() {

        if (!tbody) return;

        const filasFiltradas = obtenerFilasFiltradas();

        const totalPaginas = Math.max(
            1,
            Math.ceil(filasFiltradas.length / FILAS_POR_PAGINA)
        );

        if (paginaActual > totalPaginas) paginaActual = totalPaginas;
        if (paginaActual < 1) paginaActual = 1;

        filasOriginales.forEach(function (fila) {
            fila.style.display = "none";
        });

        const inicio = (paginaActual - 1) * FILAS_POR_PAGINA;

        const filasPagina = filasFiltradas.slice(
            inicio,
            inicio + FILAS_POR_PAGINA
        );

        filasPagina.forEach(function (fila) {
            fila.style.display = "";
        });

        if (noResultados) {
            noResultados.style.display =
                filasFiltradas.length === 0 ? "block" : "none";
        }

        renderPaginacion(totalPaginas, filasFiltradas.length);
    }


    if (buscarInput) {

        buscarInput.addEventListener("input", function () {
            paginaActual = 1;
            renderTabla();
        });
    }


    actualizarStats();
    renderTabla();

});