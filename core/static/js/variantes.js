// // ======================================
// CATEGORÍAS
// ======================================


function editarCategoria(id, nombre) {

    document.getElementById("tituloCategoria").innerHTML =
    "Editar Categoría";

    document.getElementById("categoria_id").value = id;

    document.getElementById("categoria_nombre").value = nombre;

    document.getElementById("btnCategoria").innerHTML =
    "Actualizar categoría";

    document.getElementById("cancelarCategoria").style.display =
    "inline-block";

}



function cancelarEdicionCategoria() {

    document.getElementById("tituloCategoria").innerHTML =
    "Nueva Categoría";

    document.getElementById("categoria_id").value = "";

    document.getElementById("categoria_nombre").value = "";

    document.getElementById("btnCategoria").innerHTML =
    "Guardar categoría";

    document.getElementById("cancelarCategoria").style.display =
    "none";
}

// ======================================
// MARCAS
// ======================================


function editarMarca(id, nombre) {

    document.getElementById("tituloMarca").innerHTML =
    "Editar Marca";

    document.getElementById("marca_id").value = id;

    document.getElementById("marca_nombre").value = nombre;

    document.getElementById("btnMarca").innerHTML =
    "Actualizar marca";

    document.getElementById("cancelarMarca").style.display =
    "inline-block";

}

function cancelarEdicionMarca() {

    document.getElementById("tituloMarca").innerHTML =
    "Nueva Marca";

    document.getElementById("marca_id").value = "";

    document.getElementById("marca_nombre").value = "";

    document.getElementById("btnMarca").innerHTML =
    "Guardar marca";

    document.getElementById("cancelarMarca").style.display =
    "none";
}

// ======================================
// COLECCIONES
// ======================================


function editarColeccion(id,nombre,marca){


    document.getElementById("tituloColeccion").innerHTML =
    "Editar Colección";


    document.getElementById("coleccion_id").value = id;


    document.getElementById("coleccion_nombre").value = nombre;


    document.getElementById("coleccion_marca").value = marca;


    document.getElementById("btnColeccion").innerHTML =
    "Actualizar colección";


    document.getElementById("cancelarColeccion").style.display =
    "inline-block";

}
function cancelarEdicionColeccion() {

    document.getElementById("tituloColeccion").innerHTML =
    "Nueva Colección";

    document.getElementById("coleccion_id").value = "";

    document.getElementById("coleccion_nombre").value = "";

    document.getElementById("coleccion_marca").selectedIndex = 0;

    document.getElementById("btnColeccion").innerHTML =
    "Guardar colección";

    document.getElementById("cancelarColeccion").style.display =
    "none";
}
// ======================================
// CAMBIO DE PESTAÑAS
// ======================================


function mostrarCatalogo(panel, boton){


    document
    .querySelectorAll(".catalogo-panel")
    .forEach(function(seccion){

        seccion.classList.remove("activo");

    });



    document
    .querySelectorAll(".tab-btn")
    .forEach(function(btn){

        btn.classList.remove("active");

    });



    document
    .getElementById(panel)
    .classList.add("activo");



    boton.classList.add("active");



    // mantiene búsqueda

    buscarCatalogo();


}





// ======================================
// BUSCADOR GLOBAL DEL CATÁLOGO
// ======================================


function buscarCatalogo(){


    const buscador =
    document.getElementById("buscadorCatalogo");


    if(!buscador) return;



    let texto =
    buscador.value.toLowerCase().trim();



    let panelActivo =
    document.querySelector(".catalogo-panel.activo");



    if(!panelActivo) return;



    let filas =
    panelActivo.querySelectorAll(
        ".tablaCatalogo tbody tr:not(.sin-resultados)"
    );



    let encontrados = 0;



    filas.forEach(function(fila){


        let contenido =
        fila.textContent.toLowerCase();



        if(contenido.includes(texto)){


            fila.style.display = "";

            encontrados++;


        }else{


            fila.style.display = "none";


        }


    });





    // eliminar mensaje anterior

    let mensaje =
    panelActivo.querySelector(".sin-resultados");


    if(mensaje){

        mensaje.remove();

    }





    // mostrar mensaje

    if(encontrados === 0){


        let tbody =
        panelActivo.querySelector(".tablaCatalogo tbody");



        if(tbody){


            let columnas =
            panelActivo.querySelectorAll(
                ".tablaCatalogo thead th"
            ).length;



            let filaMensaje =
            document.createElement("tr");


            filaMensaje.className =
            "sin-resultados";



            filaMensaje.innerHTML = `

            <td colspan="${columnas}"
            style="
            text-align:center;
            padding:25px;
            color:#999;
            font-size:16px;
            ">

            🔍 No se encontraron coincidencias

            </td>

            `;



            tbody.appendChild(filaMensaje);


        }


    }


}







// ======================================
// CARGA DE PÁGINA
// ======================================


document.addEventListener(
"DOMContentLoaded",
function(){



    // BUSCADOR

    const buscador =
    document.getElementById("buscadorCatalogo");



    if(buscador){


        buscador.addEventListener(
        "keyup",
        buscarCatalogo
        );


    }





    // ======================================
    // CONFIRMAR ELIMINACIÓN
    // ======================================


    document
    .querySelectorAll(".eliminar")
    .forEach(function(boton){



        boton.addEventListener(
        "click",
        function(e){



            e.preventDefault();



            let formulario =
            this.closest("form");





            Swal.fire({


                title:"¿Eliminar registro?",


                text:"Esta acción no se puede deshacer.",


                icon:"warning",


                showCancelButton:true,


                confirmButtonText:"Sí, eliminar",


                cancelButtonText:"Cancelar",


                confirmButtonColor:"#df6d86",


                cancelButtonColor:"#999"



            })

            .then((resultado)=>{



                if(resultado.isConfirmed){


                    formulario.submit();


                }



            });



        });



    });

});
// ======================================
// VALIDACIONES
// ======================================

document.addEventListener("DOMContentLoaded", function () {

    const formularios = document.querySelectorAll(".form-card");

    formularios.forEach(formulario => {

        const campos = formulario.querySelectorAll("input[type='text'], select");

        campos.forEach(campo => {

            campo.addEventListener("input", () => validarCampo(campo));
            campo.addEventListener("change", () => validarCampo(campo));

        });

        formulario.addEventListener("submit", function (e) {

            let formularioValido = true;

            campos.forEach(campo => {

                if (!validarCampo(campo)) {
                    formularioValido = false;
                }

            });

            if (!formularioValido) {

                e.preventDefault();

                Swal.fire({
                    icon: "warning",
                    title: "Formulario incompleto",
                    text: "Corrige los campos marcados antes de continuar.",
                    confirmButtonText: "Aceptar"
                });

            }

        });

    });

});

// ======================================
// ETIQUETAS
// ======================================

function editarEtiqueta(id,nombre){

    document.getElementById(
    "tituloEtiqueta"
    ).innerHTML =
    "Editar Etiqueta";

    document.getElementById(
    "etiqueta_id"
    ).value = id;

    document.getElementById(
    "etiqueta_nombre"
    ).value = nombre;

    document.getElementById(
    "btnEtiqueta"
    ).innerHTML =
    "Actualizar etiqueta";

    document.getElementById(
    "cancelarEtiqueta"
    ).style.display =
    "inline-block";

}

function cancelarEdicionEtiqueta(){

    document.getElementById(
    "tituloEtiqueta"
    ).innerHTML =
    "Nueva Etiqueta";

    document.getElementById(
    "etiqueta_id"
    ).value = "";

    document.getElementById(
    "etiqueta_nombre"
    ).value = "";

    document.getElementById(
    "btnEtiqueta"
    ).innerHTML =
    "Guardar etiqueta";

    document.getElementById(
    "cancelarEtiqueta"
    ).style.display =
    "none";

}

function validarCampo(campo) {

    const error = campo.parentElement.querySelector(".error-text");

    let mensaje = "";

    campo.classList.remove("input-error");

    if (error) {
        error.textContent = "";
    }

    // SELECT

    if (campo.tagName === "SELECT") {

        if (campo.value === "") {

            mensaje = "Debes seleccionar una opción.";

        }

    }

    // INPUT

    else {

        const valor = campo.value.trim();

        if (valor === "") {

            mensaje = "Este campo es obligatorio.";

        }

        else if (valor.length < 3) {

            mensaje = "Debe tener mínimo 3 caracteres.";

        }

        else if (valor.length > 60) {

            mensaje = "Máximo 60 caracteres.";

        }

        else if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$/.test(valor)) {

            mensaje = "Solo se permiten letras, números y espacios.";

        }

    }

    if (mensaje !== "") {

        campo.classList.add("input-error");

        if (error) {
            error.textContent = mensaje;
        }

        return false;

    }

    return true;

}


