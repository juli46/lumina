document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // ELIMINAR DIRECCIÓN (formulario POST + confirmación)
    // Si el JS fallara, el formulario igual se envía por POST.
    // =========================
    document.querySelectorAll(".delete-address-form").forEach(formEl => {

        formEl.addEventListener("submit", function (e) {

            e.preventDefault();

            Swal.fire({
                title: "¿Eliminar dirección?",
                text: "Esta acción no se puede deshacer.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Sí, eliminar",
                cancelButtonText: "Cancelar",
                confirmButtonColor: "#df6d77",
                cancelButtonColor: "#9ca3af"
            }).then(result => {

                if (result.isConfirmed) {
                    formEl.submit();
                }

            });

        });

    });

    // =========================
    // MODAL
    // =========================
    const modal = document.getElementById("addressModal");

    window.openModal = () => {
        modal?.classList.add("active");
    };

    window.closeModal = () => {
        modal?.classList.remove("active");
    };

    window.addEventListener("click", (e) => {

        if (e.target === modal) {
            modal.classList.remove("active");
        }

    });

    // =========================
    // DEPARTAMENTOS Y CIUDADES
    // =========================
    const data = {

        "Antioquia": [
            "Medellín","Bello","Itagüí","Envigado","Rionegro",
            "Apartadó","Turbo","La Ceja","Caldas","Sabaneta"
        ],

        "Cundinamarca": [
            "Bogotá","Soacha","Chía","Zipaquirá",
            "Facatativá","Madrid","Mosquera",
            "Fusagasugá","Girardot"
        ],

        "Valle del Cauca": [
            "Cali","Palmira","Buenaventura",
            "Tuluá","Buga","Cartago",
            "Jamundí","Yumbo"
        ],

        "Atlántico": [
            "Barranquilla","Soledad",
            "Malambo","Sabanalarga",
            "Puerto Colombia"
        ],

        "Bolívar": [
            "Cartagena","Magangué",
            "Turbaco","Arjona",
            "El Carmen de Bolívar"
        ],

        "Santander": [
            "Bucaramanga","Floridablanca",
            "Girón","Piedecuesta",
            "Barrancabermeja"
        ],

        "Norte de Santander": [
            "Cúcuta","Ocaña",
            "Pamplona","Villa del Rosario"
        ],

        "Tolima": [
            "Ibagué","Espinal",
            "Melgar","Honda"
        ],

        "Huila": [
            "Neiva","Pitalito","Garzón"
        ],

        "Caldas": [
            "Manizales","La Dorada","Chinchiná"
        ],

        "Risaralda": [
            "Pereira","Dosquebradas",
            "Santa Rosa de Cabal"
        ],

        "Quindío": [
            "Armenia","Calarcá","Montenegro"
        ],

        "Meta": [
            "Villavicencio","Acacías","Granada"
        ],

        "Córdoba": [
            "Montería","Lorica","Sahagún"
        ],

        "Sucre": [
            "Sincelejo","Corozal","Sampués"
        ],

        "Nariño": [
            "Pasto","Ipiales","Tumaco"
        ],

        "Boyacá": [
            "Tunja","Duitama",
            "Sogamoso","Chiquinquirá"
        ],

        "Cesar": [
            "Valledupar","Aguachica","Codazzi"
        ],

        "La Guajira": [
            "Riohacha","Maicao","Fonseca"
        ],

        "Chocó": [
            "Quibdó","Istmina","Tadó"
        ],

        "Amazonas": [
            "Leticia"
        ],

        "San Andrés y Providencia": [
            "San Andrés"
        ]
    };

    const form = document.getElementById("direccionForm");
    const depto = document.getElementById("departamento");
    const ciudad = document.getElementById("ciudad");

    // =========================
    // CARGAR DEPARTAMENTOS
    // =========================
    if (depto) {

        Object.keys(data).forEach(dep => {

            const option =
                document.createElement("option");

            option.value = dep;
            option.textContent = dep;

            depto.appendChild(option);

        });

    }

    // =========================
    // CAMBIO DE CIUDADES
    // =========================
    depto?.addEventListener("change", () => {

        ciudad.innerHTML =
            '<option value="">Selecciona una ciudad</option>';

        if (!data[depto.value]) return;

        data[depto.value].forEach(c => {

            const option =
                document.createElement("option");

            option.value = c;
            option.textContent = c;

            ciudad.appendChild(option);

        });

    });

    // =========================
    // FUNCIONES DE ERROR
    // =========================
    function error(input, msg) {

        const small =
            input.parentElement.querySelector(".error");

        if (small) {
            small.textContent = msg;
        }

        input.classList.add("input-error");
    }

    function ok(input) {

        const small =
            input.parentElement.querySelector(".error");

        if (small) {
            small.textContent = "";
        }

        input.classList.remove("input-error");
    }

    // =========================
    // SOLO LETRAS NOMBRE
    // =========================
    const nombreInput =
        form?.querySelector("[name='nombre_receptor']");

    nombreInput?.addEventListener("input", () => {

        nombreInput.value =
            nombreInput.value.replace(
                /[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g,
                ""
            );

    });

    // =========================
    // SOLO NÚMEROS TELÉFONO
    // =========================
    const telefonoInput =
        form?.querySelector("[name='telefono']");

    telefonoInput?.addEventListener("input", () => {

        telefonoInput.value =
            telefonoInput.value.replace(/\D/g, "");

    });

    // =========================
    // VALIDAR FORMULARIO
    // =========================
    form?.addEventListener("submit", (e) => {

        let errores = 0;

        const nombre =
            form.querySelector("[name='nombre_receptor']");

        const telefono =
            form.querySelector("[name='telefono']");

        const direccion =
            form.querySelector("[name='direccion']");

        // NOMBRE
        if (!nombre.value.trim()) {

            error(nombre, "El nombre es obligatorio");
            errores++;

        } else if (nombre.value.trim().length < 3) {

            error(nombre, "Mínimo 3 caracteres");
            errores++;

        } else {

            ok(nombre);

        }

        // TELÉFONO
        if (!telefono.value.trim()) {

            error(telefono, "El teléfono es obligatorio");
            errores++;

        } else if (!/^[0-9]{10}$/.test(telefono.value)) {

            error(
                telefono,
                "Debe contener 10 números"
            );

            errores++;

        } else {

            ok(telefono);

        }

        // DIRECCIÓN
        if (!direccion.value.trim()) {

            error(
                direccion,
                "La dirección es obligatoria"
            );

            errores++;

        } else if (direccion.value.trim().length < 8) {

            error(
                direccion,
                "Dirección demasiado corta"
            );

            errores++;

        } else if (!/\d/.test(direccion.value)) {

            error(
                direccion,
                "Debe contener al menos un número"
            );

            errores++;

        } else {

            ok(direccion);

        }

        // DEPARTAMENTO
        if (!depto.value) {

            depto.classList.add("input-error");
            errores++;

        } else {

            depto.classList.remove("input-error");

        }

        // CIUDAD
        if (!ciudad.value) {

            ciudad.classList.add("input-error");
            errores++;

        } else {

            ciudad.classList.remove("input-error");

        }

        // BLOQUEAR ENVÍO
        if (errores > 0) {

            e.preventDefault();

            Swal.fire({
                icon: "error",
                title: "Formulario incompleto",
                text: "Corrige los campos marcados antes de continuar.",
                confirmButtonColor: "#df6d77"
            });

        }

    });

});

function abrirRutina(titulo, descripcion){

    document.getElementById("tituloRutina").textContent = titulo;

    document.getElementById("contenidoRutina").innerHTML =
        descripcion.replace(/\n/g,"<br>");

    document.getElementById("modalRutina").classList.add("active");

}

function cerrarRutina(){

    document.getElementById("modalRutina").classList.remove("active");

}

document.querySelectorAll(".eliminar-resultado").forEach(boton => {

    boton.addEventListener("click", function(e){

        e.preventDefault();

        const url = this.href;

        Swal.fire({

            title: "¿Eliminar resultado?",
            text: "Esta acción no se puede deshacer.",

            icon: "warning",

            showCancelButton: true,

            confirmButtonColor: "#df6d77",
            cancelButtonColor: "#999",

            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar"

        }).then((result)=>{

            if(result.isConfirmed){

                window.location.href = url;

            }

        });

    });

});