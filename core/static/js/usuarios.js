
document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // BUSCADOR DE USUARIOS
    // =========================================================

    const input = document.getElementById("searchInput");
    const rows = document.querySelectorAll("#usersTable tr");
    const table = document.getElementById("usersTable");
    const noResults = document.getElementById("noResults");

    input?.addEventListener("input", () => {

        const value = input.value
            .trim()
            .toLowerCase();

        let encontrados = 0;

        rows.forEach(row => {

            const username =
                row.children[0]?.innerText.toLowerCase() || "";

            const email =
                row.children[1]?.innerText.toLowerCase() || "";

            const telefono =
                row.children[2]?.innerText.toLowerCase() || "";

            const rol =
                row.children[3]?.innerText.toLowerCase() || "";

            const estado =
                row.children[4]?.innerText.toLowerCase() || "";

            const coincide =
                username.includes(value) ||
                email.includes(value) ||
                telefono.includes(value) ||
                rol.includes(value) ||
                estado.includes(value);

            row.style.display = coincide ? "" : "none";

            if (coincide) {
                encontrados++;
            }
        });

        // =====================================================
        // SIN RESULTADOS
        // =====================================================

        if (encontrados === 0 && value !== "") {

            table.style.display = "none";
            noResults.style.display = "block";

        } else {

            table.style.display = "";
            noResults.style.display = "none";

        }

    });


    // =========================================================
    // ELIMINAR USUARIO
    // =========================================================

    document.querySelectorAll(".delete-form").forEach(form => {

        form.addEventListener("submit", function (e) {

            e.preventDefault();

            Swal.fire({

                icon: "warning",

                title: "¿Eliminar usuario?",

                text: "Esta acción no se puede deshacer.",

                showCancelButton: true,

                confirmButtonText: "Sí, eliminar",

                cancelButtonText: "Cancelar",

                confirmButtonColor: "#dc2626",

                cancelButtonColor: "#6b7280",

                reverseButtons: true,

                focusCancel: true

            }).then((result) => {

                if (result.isConfirmed) {

                    // Envía el formulario mediante POST
                    form.submit();

                }

            });

        });

    });

});
