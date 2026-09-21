// ======================================
// CONTACTO DASHBOARD
// ======================================

document.addEventListener("DOMContentLoaded", () => {

    iniciarMensajes();

    iniciarCerrarDetalle();

    iniciarBuscador();

    iniciarFormulario();

    iniciarBotonesArchivo();

    iniciarEliminar();

    iniciarValidaciones();

});



// ======================================
// CSRF HELPER
// ======================================

function obtenerCSRFToken() {

    const match =
        document.cookie.match(/csrftoken=([^;]+)/);

    return match ? match[1] : "";

}



// ======================================
// ABRIR MENSAJES
// ======================================

function iniciarMensajes() {

    const botones = document.querySelectorAll(".btn-ver");


    botones.forEach(boton => {


        boton.addEventListener("click", function () {

            const id = this.dataset.id;

            fetch(`/contacto/marcar-leido/${id}/`)
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error(error));

            cargarMensaje(this);

            activarFila(this);

        });


    });


}



// ======================================
// CARGAR MENSAJE
// ======================================

function cargarMensaje(boton) {


    document
        .querySelectorAll(".btn-ver")
        .forEach(btn => btn.classList.remove("activo"));


    boton.classList.add("activo");



    const detalle =
        document.getElementById("detalleContacto");


    if (!detalle) return;



    detalle.classList.remove("oculto");

    detalle.classList.add("mostrar");



    document.getElementById("detalleNombre").value =
        boton.dataset.nombre;



    document.getElementById("detalleCorreo").value =
        boton.dataset.correo;



    document.getElementById("detalleAsunto").value =
        boton.dataset.asunto;



    document.getElementById("detalleFecha").value =
        boton.dataset.fecha;



    document.getElementById("contactoId").value =
        boton.dataset.id;



    document.getElementById("contactoIdFormulario").value =
        boton.dataset.id;



    // ==================================
    // HISTORIAL
    // ==================================

    const historial =
        document.getElementById("historialMensajes");



    historial.innerHTML = "";



    historial.innerHTML += `

    <div class="burbuja cliente">


        <div class="burbuja-header">

            <i class="fa-solid fa-user"></i>

            Cliente

        </div>


        <textarea readonly rows="5">${boton.dataset.mensaje}</textarea>


        <div class="fecha-chat">

            ${boton.dataset.fecha}

        </div>


    </div>

    `;



    if (boton.dataset.respuesta) {


        historial.innerHTML += `

        <div class="burbuja lumina">


            <div class="burbuja-header">

                <i class="fa-solid fa-spa"></i>

                Lúmina

            </div>


            <textarea readonly rows="5">${boton.dataset.respuesta}</textarea>


        </div>

        `;

    }



    if (boton.dataset.respuestaCliente) {


        historial.innerHTML += `

        <div class="burbuja cliente">


            <div class="burbuja-header">

                <i class="fa-solid fa-user-check"></i>

                Cliente

            </div>


            <textarea readonly rows="5">${boton.dataset.respuestaCliente}</textarea>


            <div class="fecha-chat">

                ${boton.dataset.fechaCliente || ""}

            </div>


        </div>

        `;


    }



    // ==================================
    // BOTONES ARCHIVO
    // ==================================

    const archivado =
        boton.dataset.archivado === "True" ||
        boton.dataset.archivado === "true";



    const btnArchivar =
        document.getElementById("btnArchivar");


    const btnRestaurar =
        document.getElementById("btnRestaurar");



    if (btnArchivar && btnRestaurar) {


        if (archivado) {


            btnArchivar.style.display = "none";

            btnRestaurar.style.display = "inline-flex";


        } else {


            btnArchivar.style.display = "inline-flex";

            btnRestaurar.style.display = "none";


        }


    }



    document.getElementById("respuesta").value = "";



    document.getElementById("formRespuesta").action =

        "/dashboard/contacto/" +

        boton.dataset.id +

        "/responder/";



    detalle.scrollIntoView({

        behavior: "smooth",

        block: "start"

    });


}
// ======================================
// CERRAR DETALLE
// ======================================

function iniciarCerrarDetalle() {


    const boton =
        document.getElementById("cerrarDetalle");


    const detalle =
        document.getElementById("detalleContacto");



    if (!boton || !detalle) return;



    boton.addEventListener("click", () => {


        detalle.classList.remove("mostrar");

        detalle.classList.add("oculto");



        document
            .querySelectorAll(".btn-ver.activo")
            .forEach(btn => {

                btn.classList.remove("activo");

            });



        document
            .querySelectorAll(".fila-activa")
            .forEach(fila => {

                fila.classList.remove("fila-activa");

            });


    });


}





// ======================================
// BUSCADOR
// ======================================

function iniciarBuscador() {


    const buscador =
        document.getElementById("buscarMensaje");



    if (!buscador) return;



    const filas =
        document.querySelectorAll("#tablaMensajes tr");



    const sinResultados =
        document.getElementById("sinResultados");



    buscador.addEventListener("input", function () {


        const texto =
            this.value.toLowerCase().trim();



        let encontrados = 0;



        filas.forEach(fila => {


            if (
                !fila.querySelector("td") ||
                fila.id === "sinResultados"
            ) {

                return;

            }



            const contenido =
                fila.textContent.toLowerCase();



            if (contenido.includes(texto)) {


                fila.style.display = "";

                encontrados++;


            } else {


                fila.style.display = "none";


            }



        });



        if (texto !== "" && encontrados === 0) {


            sinResultados.style.display = "";


        } else {


            sinResultados.style.display = "none";


        }



    });



    buscador.addEventListener("keydown", function (e) {


        if (e.key === "Escape") {


            this.value = "";


            this.dispatchEvent(
                new Event("input")
            );


        }


    });



}





// ======================================
// FORMULARIO RESPUESTA
// ======================================

function iniciarFormulario() {


    const formulario =
        document.getElementById("formRespuesta");



    if (!formulario) return;



    const respuesta =
        document.getElementById("respuesta");



    const botonEnviar =
        formulario.querySelector(".btn-principal");



    formulario.addEventListener("submit", function (e) {


        const texto =
            respuesta.value.trim();



        if (texto.length < 10) {


            e.preventDefault();



            Swal.fire({

                title: "Respuesta incompleta",

                text: "La respuesta debe tener mínimo 10 caracteres.",

                icon: "warning",

                confirmButtonText: "Aceptar"

            });



            respuesta.focus();


            return;


        }



        e.preventDefault();



        Swal.fire({


            title: "¿Enviar respuesta?",


            text: "El mensaje será enviado al cliente.",


            icon: "question",


            showCancelButton: true,


            confirmButtonText: "Enviar",


            cancelButtonText: "Cancelar",


            confirmButtonColor: "#8b5cf6",


            cancelButtonColor: "#6b7280"



        }).then((resultado) => {


            if (resultado.isConfirmed) {



                botonEnviar.disabled = true;



                botonEnviar.innerHTML = `

                <i class="fa-solid fa-spinner fa-spin"></i>

                Enviando...

                `;



                formulario.submit();



            }



        });



    });



    formulario.addEventListener("reset", () => {


        setTimeout(() => {


            respuesta.focus();



        }, 50);



    });



}
// ======================================
// ARCHIVAR / RESTAURAR
// ======================================

function iniciarBotonesArchivo() {


    const btnArchivar =
        document.getElementById("btnArchivar");


    const btnRestaurar =
        document.getElementById("btnRestaurar");



    if (btnArchivar) {


        btnArchivar.addEventListener("click", () => {


            const id =
                document.getElementById("contactoId").value;



            if (!id) {


                Swal.fire({

                    title: "Error",

                    text: "No se encontró el mensaje.",

                    icon: "error",

                    confirmButtonText: "Aceptar"

                });


                return;


            }



            Swal.fire({


                title: "¿Archivar conversación?",


                text: "El mensaje será movido a archivados.",


                icon: "warning",


                showCancelButton: true,


                confirmButtonText: "Archivar",


                cancelButtonText: "Cancelar",


                confirmButtonColor: "#f59e0b",


                cancelButtonColor: "#6b7280"



            }).then((resultado) => {


                if (resultado.isConfirmed) {


                    fetch(`/dashboard/contacto/${id}/archivar/`, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": obtenerCSRFToken()
                        }
                    })
                    .then(response => {

                        if (response.redirected) {
                            window.location.href = response.url;
                        } else if (response.ok) {
                            window.location.reload();
                        } else {
                            throw new Error("Error al archivar");
                        }

                    })
                    .catch(() => {

                        Swal.fire({
                            title: "Error",
                            text: "No se pudo archivar el mensaje.",
                            icon: "error",
                            confirmButtonText: "Aceptar"
                        });

                    });


                }


            });



        });



    }




    if (btnRestaurar) {


        btnRestaurar.addEventListener("click", () => {


            const id =
                document.getElementById("contactoId").value;



            Swal.fire({


                title: "¿Restaurar conversación?",


                text: "Volverá a la bandeja principal.",


                icon: "info",


                showCancelButton: true,


                confirmButtonText: "Restaurar",


                cancelButtonText: "Cancelar",


                confirmButtonColor: "#10b981",


                cancelButtonColor: "#6b7280"



            }).then((resultado) => {


                if (resultado.isConfirmed) {


                    fetch(`/dashboard/contacto/${id}/restaurar/`, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": obtenerCSRFToken()
                        }
                    })
                    .then(response => {

                        if (response.redirected) {
                            window.location.href = response.url;
                        } else if (response.ok) {
                            window.location.reload();
                        } else {
                            throw new Error("Error al restaurar");
                        }

                    })
                    .catch(() => {

                        Swal.fire({
                            title: "Error",
                            text: "No se pudo restaurar el mensaje.",
                            icon: "error",
                            confirmButtonText: "Aceptar"
                        });

                    });


                }


            });



        });



    }


}





// ======================================
// ELIMINAR CONVERSACIÓN
// ======================================

function iniciarEliminar() {


    const btnEliminar =
        document.getElementById("btnEliminar");



    if (!btnEliminar) return;



    btnEliminar.addEventListener("click", () => {


        const id =
            document.getElementById("contactoId").value;



        Swal.fire({


            title: "¿Eliminar conversación?",


            text: "Esta acción eliminará el chat permanentemente.",


            icon: "warning",


            showCancelButton: true,


            confirmButtonText: "Sí, eliminar",


            cancelButtonText: "Cancelar",


            confirmButtonColor: "#dc2626",


            cancelButtonColor: "#6b7280"



        }).then((resultado) => {


            if (resultado.isConfirmed) {


                fetch(`/dashboard/eliminar-mensaje/${id}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": obtenerCSRFToken()
                    }
                })
                .then(response => {

                    if (response.redirected) {
                        window.location.href = response.url;
                    } else if (response.ok) {
                        window.location.reload();
                    } else {
                        throw new Error("Error al eliminar");
                    }

                })
                .catch(() => {

                    Swal.fire({
                        title: "Error",
                        text: "No se pudo eliminar el mensaje.",
                        icon: "error",
                        confirmButtonText: "Aceptar"
                    });

                });


            }


        });



    });



}





// ======================================
// VALIDACIONES DE CAMPOS
// ======================================

function iniciarValidaciones() {


    const respuesta =
        document.getElementById("respuesta");


    if (!respuesta) return;



    const error =
        document.createElement("small");



    error.className = "error-campo";



    respuesta.parentNode.insertBefore(

        error,

        respuesta.nextSibling

    );



    respuesta.addEventListener("input", () => {


        const cantidad =
            respuesta.value.trim().length;



        if (cantidad === 0) {


            error.innerHTML = "";


            respuesta.classList.remove("campo-valido");


        }

        else if (cantidad < 10) {


            error.innerHTML =
                "La respuesta debe tener mínimo 10 caracteres.";


            error.classList.remove("valido");


            error.classList.add("error");


            respuesta.classList.remove("campo-valido");



        }

        else {


            error.innerHTML =
                "Respuesta válida ✓";


            error.classList.remove("error");


            error.classList.add("valido");


            respuesta.classList.add("campo-valido");


        }



    });



}





// ======================================
// ALERTAS DJANGO CON SWEETALERT
// ======================================

function iniciarAlertasDjango() {


    const alertas =
        document.querySelectorAll(".alerta");



    alertas.forEach(alerta => {


        Swal.fire({


            title: "Lúmina",


            text: alerta.innerText,


            icon:

                alerta.classList.contains("success")

                    ? "success"

                    : "info",


            confirmButtonText: "Aceptar"



        });



        alerta.remove();



    });



}


document.addEventListener(

    "DOMContentLoaded",

    iniciarAlertasDjango

);





// ======================================
// ACTIVAR FILA
// ======================================

function activarFila(boton) {


    document
        .querySelectorAll(".fila-activa")
        .forEach(fila => {


            fila.classList.remove("fila-activa");


        });



    const fila =
        boton.closest("tr");



    if (fila) {


        fila.classList.add("fila-activa");


    }


}





// ======================================
// ATAJOS TECLADO
// ======================================

document.addEventListener("keydown", (e) => {


    if (e.ctrlKey && e.key.toLowerCase() === "f") {


        e.preventDefault();



        const buscador =
            document.getElementById("buscarMensaje");



        if (buscador) {


            buscador.focus();

            buscador.select();


        }


    }



    if (e.key === "Escape") {


        const detalle =
            document.getElementById("detalleContacto");



        if (detalle && detalle.classList.contains("mostrar")) {


            detalle.classList.remove("mostrar");

            detalle.classList.add("oculto");


        }


    }



});