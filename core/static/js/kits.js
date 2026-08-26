
document.addEventListener("DOMContentLoaded", function () {


    /* =====================================================
       MENSAJES DJANGO → SWEETALERT
    ===================================================== */

    const mensajes = document.querySelectorAll(
        "#django-messages .django-message"
    );

    mensajes.forEach(function (mensaje) {

        if (!window.Swal) return;

        Swal.fire({
            icon: mensaje.dataset.icon || "success",
            title: mensaje.dataset.title || "",
            timer: 1800,
            showConfirmButton: false
        });

    });



    /* =====================================================
       FORMULARIO PRINCIPAL DEL KIT
    ===================================================== */

    const formulario = document.querySelector(
        'form[method="POST"]:not([action])'
    );


    if (formulario) {

        const nombre = formulario.querySelector(
            '[name="nombre"]'
        );

        const categoria = formulario.querySelector(
            '[name="categoria"]'
        );

        const sku = formulario.querySelector(
            '[name="sku"]'
        );

        const stock = formulario.querySelector(
            '[name="stock"]'
        );

        const descripcion = formulario.querySelector(
            '[name="descripcion"]'
        );

        const descuento = formulario.querySelector(
            '[name="descuento_personalizado"]'
        );

        const imagen = formulario.querySelector(
            '[name="imagen"]'
        );

        const activo = formulario.querySelector(
            '[name="activo"]'
        );



        /* =================================================
           FUNCIONES PARA ERRORES
        ================================================= */

        function limpiarError(input) {

            if (!input) return;

            input.classList.remove("campo-error");
            input.classList.remove("campo-exito");

            const campo = input.closest(".campo");

            if (!campo) return;

            campo.classList.remove("has-error");

            const mensaje =
                campo.querySelector(
                    ".mensaje-error-campo"
                );

            if (mensaje) {
                mensaje.remove();
            }

        }


        function mostrarError(input, texto) {

            if (!input) return;

            limpiarError(input);

            input.classList.add(
                "campo-error"
            );

            const campo =
                input.closest(".campo");

            if (!campo) return;

            campo.classList.add(
                "has-error"
            );

            const mensaje =
                document.createElement("small");

            mensaje.className =
                "mensaje-error-campo";

            mensaje.innerHTML = `
                <i class="fa-solid fa-circle-exclamation"></i>
                ${texto}
            `;

            campo.appendChild(
                mensaje
            );

        }


        function mostrarExito(input) {

            if (!input) return;

            input.classList.remove(
                "campo-error"
            );

            input.classList.add(
                "campo-exito"
            );

        }



        /* =================================================
           VALIDAR NOMBRE
        ================================================= */

        function validarNombre() {

            if (!nombre) return true;

            const valor =
                nombre.value.trim();


            if (valor === "") {

                mostrarError(
                    nombre,
                    "El nombre del kit es obligatorio."
                );

                return false;

            }


            if (valor.length < 3) {

                mostrarError(
                    nombre,
                    "El nombre debe tener mínimo 3 caracteres."
                );

                return false;

            }


            if (valor.length > 150) {

                mostrarError(
                    nombre,
                    "El nombre no puede superar los 150 caracteres."
                );

                return false;

            }


            mostrarExito(nombre);

            return true;

        }



        /* =================================================
           VALIDAR CATEGORÍA
        ================================================= */

        function validarCategoria() {

            if (!categoria) return true;


            if (categoria.value === "") {

                mostrarError(
                    categoria,
                    "Debes seleccionar una categoría."
                );

                return false;

            }


            mostrarExito(categoria);

            return true;

        }



        /* =================================================
           VALIDAR SKU
        ================================================= */

        function validarSKU() {

            if (!sku) return true;

            const valor =
                sku.value.trim();


            /*
             * SKU opcional.
             * Si está vacío, Django lo genera.
             */

            if (valor === "") {

                limpiarError(sku);

                return true;

            }


            if (valor.length < 2) {

                mostrarError(
                    sku,
                    "El SKU debe tener mínimo 2 caracteres."
                );

                return false;

            }


            if (valor.length > 50) {

                mostrarError(
                    sku,
                    "El SKU no puede superar los 50 caracteres."
                );

                return false;

            }


            /*
             * Solo letras, números,
             * guiones y guiones bajos.
             */

            const formatoSKU =
                /^[A-Za-z0-9_-]+$/;


            if (!formatoSKU.test(valor)) {

                mostrarError(
                    sku,
                    "El SKU solo puede contener letras, números, guiones y guiones bajos."
                );

                return false;

            }


            mostrarExito(sku);

            return true;

        }



        /* =================================================
           AVISO SKU AUTOMÁTICO
        ================================================= */

        function mostrarSkuGenerado() {

            if (!sku) return;


            const valor =
                sku.value.trim();


            const campo =
                sku.closest(".campo");


            if (!campo) return;


            /*
             * Si escribió un SKU,
             * quitar aviso.
             */

            if (valor !== "") {

                const aviso =
                    campo.querySelector(
                        ".sku-generado"
                    );

                if (aviso) {
                    aviso.remove();
                }

                return;

            }


            /*
             * Si está vacío,
             * mostrar aviso.
             */

            let aviso =
                campo.querySelector(
                    ".sku-generado"
                );


            if (!aviso) {

                aviso =
                    document.createElement(
                        "small"
                    );

                aviso.className =
                    "sku-generado";

                aviso.innerHTML = `
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                    El SKU se generará automáticamente al guardar.
                `;

                campo.appendChild(
                    aviso
                );

            }

        }



        /* =================================================
           VALIDAR STOCK
        ================================================= */

        function validarStock() {

            if (!stock) return true;


            const valor =
                stock.value.trim();


            if (valor === "") {

                mostrarError(
                    stock,
                    "El stock es obligatorio."
                );

                return false;

            }


            const numero =
                Number(valor);


            if (!Number.isInteger(numero)) {

                mostrarError(
                    stock,
                    "El stock debe ser un número entero."
                );

                return false;

            }


            if (numero < 0) {

                mostrarError(
                    stock,
                    "El stock no puede ser negativo."
                );

                return false;

            }


            mostrarExito(stock);

            return true;

        }



        /* =================================================
           VALIDAR DESCRIPCIÓN
        ================================================= */

        function validarDescripcion() {

            if (!descripcion) return true;


            const valor =
                descripcion.value.trim();


            /*
             * Descripción obligatoria.
             */

            if (valor === "") {

                mostrarError(
                    descripcion,
                    "La descripción del kit es obligatoria."
                );

                return false;

            }


            if (valor.length < 10) {

                mostrarError(
                    descripcion,
                    "La descripción debe tener mínimo 10 caracteres."
                );

                return false;

            }


            if (valor.length > 2000) {

                mostrarError(
                    descripcion,
                    "La descripción no puede superar los 2000 caracteres."
                );

                return false;

            }


            mostrarExito(
                descripcion
            );

            return true;

        }



        /* =================================================
           VALIDAR DESCUENTO
        ================================================= */

        function validarDescuento() {

            if (!descuento) return true;


            const valor =
                descuento.value.trim();


            /*
             * El descuento es opcional.
             */

            if (valor === "") {

                limpiarError(
                    descuento
                );

                return true;

            }


            /*
             * Permite:
             *
             * 10
             * 10.5
             * 10,5
             */

            const numero =
                Number(
                    valor.replace(",", ".")
                );


            if (isNaN(numero)) {

                mostrarError(
                    descuento,
                    "Ingresa un descuento válido."
                );

                return false;

            }


            if (numero < 0 || numero > 100) {

                mostrarError(
                    descuento,
                    "El descuento debe estar entre 0% y 100%."
                );

                return false;

            }


            mostrarExito(
                descuento
            );

            return true;

        }



        /* =================================================
           VALIDAR IMAGEN
        ================================================= */

        function validarImagen() {

            if (!imagen) return true;


            /*
             * Imagen opcional.
             */

            if (
                !imagen.files ||
                imagen.files.length === 0
            ) {

                limpiarError(
                    imagen
                );

                return true;

            }


            const archivo =
                imagen.files[0];


            const formatosPermitidos = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];


            if (
                !formatosPermitidos.includes(
                    archivo.type
                )
            ) {

                mostrarError(
                    imagen,
                    "La imagen debe ser JPG, PNG o WEBP."
                );

                return false;

            }


            /*
             * Máximo 5 MB.
             */

            const maximo =
                5 * 1024 * 1024;


            if (archivo.size > maximo) {

                mostrarError(
                    imagen,
                    "La imagen no puede superar los 5 MB."
                );

                return false;

            }


            mostrarExito(
                imagen
            );

            return true;

        }



        /* =================================================
           CONTAR PRODUCTOS DEL KIT
        ================================================= */

        function obtenerCantidadProductos() {

            return document.querySelectorAll(
                ".item-kit"
            ).length;

        }



        /* =================================================
           VALIDAR PRODUCTOS
        ================================================= */

        function validarProductosKit() {

            const cantidad =
                obtenerCantidadProductos();


            /*
             * Si no hay productos y está activo,
             * no permitimos guardar como activo.
             */

            if (
                activo &&
                activo.checked &&
                cantidad === 0
            ) {

                activo.checked = false;


                if (window.Swal) {

                    Swal.fire({

                        icon: "warning",

                        title: "Kit sin productos",

                        text:
                            "Un kit no puede estar activo si no tiene productos.",

                        confirmButtonText:
                            "Entendido",

                        confirmButtonColor:
                            "#df6d86"

                    });

                }


                return false;

            }


            return true;

        }



        /* =================================================
           VALIDAR TODO EL FORMULARIO
        ================================================= */

        function validarFormulario() {

            const resultados = [

                validarNombre(),

                validarCategoria(),

                validarSKU(),

                validarStock(),

                validarDescripcion(),

                validarDescuento(),

                validarImagen()

            ];


            return !resultados.includes(
                false
            );

        }



        /* =================================================
           EVENTOS DE VALIDACIÓN
        ================================================= */

        if (nombre) {

            nombre.addEventListener(
                "input",
                validarNombre
            );

            nombre.addEventListener(
                "blur",
                validarNombre
            );

        }


        if (categoria) {

            categoria.addEventListener(
                "change",
                validarCategoria
            );

        }


        if (sku) {

            sku.addEventListener(
                "input",
                function () {

                    validarSKU();

                    mostrarSkuGenerado();

                }
            );


            sku.addEventListener(
                "blur",
                function () {

                    validarSKU();

                    mostrarSkuGenerado();

                }
            );


            /*
             * Mostrar aviso al cargar.
             */

            mostrarSkuGenerado();

        }


        if (stock) {

            stock.addEventListener(
                "input",
                validarStock
            );

            stock.addEventListener(
                "blur",
                validarStock
            );

        }


        if (descripcion) {

            descripcion.addEventListener(
                "input",
                validarDescripcion
            );

            descripcion.addEventListener(
                "blur",
                validarDescripcion
            );

        }


        if (descuento) {

            descuento.addEventListener(
                "input",
                validarDescuento
            );

            descuento.addEventListener(
                "blur",
                validarDescuento
            );

        }


        if (imagen) {

            imagen.addEventListener(
                "change",
                validarImagen
            );

        }



        /* =================================================
           SUBMIT FORMULARIO PRINCIPAL
        ================================================= */

        formulario.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();


                /*
                 * Primero validar campos.
                 */

                const valido =
                    validarFormulario();


                if (!valido) {

                    if (window.Swal) {

                        Swal.fire({

                            icon: "error",

                            title:
                                "Revisa el formulario",

                            text:
                                "Hay campos que necesitan ser corregidos.",

                            confirmButtonText:
                                "Entendido",

                            confirmButtonColor:
                                "#df6d86"

                        });

                    }


                    /*
                     * Ir al primer error.
                     */

                    const primerError =
                        formulario.querySelector(
                            ".campo-error"
                        );


                    if (primerError) {

                        primerError.scrollIntoView({
                            behavior: "smooth",
                            block: "center"
                        });

                        primerError.focus();

                    }


                    return;

                }


                /*
                 * Validar productos.
                 */

                if (!validarProductosKit()) {

                    return;

                }


                /*
                 * Determinar si es edición.
                 */

                const kitId =
                    formulario.querySelector(
                        '[name="kit_id"]'
                    );


                const editando =
                    kitId &&
                    kitId.value !== "";


                /*
                 * Si SweetAlert no está disponible,
                 * enviar directamente.
                 */

                if (!window.Swal) {

                    formulario.submit();

                    return;

                }


                /* =========================================
                   CONFIRMACIÓN
                ========================================= */

                Swal.fire({

                    icon: "question",

                    title:
                        editando
                            ? "¿Actualizar kit?"
                            : "¿Guardar kit?",

                    text:
                        editando
                            ? "Se actualizará la información del kit."
                            : "Se creará un nuevo kit.",

                    showCancelButton: true,

                    confirmButtonText:
                        editando
                            ? "Sí, actualizar"
                            : "Sí, guardar",

                    cancelButtonText:
                        "Cancelar",

                    confirmButtonColor:
                        "#df6d86",

                    cancelButtonColor:
                        "#8b8593",

                    reverseButtons:
                        true

                }).then(function (result) {

                    if (result.isConfirmed) {

                        formulario.submit();

                    }

                });

            }
        );

    }



    /* =====================================================
       BUSCADOR DE PRODUCTOS
    ===================================================== */

    const buscador =
        document.getElementById(
            "buscarProducto"
        );


    if (buscador) {

        buscador.addEventListener(
            "keyup",
            function () {

                const texto =
                    this.value
                        .toLowerCase()
                        .trim();


                document
                    .querySelectorAll(
                        "#listaProductos .producto-card"
                    )
                    .forEach(function (card) {

                        const titulo =
                            card.querySelector(
                                "h4"
                            );


                        const nombre =
                            titulo
                                ? titulo.textContent
                                    .toLowerCase()
                                : "";


                        card.hidden =
                            !nombre.includes(
                                texto
                            );

                    });

            }
        );

    }



    /* =====================================================
       MOSTRAR / OCULTAR PRODUCTOS
    ===================================================== */

    const toggleProductosBtn =
        document.getElementById(
            "toggleProductos"
        );


    const listaProductos =
        document.getElementById(
            "listaProductos"
        );


    if (
        toggleProductosBtn &&
        listaProductos
    ) {

        toggleProductosBtn.addEventListener(
            "click",
            function () {

                const oculto =
                    listaProductos.hidden;


                listaProductos.hidden =
                    !oculto;


                toggleProductosBtn.innerHTML =
                    oculto

                        ? '<i class="fa-solid fa-eye-slash"></i> Ocultar productos'

                        : '<i class="fa-solid fa-eye"></i> Mostrar productos';

            }
        );

    }



    /* =====================================================
       MOSTRAR / OCULTAR INFORMACIÓN
    ===================================================== */

    document
        .querySelectorAll(
            ".btn-toggle-info"
        )
        .forEach(function (boton) {

            boton.addEventListener(
                "click",
                function () {

                    const targetId =
                        boton.getAttribute(
                            "data-info"
                        );


                    const panel =
                        document.getElementById(
                            targetId
                        );


                    if (!panel) return;


                    const oculto =
                        panel.hidden;


                    panel.hidden =
                        !oculto;


                    boton.innerHTML =
                        oculto

                            ? '<i class="fa-solid fa-eye-slash"></i> Ocultar informacion'

                            : '<i class="fa-solid fa-eye"></i> Mostrar informacion';

                }
            );

        });



    /* =====================================================
       TABS DE LOS KITS
    ===================================================== */

    document
        .querySelectorAll(
            ".kit-tabs"
        )
        .forEach(function (tabsContainer) {

            const botones =
                tabsContainer.querySelectorAll(
                    ".tab-btn"
                );


            botones.forEach(function (boton) {

                boton.addEventListener(
                    "click",
                    function () {

                        const targetId =
                            boton.getAttribute(
                                "data-tab"
                            );


                        botones.forEach(
                            function (tabButton) {

                                tabButton.classList.remove(
                                    "active"
                                );

                            }
                        );


                        boton.classList.add(
                            "active"
                        );


                        tabsContainer
                            .querySelectorAll(
                                ".tab-panel"
                            )
                            .forEach(
                                function (panel) {

                                    panel.classList.toggle(
                                        "active",
                                        panel.id === targetId
                                    );

                                }
                            );

                    }
                );

            });

        });



    /* =====================================================
       AGREGAR PRODUCTO AL KIT
    ===================================================== */

    document
        .querySelectorAll(
            'form[action*="agregar_producto_kit"]'
        )
        .forEach(function (
            formularioProducto
        ) {

            formularioProducto.addEventListener(
                "submit",
                function (event) {

                    const variante =
                        formularioProducto.querySelector(
                            '[name="variante"]'
                        );


                    const cantidad =
                        formularioProducto.querySelector(
                            '[name="cantidad"]'
                        );


                    /* =====================================
                       VARIANTE
                    ===================================== */

                    if (
                        variante &&
                        variante.value === ""
                    ) {

                        event.preventDefault();


                        if (window.Swal) {

                            Swal.fire({

                                icon: "warning",

                                title:
                                    "Selecciona una variante",

                                text:
                                    "Debes seleccionar una variante antes de agregar el producto.",

                                confirmButtonText:
                                    "Entendido",

                                confirmButtonColor:
                                    "#df6d86"

                            });

                        }


                        variante.focus();

                        return;

                    }


                    /* =====================================
                       CANTIDAD
                    ===================================== */

                    const numeroCantidad =
                        cantidad
                            ? Number(
                                cantidad.value
                            )
                            : 1;


                    if (
                        cantidad &&
                        (
                            cantidad.value === "" ||
                            !Number.isInteger(
                                numeroCantidad
                            ) ||
                            numeroCantidad < 1
                        )
                    ) {

                        event.preventDefault();


                        if (window.Swal) {

                            Swal.fire({

                                icon: "warning",

                                title:
                                    "Cantidad inválida",

                                text:
                                    "La cantidad debe ser un número entero mayor o igual a 1.",

                                confirmButtonText:
                                    "Entendido",

                                confirmButtonColor:
                                    "#df6d86"

                            });

                        }


                        cantidad.focus();

                        return;

                    }


                    /* =====================================
                       CONFIRMACIÓN
                    ===================================== */

                    event.preventDefault();


                    if (!window.Swal) {

                        formularioProducto.submit();

                        return;

                    }


                    Swal.fire({

                        icon: "question",

                        title:
                            "¿Agregar producto?",

                        text:
                            "El producto se agregará al kit.",

                        showCancelButton:
                            true,

                        confirmButtonText:
                            "Sí, agregar",

                        cancelButtonText:
                            "Cancelar",

                        confirmButtonColor:
                            "#df6d86",

                        cancelButtonColor:
                            "#8b8593",

                        reverseButtons:
                            true

                    }).then(function (result) {

                        if (
                            result.isConfirmed
                        ) {

                            formularioProducto.submit();

                        }

                    });

                }
            );

        });

});



/* =========================================================
   ELIMINAR KIT
========================================================= */

window.eliminarKit = function (
    id,
    nombre
) {

    if (!window.Swal) {

        if (
            window.confirm(
                "¿Eliminar kit " +
                nombre +
                "?"
            )
        ) {

            window.location.href =
                "/dashboard/kits/eliminar/" +
                id +
                "/";

        }

        return;

    }


    Swal.fire({

        title:
            "¿Eliminar kit?",

        html:
            `Se eliminará <b>${nombre}</b>`,

        icon:
            "warning",

        showCancelButton:
            true,

        confirmButtonText:
            "Sí, eliminar",

        cancelButtonText:
            "Cancelar",

        confirmButtonColor:
            "#df6d86",

        cancelButtonColor:
            "#8b8593",

        reverseButtons:
            true

    }).then(function (result) {

        if (
            result.isConfirmed
        ) {

            window.location.href =
                "/dashboard/kits/eliminar/" +
                id +
                "/";

        }

    });

};
