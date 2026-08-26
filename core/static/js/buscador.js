function normalizeText(text) {
    return text
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();
}
document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("searchInput");

    if (!input) return;

    const searchableItems = document.querySelectorAll(".searchable-item");

    /* MENSAJE */
    const noResults = document.createElement("div");

    noResults.className = "no-results";

    noResults.innerHTML = `
        <h3>No se encontraron resultados 💔</h3>
        <p>Prueba con otra palabra clave</p>
    `;

    noResults.style.display = "none";

    const footer = document.querySelector("footer");

    if (footer) {
        footer.parentNode.insertBefore(noResults, footer);
    } else {
        document.body.appendChild(noResults);
    }

    /* CSS DINÁMICO */
    const style = document.createElement("style");

    style.innerHTML = `
        .hidden-search{
            display:none !important;
        }

        .no-results{
            text-align:center;
            padding:90px 20px;
            color:#777;
        }

        .no-results h3{
            font-size:2rem;
            margin-bottom:10px;
            color:#ff4f87;
        }

        .no-results p{
            font-size:1rem;
        }
    `;

    document.head.appendChild(style);

    /* BUSCADOR */
    input.addEventListener("input", () => {

        const value = normalizeText(input.value);

        let found = false;

        searchableItems.forEach(item => {

            const text = normalizeText(
                item.innerText + " " + (item.dataset.tags || "")
            );

            const match = text.includes(value);

            if (value === "" || match) {

                item.classList.remove("hidden-search");
                found = true;

            } else {

                item.classList.add("hidden-search");
            }

        });

        /* OCULTAR SECCIONES VACÍAS */
        document.querySelectorAll("section").forEach(section => {

            const visibleItems = section.querySelectorAll(
                ".searchable-item:not(.hidden-search)"
            );

            if (value === "" || visibleItems.length > 0) {

                section.style.display = "";

            } else {

                section.style.display = "none";
            }

        });

        /* MENSAJE */
        if (value !== "" && !found) {

            noResults.style.display = "block";

        } else {

            noResults.style.display = "none";
        }

    });

});