let index = 0;
// ======================================================
// AGREGAR NUEVAS SECCIONES AL BLOG
// ======================================================
function agregarSeccion() {

    const container = document.getElementById("secciones-container");

    const bloque = `
        <div class="bloque-seccion">

            <input type="text"
                   name="seccion-${index}-subtitulo"
                   placeholder="Subtítulo (opcional)">

            <textarea name="seccion-${index}-contenido"
                      placeholder="Escribe el contenido"></textarea>

            <input type="file"
                   name="seccion-${index}-imagen">

        </div>
    `;

    container.insertAdjacentHTML("beforeend", bloque);
    index++;
}


document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("blogForm");
    const select = document.querySelector("select[name='publicado']");
    const titulo = document.querySelector("input[name='titulo']");
    const resumen = document.querySelector("textarea[name='resumen']");

    if (!form) return;

    // --------------------------------------------------
    // VALIDACIÓN Y ENVÍO DEL FORMULARIO
    // --------------------------------------------------

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const tituloVal = titulo.value.trim();
        const resumenVal = resumen.value.trim();
        const estado = select.value;


        if (!tituloVal) {
            Swal.fire("Oops", "El título no puede estar vacío ✏️", "warning");
            return;
        }

        if (tituloVal.length < 3) {
            Swal.fire("Oops", "El título es muy corto 🌱", "warning");
            return;
        }

        if (!resumenVal) {
            Swal.fire("Oops", "El resumen es obligatorio 📝", "warning");
            return;
        }

        if (resumenVal.length < 10) {
            Swal.fire("Oops", "El resumen es demasiado corto 🌸", "warning");
            return;
        }

        let texto = estado === "True"
            ? "¿Quieres publicar este blog ahora? 🌍"
            : "¿Guardar como borrador? 🟡";

        Swal.fire({
            title: "Confirmar acción",
            text: texto,
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Sí",
            cancelButtonText: "Cancelar"
        }).then((result) => {
            if (result.isConfirmed) {
                form.submit();
            }
        });

    });

    // --------------------------------------------------
    // ELIMINAR BLOG
    // --------------------------------------------------
    window.confirmarEliminar = function (event, element) {
        event.preventDefault();

        Swal.fire({
            title: "¿Eliminar este blog?",
            text: "Esta acción no se puede deshacer 💀",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar"
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = element.href;
            }
        });
    };

    // --------------------------------------------------
    // PUBLICAR BLOG
    // --------------------------------------------------
    window.confirmarPublicar = function (event, element) {
        event.preventDefault();

        Swal.fire({
            title: "¿Publicar este blog?",
            text: "Será visible para todos 🌍",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Sí, publicar",
            cancelButtonText: "Cancelar"
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = element.href;
            }
        });
    };

    // --------------------------------------------------
    // CAMBIO DE ESTADO (PUBLICADO / BORRADOR)
    // --------------------------------------------------

    if (select) {
        let anterior = select.value;

        select.addEventListener("change", function () {

            if (this.value === "True") {
                Swal.fire({
                    title: "¿Publicar este blog?",
                    icon: "question",
                    showCancelButton: true
                }).then((r) => {
                    if (!r.isConfirmed) this.value = anterior;
                    else anterior = "True";
                });
            } else {
                Swal.fire({
                    title: "¿Mover a borrador?",
                    icon: "warning",
                    showCancelButton: true
                }).then((r) => {
                    if (!r.isConfirmed) this.value = anterior;
                    else anterior = "False";
                });
            }

        });
    }

});