function abrirFormulario() {

    const modal = document.getElementById(
        "recomendacionModal"
    );

    if (!modal) return;

    modal.classList.add("active");

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.style.overflow = "hidden";

}


function cerrarFormulario() {

    const modal = document.getElementById(
        "recomendacionModal"
    );

    if (!modal) return;

    modal.classList.remove("active");

    modal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.style.overflow = "";

}


function confirmarEliminacion(event) {

    const confirmar = confirm(
        "¿Seguro que quieres eliminar esta recomendación?\n\nEsta acción no se puede deshacer."
    );

    if (!confirmar) {

        event.preventDefault();

        return false;

    }

    return true;

}


/* Cerrar haciendo clic fuera del modal */

document.addEventListener(
    "click",
    function(event) {

        const modal = document.getElementById(
            "recomendacionModal"
        );

        if (!modal) return;

        if (
            event.target === modal &&
            modal.classList.contains("active")
        ) {

            cerrarFormulario();

        }

    }
);


/* Cerrar con ESC */

document.addEventListener(
    "keydown",
    function(event) {

        if (event.key !== "Escape") return;

        const modal = document.getElementById(
            "recomendacionModal"
        );

        if (
            modal &&
            modal.classList.contains("active")
        ) {

            cerrarFormulario();

        }

    }
);


/* Validar rango de presupuesto */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        const min = document.getElementById(
            "presupuesto_min"
        );

        const max = document.getElementById(
            "presupuesto_max"
        );

        if (!min || !max) return;

        function validarRango() {

            if (
                min.value &&
                max.value &&
                Number(max.value) < Number(min.value)
            ) {

                max.setCustomValidity(
                    "El presupuesto máximo debe ser mayor o igual al mínimo."
                );

            } else {

                max.setCustomValidity("");

            }

        }

        min.addEventListener(
            "input",
            validarRango
        );

        max.addEventListener(
            "input",
            validarRango
        );

    }
);