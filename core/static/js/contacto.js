const formulario = document.getElementById("contactForm");

const nombre = document.getElementById("nombre");
const correo = document.getElementById("correo");
const asunto = document.getElementById("asunto");
const mensaje = document.getElementById("mensaje");

formulario.addEventListener("submit", function(e){

    e.preventDefault();

    if(validarFormulario()){

        formulario.submit();

    }

});

function validarFormulario(){

    let valido = true;

    limpiarErrores();

    /* =========================
            NOMBRE
    ========================= */

    const nombreValor = nombre.value;
    const nombreTrim = nombreValor.trim();

    if(nombreTrim === ""){

        mostrarError(
            nombre,
            "El nombre es obligatorio"
        );

        valido = false;

    }else if(nombreValor !== nombreTrim){

        mostrarError(
            nombre,
            "No uses espacios al inicio o final"
        );

        valido = false;

    }else if(nombreTrim.length < 3){

        mostrarError(
            nombre,
            "Debe tener mínimo 3 caracteres"
        );

        valido = false;

    }else if(/\s{2,}/.test(nombreTrim)){

        mostrarError(
            nombre,
            "No uses múltiples espacios seguidos"
        );

        valido = false;

    }else{

        mostrarCorrecto(nombre);

    }

    /* =========================
            CORREO
    ========================= */

    const correoValor = correo.value;

    const regexEmail =
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if(correoValor === ""){

        mostrarError(
            correo,
            "El correo es obligatorio"
        );

        valido = false;

    }else if(correoValor.includes(" ")){

        mostrarError(
            correo,
            "El correo no puede contener espacios"
        );

        valido = false;

    }else if(correoValor !== correoValor.trim()){

        mostrarError(
            correo,
            "No uses espacios al inicio o final"
        );

        valido = false;

    }else if(!regexEmail.test(correoValor)){

        mostrarError(
            correo,
            "Ingresa un correo válido"
        );

        valido = false;

    }else{

        mostrarCorrecto(correo);

    }

    /* =========================
            ASUNTO
    ========================= */

    const asuntoValor = asunto.value;
    const asuntoTrim = asuntoValor.trim();

    if(asuntoTrim === ""){

        mostrarError(
            asunto,
            "El asunto es obligatorio"
        );

        valido = false;

    }else if(asuntoValor !== asuntoTrim){

        mostrarError(
            asunto,
            "No uses espacios al inicio o final"
        );

        valido = false;

    }else if(asuntoTrim.length < 5){

        mostrarError(
            asunto,
            "Debe tener mínimo 5 caracteres"
        );

        valido = false;

    }else if(/\s{2,}/.test(asuntoTrim)){

        mostrarError(
            asunto,
            "No uses múltiples espacios seguidos"
        );

        valido = false;

    }else{

        mostrarCorrecto(asunto);

    }

    /* =========================
            MENSAJE
    ========================= */

    const mensajeValor = mensaje.value;
    const mensajeTrim = mensajeValor.trim();

    if(mensajeTrim === ""){

        mostrarError(
            mensaje,
            "El mensaje es obligatorio"
        );

        valido = false;

    }else if(mensajeValor !== mensajeTrim){

        mostrarError(
            mensaje,
            "No uses espacios al inicio o final"
        );

        valido = false;

    }else if(mensajeTrim.length < 10){

        mostrarError(
            mensaje,
            "El mensaje debe tener mínimo 10 caracteres"
        );

        valido = false;

    }else if(/\s{2,}/.test(mensajeTrim)){

        mostrarError(
            mensaje,
            "No uses múltiples espacios seguidos"
        );

        valido = false;

    }else{

        mostrarCorrecto(mensaje);

    }

    return valido;

}

/* =========================
        MOSTRAR ERROR
========================= */

function mostrarError(input, mensaje){

    const formGroup = input.parentElement;

    const small = formGroup.querySelector(".error");

    small.textContent = mensaje;

    input.classList.add("input-error");

}

/* =========================
        INPUT CORRECTO
========================= */

function mostrarCorrecto(input){

    input.classList.add("input-success");

}

/* =========================
        LIMPIAR
========================= */

function limpiarErrores(){

    const errores = document.querySelectorAll(".error");

    errores.forEach(error => {

        error.textContent = "";

    });

    const inputs = document.querySelectorAll("input, textarea");

    inputs.forEach(input => {

        input.classList.remove(
            "input-error",
            "input-success"
        );

    });

}

function limpiarCorrectos(){

    const inputs = document.querySelectorAll("input, textarea");

    inputs.forEach(input => {

        input.classList.remove("input-success");

    });

}