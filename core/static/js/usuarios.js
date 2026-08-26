// Buscador de usuarios
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    const rows = document.querySelectorAll("#usersTable tr");
    const table = document.getElementById("usersTable");
    const noResults = document.getElementById("noResults");

    input?.addEventListener("input", () => {
        const value = input.value.toLowerCase();
        let encontrados = 0;

        rows.forEach(row => {
            const username = row.children[0]?.innerText.toLowerCase() || "";
            const email = row.children[1]?.innerText.toLowerCase() || "";
            const telefono = row.children[2]?.innerText.toLowerCase() || "";
            const rol = row.children[3]?.innerText.toLowerCase() || "";
            const estado = row.children[4]?.innerText.toLowerCase() || "";

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

        if (encontrados === 0) {
            table.style.display = "none";
            noResults.style.display = "block";
        } else {
            table.style.display = "";
            noResults.style.display = "none";
        }

        if (value === "") {
            table.style.display = "";
            noResults.style.display = "none";
        }
    });

    document.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();

            const url = btn.getAttribute("href");

            Swal.fire({
                icon: "warning",
                title: "¿Eliminar usuario?",
                text: "Esta acción no se puede deshacer.",
                showCancelButton: true,
                confirmButtonText: "Sí, eliminar",
                cancelButtonText: "Cancelar",
                confirmButtonColor: "#dc2626",
                cancelButtonColor: "#6b7280"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});