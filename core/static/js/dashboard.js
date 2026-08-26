
    // =====================
    // MENÚ PERFIL
    // =====================

    const profileMenu =
        document.getElementById("profileMenu");

    if (profileMenu) {

        profileMenu.addEventListener("click", (e) => {

            e.stopPropagation();

            profileMenu.classList.toggle("active");

        });

        document.addEventListener("click", () => {

            profileMenu.classList.remove("active");

        });

    }

    // =====================
    // DARK MODE
    // =====================
    document.addEventListener("DOMContentLoaded", () => {

    const themeSelect = document.getElementById("themeSelect");
    const colorSelect = document.getElementById("colorSelect");
    const fontSizeSelect = document.getElementById("fontSizeSelect");

    // =====================
    // APLICAR CONFIG GUARDADA AL RECARGAR
    // =====================

    const savedTheme = localStorage.getItem("theme");
    const savedColor = localStorage.getItem("primary");
    const savedFont = localStorage.getItem("font");

    // 🌙 tema
    if (savedTheme === "dark") {
        document.body.classList.add("dark");
        if (themeSelect) themeSelect.value = "dark";
    } else if (themeSelect) {
        themeSelect.value = "light";
    }

    // 🎨 color
    if (savedColor) {
        document.documentElement.style.setProperty("--primary", savedColor);
        if (colorSelect) colorSelect.value = savedColor;
    }

    // 🔠 fuente
    if (savedFont) {
        document.documentElement.style.fontSize = savedFont;
        if (fontSizeSelect) fontSizeSelect.value = savedFont;
    }

    // =====================
    // EVENTOS (GUARDAR CAMBIOS)
    // =====================

    themeSelect?.addEventListener("change", (e) => {
        const value = e.target.value;

        if (value === "dark") {
            document.body.classList.add("dark");
            localStorage.setItem("theme", "dark");
        } else {
            document.body.classList.remove("dark");
            localStorage.setItem("theme", "light");
        }
    });

    colorSelect?.addEventListener("change", (e) => {
        localStorage.setItem("primary", e.target.value);
        document.documentElement.style.setProperty("--primary", e.target.value);
    });

    fontSizeSelect?.addEventListener("change", (e) => {
        localStorage.setItem("font", e.target.value);
        document.documentElement.style.fontSize = e.target.value;
    });

});

function toggleSidebar(){
    document.querySelector('.sidebar')
        .classList.toggle('active');
}