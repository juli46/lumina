document.addEventListener("DOMContentLoaded", function () {

    /*
    ==========================================================
    TOASTS
    ==========================================================
    */

    function obtenerContenedorToast() {

        let contenedor = document.querySelector(".toast-contenedor");

        if (!contenedor) {
            contenedor = document.createElement("div");
            contenedor.className = "toast-contenedor";
            document.body.appendChild(contenedor);
        }

        return contenedor;
    }


    function mostrarToast(mensaje, tipo = "error", titulo = null) {

        const contenedor = obtenerContenedorToast();
        const toast = document.createElement("div");

        toast.className = `toast toast-${tipo}`;

        const icono =
            tipo === "exito"
                ? "fa-circle-check"
                : "fa-circle-exclamation";

        const tituloDefault =
            tipo === "exito"
                ? "Listo"
                : "Carrito";

        toast.innerHTML = `
            <div class="toast-icono">
                <i class="fa-solid ${icono}"></i>
            </div>

            <div class="toast-texto">
                <strong>${titulo || tituloDefault}</strong>
                ${mensaje}
            </div>

            <button
                type="button"
                class="toast-cerrar"
                aria-label="Cerrar"
            >
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;

        contenedor.appendChild(toast);

        requestAnimationFrame(function () {
            toast.classList.add("toast-visible");
        });


        function cerrarToast() {

            toast.classList.remove("toast-visible");
            toast.classList.add("toast-saliendo");

            setTimeout(function () {
                toast.remove();
            }, 250);
        }


        const temporizador = setTimeout(
            cerrarToast,
            4000
        );


        const botonCerrar =
            toast.querySelector(".toast-cerrar");

        if (botonCerrar) {

            botonCerrar.addEventListener(
                "click",
                function () {

                    clearTimeout(temporizador);

                    cerrarToast();
                }
            );
        }
    }


    /*
    ==========================================================
    CSRF
    ==========================================================
    */

    function obtenerCSRF() {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith("csrftoken=")) {

                return decodeURIComponent(
                    cookie.substring("csrftoken=".length)
                );
            }
        }

        return "";
    }


    /*
    ==========================================================
    FORMATEAR PRECIO
    ==========================================================
    */

    function formatearPrecio(valor) {

        return "$" + Number(valor).toLocaleString("es-CO");
    }


    /*
    ==========================================================
    ACTUALIZAR CONTADOR NAVBAR
    ==========================================================
    */

    function actualizarContador(cantidad) {

        const contador =
            document.getElementById("contador-carrito");

        if (!contador) {
            return;
        }

        contador.textContent = cantidad;

        if (Number(cantidad) <= 0) {

            contador.classList.add("vacio");

        } else {

            contador.classList.remove("vacio");
            contador.classList.add("actualizado");

            setTimeout(function () {

                contador.classList.remove("actualizado");

            }, 200);
        }
    }


    /*
    ==========================================================
    PETICIÓN
    ==========================================================
    */

    async function enviarPeticion(url) {

        try {

            const respuesta = await fetch(url, {

                method: "POST",

                headers: {

                    "X-CSRFToken": obtenerCSRF(),

                    "X-Requested-With": "XMLHttpRequest",

                    "Content-Type": "application/json"
                },

                body: JSON.stringify({})
            });


            const tipoContenido =
                respuesta.headers.get("content-type") || "";


            if (!tipoContenido.includes("application/json")) {

                throw new Error(
                    "El servidor no devolvió una respuesta válida."
                );
            }


            const datos = await respuesta.json();


            /*
            --------------------------------------------------
            SESIÓN NO INICIADA
            --------------------------------------------------
            */

            if (respuesta.status === 401) {

                mostrarLogin();

                throw new Error(
                    "__LOGIN_MOSTRADO__"
                );
            }


            /*
            --------------------------------------------------
            ERROR DEL SERVIDOR
            --------------------------------------------------
            */

            if (!respuesta.ok || !datos.ok) {

                throw new Error(
                    datos.mensaje ||
                    "No se pudo actualizar el carrito."
                );
            }


            return datos;

        } catch (error) {

            if (
                error.message ===
                "__LOGIN_MOSTRADO__"
            ) {

                throw error;
            }


            if (
                error instanceof TypeError
            ) {

                throw new Error(
                    "No se pudo conectar con el servidor."
                );
            }


            throw error;
        }
    }


    /*
    ==========================================================
    LOGIN
    ==========================================================
    */

    function mostrarLogin() {

        if (typeof Swal !== "undefined") {

            Swal.fire({

                icon: "warning",

                title: "Inicia sesión 💕",

                text:
                    "Debes iniciar sesión para modificar tu carrito.",

                showCancelButton: true,

                confirmButtonText:
                    "Iniciar sesión",

                cancelButtonText:
                    "Seguir comprando",

                reverseButtons: true

            }).then(function (resultado) {

                if (resultado.isConfirmed) {

                    window.location.href = "/login/";
                }
            });

            return;
        }


        const confirmar =
            window.confirm(
                "Debes iniciar sesión para continuar. ¿Quieres iniciar sesión?"
            );


        if (confirmar) {

            window.location.href = "/login/";
        }
    }


    /*
    ==========================================================
    ACTUALIZAR SUBTOTAL ITEM
    ==========================================================
    */

    function actualizarSubtotalItem(
        itemId,
        subtotal
    ) {

        const elemento =
            document.getElementById(
                "subtotal-" + itemId
            );


        if (!elemento) {
            return;
        }


        elemento.textContent =
            formatearPrecio(subtotal);
    }


    /*
    ==========================================================
    AUMENTAR CANTIDAD
    ==========================================================
    */

    document
        .querySelectorAll(".btn-aumentar")
        .forEach(function (boton) {

            boton.addEventListener(
                "click",
                async function () {

                    const itemId =
                        this.dataset.itemId;


                    const cantidad =
                        document.getElementById(
                            "cantidad-" + itemId
                        );


                    this.disabled = true;


                    try {

                        const datos =
                            await enviarPeticion(
                                `/carrito/aumentar/${itemId}/`
                            );


                        if (!cantidad) {
                            return;
                        }


                        cantidad.textContent =
                            datos.cantidad;


                        actualizarSubtotalItem(
                            itemId,
                            datos.subtotal
                        );


                        actualizarContador(
                            datos.cantidad_carrito
                        );


                    } catch (error) {

                        if (
                            error.message !==
                            "__LOGIN_MOSTRADO__"
                        ) {

                            mostrarMensaje(
                                error.message
                            );
                        }

                    } finally {

                        this.disabled = false;
                    }
                }
            );
        });


    /*
    ==========================================================
    DISMINUIR CANTIDAD
    ==========================================================
    */

    document
        .querySelectorAll(".btn-disminuir")
        .forEach(function (boton) {

            boton.addEventListener(
                "click",
                async function () {

                    const itemId =
                        this.dataset.itemId;


                    this.disabled = true;


                    try {

                        const datos =
                            await enviarPeticion(
                                `/carrito/disminuir/${itemId}/`
                            );


                        if (datos.eliminado) {

                            eliminarElementoCarrito(
                                itemId
                            );

                        } else {

                            const cantidad =
                                document.getElementById(
                                    "cantidad-" + itemId
                                );


                            if (cantidad) {

                                cantidad.textContent =
                                    datos.cantidad;
                            }


                            actualizarSubtotalItem(
                                itemId,
                                datos.subtotal
                            );
                        }


                        actualizarContador(
                            datos.cantidad_carrito
                        );


                        recalcularResumenVisual();


                    } catch (error) {

                        if (
                            error.message !==
                            "__LOGIN_MOSTRADO__"
                        ) {

                            mostrarMensaje(
                                error.message
                            );
                        }

                    } finally {

                        this.disabled = false;
                    }
                }
            );
        });


    /*
    ==========================================================
    ELIMINAR PRODUCTO
    ==========================================================
    */

    document
        .querySelectorAll(".btn-eliminar-carrito")
        .forEach(function (boton) {

            boton.addEventListener(
                "click",
                async function () {

                    const itemId =
                        this.dataset.itemId;


                    this.disabled = true;


                    try {

                        const datos =
                            await enviarPeticion(
                                `/carrito/eliminar/${itemId}/`
                            );


                        eliminarElementoCarrito(
                            itemId
                        );


                        actualizarContador(
                            datos.cantidad_carrito
                        );


                        recalcularResumenVisual();


                    } catch (error) {

                        if (
                            error.message !==
                            "__LOGIN_MOSTRADO__"
                        ) {

                            mostrarMensaje(
                                error.message
                            );
                        }


                    } finally {

                        this.disabled = false;
                    }
                }
            );
        });


    /*
    ==========================================================
    ELIMINAR ELEMENTO VISUAL
    ==========================================================
    */

    function eliminarElementoCarrito(itemId) {

        const elemento =
            document.getElementById(
                "carrito-item-" + itemId
            );


        if (!elemento) {
            return;
        }


        elemento.classList.add(
            "item-eliminando"
        );


        setTimeout(function () {

            elemento.remove();


            const items =
                document.querySelectorAll(
                    ".carrito-item"
                );


            if (items.length === 0) {

                location.reload();
            }

        }, 250);
    }


    /*
    ==========================================================
    RECALCULAR RESUMEN
    ==========================================================
    */

    function recalcularResumenVisual() {

        setTimeout(function () {

            location.reload();

        }, 300);
    }


    /*
    ==========================================================
    MENSAJE
    ==========================================================
    */

    function mostrarMensaje(mensaje) {

        mostrarToast(
            mensaje,
            "error"
        );
    }


    /*
    ==========================================================
    CONTINUAR CON LA COMPRA
    ==========================================================
    */

    const botonContinuar =
        document.getElementById(
            "btn-continuar-compra"
        );


    if (botonContinuar) {

        botonContinuar.addEventListener(
            "click",
            function () {

                /*
                ------------------------------------------------
                URL_CHECKOUT viene desde el HTML:

                const URL_CHECKOUT = "{% url 'checkout' %}";
                ------------------------------------------------
                */

                if (
                    typeof URL_CHECKOUT !== "undefined" &&
                    URL_CHECKOUT
                ) {

                    window.location.href =
                        URL_CHECKOUT;

                } else {

                    mostrarMensaje(
                        "No se pudo acceder al checkout."
                    );
                }
            }
        );
    }


    /*
    ==========================================================
    CONTADOR INICIAL
    ==========================================================
    */

    const contadorInicial =
        document.getElementById(
            "contador-carrito"
        );


    if (contadorInicial) {

        const cantidadInicial =
            Number(
                contadorInicial.dataset.cantidadInicial || 0
            );


        actualizarContador(
            cantidadInicial
        );
    }

});