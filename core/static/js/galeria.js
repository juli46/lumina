document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("galeriaForm");

    if (!form) return;

    const titulo = document.querySelector("input[name='titulo']");
    const categoria = document.querySelector("input[name='categoria']");
    const descripcion = document.querySelector("textarea[name='descripcion']");
    const tags = document.querySelector("input[name='tags']");
    const imagen = document.querySelector("input[name='imagen']");

    // =========================
    // GUARDAR / ACTUALIZAR
    // =========================

    form.addEventListener("submit", function (event) {

        event.preventDefault();

        const tituloVal = titulo.value.trim();
        const categoriaVal = categoria.value.trim();
        const descripcionVal = descripcion.value.trim();
        const tagsVal = tags.value.trim();

        // TÍTULO

        if (!tituloVal) {

            Swal.fire(
                "Oops",
                "El título es obligatorio ✏️",
                "warning"
            );

            return;
        }

        if (tituloVal.length < 3) {

            Swal.fire(
                "Oops",
                "El título debe tener al menos 3 caracteres 🌱",
                "warning"
            );

            return;
        }

        if (tituloVal.length > 150) {

            Swal.fire(
                "Oops",
                "El título es demasiado largo 📏",
                "warning"
            );

            return;
        }

        // CATEGORÍA

        if (!categoriaVal) {

            Swal.fire(
                "Oops",
                "La categoría es obligatoria 🏷️",
                "warning"
            );

            return;
        }

        if (categoriaVal.length < 3) {

            Swal.fire(
                "Oops",
                "La categoría es demasiado corta 🌸",
                "warning"
            );

            return;
        }

        // DESCRIPCIÓN

        if (!descripcionVal) {

            Swal.fire(
                "Oops",
                "La descripción es obligatoria 📝",
                "warning"
            );

            return;
        }

        if (descripcionVal.length < 10) {

            Swal.fire(
                "Oops",
                "La descripción debe tener al menos 10 caracteres ✨",
                "warning"
            );

            return;
        }

        // TAGS

        if (tagsVal.length > 255) {

            Swal.fire(
                "Oops",
                "Los tags son demasiado largos 🏷️",
                "warning"
            );

            return;
        }

        // =========================
        // VALIDAR IMAGEN (FINAL FIX)
        // =========================

        const modoEdicion =
            document.getElementById("modoEdicion") !== null;

        const tieneImagen =
            imagen && imagen.files && imagen.files.length > 0;

        if (!modoEdicion && !tieneImagen) {

            Swal.fire(
                "Oops",
                "Debes seleccionar una imagen 📸",
                "warning"
            );

            return;
        }

        if (imagen && imagen.files.length > 0) {

            const archivo = imagen.files[0];

            const formatosPermitidos = [
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp"
            ];

            if (!formatosPermitidos.includes(archivo.type)) {

                Swal.fire(
                    "Formato inválido",
                    "Solo se permiten imágenes JPG, JPEG, PNG o WEBP 🖼️",
                    "error"
                );

                return;
            }

            if (archivo.size > 10 * 1024 * 1024) {

                Swal.fire(
                    "Imagen demasiado grande",
                    "La imagen no puede superar los 10 MB 📦",
                    "error"
                );

                return;
            }

        }

        // IMAGEN OBLIGATORIA AL CREAR

        // =========================
        // IMAGEN (CREAR vs EDITAR)
        // =========================

        const modoEdicion =
            document.getElementById("modoEdicion") !== null;

        const tieneImagen =
            imagen && imagen.files && imagen.files.length > 0;

        // SOLO exigir imagen si estás creando
        if (!modoEdicion && !tieneImagen) {

            Swal.fire(
                "Oops",
                "Debes seleccionar una imagen 📸",
                "warning"
            );

            return;
        }

        // =========================
        // ELIMINAR
        // =========================

        document
            .querySelectorAll(".eliminar-galeria")
            .forEach(btn => {

                btn.addEventListener("click", function (e) {

                    e.preventDefault();

                    const url = this.href;

                    Swal.fire({

                        title: "¿Eliminar imagen?",

                        text: "Esta acción no se puede deshacer 🗑️",

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

    })
})
