document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("formUsuario");

    const username = document.getElementById("username");
    const email = document.getElementById("email");
    const telefono = document.getElementById("telefono");
    const rol = document.getElementById("rol");
    const password = document.getElementById("password");
    const password2 = document.getElementById("password2");
    const foto = document.getElementById("foto");

    const tbody = document.getElementById("usersTable");
    const searchInput = document.getElementById("searchInput");
    const noResults = document.getElementById("noResults");
    const pagination = document.querySelector(".pagination");


    /*
    ==================================================
    MOSTRAR / OCULTAR FORMULARIO
    ==================================================
    */

    window.mostrarFormulario = function () {

        const formulario = document.getElementById(
            "formularioUsuario"
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
            "formularioUsuario"
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
    ERRORES DE VALIDACIÓN
    ==================================================
    */

    function mostrarError(input, mensaje) {

        if (!input) return;

        input.classList.add("input-error");

        const contenedor = input.closest(".form-group");

        if (!contenedor) return;

        let error = contenedor.querySelector(".error-text");

        if (!error) {

            error = document.createElement("small");
            error.className = "error-text";

            contenedor.appendChild(error);
        }

        error.textContent = mensaje;
    }


    function limpiarError(input) {

        if (!input) return;

        input.classList.remove("input-error");

        const contenedor = input.closest(".form-group");

        if (!contenedor) return;

        const error = contenedor.querySelector(".error-text");

        if (error) {
            error.remove();
        }
    }


    /*
    ==================================================
    VALIDACIONES
    ==================================================
    */

    function validarUsername() {

        if (!username) return true;

        const valor = username.value.trim();

        if (valor === "") {
            mostrarError(username, "El nombre de usuario es obligatorio.");
            return false;
        }

        if (valor.length < 3) {
            mostrarError(username, "Debe tener al menos 3 caracteres.");
            return false;
        }

        if (valor.length > 150) {
            mostrarError(username, "No puede superar los 150 caracteres.");
            return false;
        }

        limpiarError(username);
        return true;
    }


    function validarEmail() {

        if (!email) return true;

        const valor = email.value.trim();

        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (valor === "") {
            mostrarError(email, "El correo electrónico es obligatorio.");
            return false;
        }

        if (!regex.test(valor)) {
            mostrarError(email, "Ingresa un correo electrónico válido.");
            return false;
        }

        limpiarError(email);
        return true;
    }


    function validarTelefono() {

        if (!telefono) return true;

        const valor = telefono.value.trim();

        /* El teléfono es opcional */
        if (valor === "") {
            limpiarError(telefono);
            return true;
        }

        if (!/^[0-9]+$/.test(valor)) {
            mostrarError(telefono, "El teléfono solo puede contener números.");
            return false;
        }

        if (valor.length < 7 || valor.length > 10) {
            mostrarError(telefono, "El teléfono debe tener entre 7 y 10 números.");
            return false;
        }

        limpiarError(telefono);
        return true;
    }


    function validarRol() {

        if (!rol) return true;

        if (rol.value === "") {
            mostrarError(rol, "Selecciona un rol.");
            return false;
        }

        limpiarError(rol);
        return true;
    }


    function validarPassword() {

        /* Solo existe en el formulario de creación */
        if (!password || !password2) return true;

        const valor = password.value;
        const valor2 = password2.value;

        if (valor === "") {
            mostrarError(password, "La contraseña es obligatoria.");
            return false;
        }

        if (valor.length < 8) {
            mostrarError(password, "Debe tener al menos 8 caracteres.");
            return false;
        }

        limpiarError(password);

        if (valor2 === "") {
            mostrarError(password2, "Confirma la contraseña.");
            return false;
        }

        if (valor !== valor2) {
            mostrarError(password2, "Las contraseñas no coinciden.");
            return false;
        }

        limpiarError(password2);
        return true;
    }


    /*
    ==================================================
    VALIDACIÓN EN TIEMPO REAL
    ==================================================
    */

    if (username) {
        username.addEventListener("input", validarUsername);
        username.addEventListener("blur", validarUsername);
    }

    if (email) {
        email.addEventListener("input", validarEmail);
        email.addEventListener("blur", validarEmail);
    }

    if (telefono) {

        telefono.addEventListener("input", function () {
            this.value = this.value.replace(/\D/g, "");
            validarTelefono();
        });

        telefono.addEventListener("blur", validarTelefono);
    }

    if (rol) {
        rol.addEventListener("change", validarRol);
    }

    if (password) {
        password.addEventListener("input", validarPassword);
        password.addEventListener("blur", validarPassword);
    }

    if (password2) {
        password2.addEventListener("input", validarPassword);
        password2.addEventListener("blur", validarPassword);
    }


    /*
    ==================================================
    VISTA PREVIA DE FOTO
    ==================================================
    */

    if (foto) {

        foto.addEventListener("change", function () {

            const archivo = this.files && this.files[0];

            if (!archivo) return;

            const preview = document.getElementById("fotoPreview");
            const img = document.getElementById("fotoPreviewImg");
            const icono = document.getElementById("fotoPreviewIcono");

            const lector = new FileReader();

            lector.onload = function (e) {

                if (img) {
                    img.src = e.target.result;
                    img.style.display = "block";
                }

                if (icono) {
                    icono.style.display = "none";
                }
            };

            lector.readAsDataURL(archivo);
        });
    }


    /*
    ==================================================
    VALIDACIÓN FINAL DEL FORMULARIO
    ==================================================
    */

    if (form) {

        form.addEventListener("submit", function (e) {

            const usernameValido = validarUsername();
            const emailValido = validarEmail();
            const telefonoValido = validarTelefono();
            const rolValido = validarRol();
            const passwordValida = validarPassword();

            if (
                !usernameValido ||
                !emailValido ||
                !telefonoValido ||
                !rolValido ||
                !passwordValida
            ) {

                e.preventDefault();

                Swal.fire({
                    icon: "error",
                    title: "No se puede guardar",
                    text: "Revisa los campos marcados en rojo.",
                    confirmButtonText: "Entendido",
                    confirmButtonColor: "#df6d86"
                });
            }

        });
    }


    /*
    ==================================================
    CONFIRMACIÓN PARA ELIMINAR
    ==================================================
    */

    const formulariosEliminar = document.querySelectorAll(".delete-form");

    formulariosEliminar.forEach(function (formulario) {

        formulario.addEventListener("submit", function (e) {

            e.preventDefault();

            Swal.fire({
                icon: "warning",
                title: "¿Eliminar usuario?",
                text: "Esta acción no se puede deshacer.",
                showCancelButton: true,
                confirmButtonText: "Sí, eliminar",
                cancelButtonText: "Cancelar",
                confirmButtonColor: "#e11d48",
                cancelButtonColor: "#8b8593",
                reverseButtons: true
            }).then(function (resultado) {

                if (resultado.isConfirmed) {
                    formulario.submit();
                }
            });
        });
    });


    /*
    ==================================================
    MENSAJES DE DJANGO CON SWEETALERT
    ==================================================
    */

    const mensajes = document.querySelectorAll(".django-message");

    mensajes.forEach(function (mensaje) {

        const texto = mensaje.dataset.message;
        const tipo = mensaje.dataset.tag || "success";

        let icono = "success";
        let titulo = "¡Listo!";

        if (tipo.includes("error") || tipo.includes("danger")) {
            icono = "error";
            titulo = "Ha ocurrido un error";
        } else if (tipo.includes("warning")) {
            icono = "warning";
            titulo = "Atención";
        } else if (tipo.includes("info")) {
            icono = "info";
            titulo = "Información";
        }

        Swal.fire({
            icon: icono,
            title: titulo,
            text: texto,
            confirmButtonText: "Aceptar",
            confirmButtonColor: "#df6d86"
        });
    });


    /*
    ==================================================
    BUSCADOR (filtra la página actual de la tabla)
    ==================================================
    */

    function normalizar(texto) {

        return texto
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    if (searchInput && tbody) {

        const filas = Array.from(tbody.querySelectorAll("tr"));

        searchInput.addEventListener("input", function () {

            const termino = normalizar(searchInput.value.trim());

            let visibles = 0;

            filas.forEach(function (fila) {

                const texto = normalizar(fila.textContent);
                const coincide = texto.includes(termino);

                fila.style.display = coincide ? "" : "none";

                if (coincide) visibles++;
            });

            if (noResults) {
                noResults.style.display = visibles === 0 ? "block" : "none";
            }

            /*
            La paginación es de Django (por servidor), así que al
            buscar solo tiene sentido dentro de la página actual;
            la ocultamos mientras el usuario está filtrando.
            */

            if (pagination) {
                pagination.style.display = termino === "" ? "flex" : "none";
            }
        });
    }

});