/* =========================================================
   LÚMINA — TIPS / TESTS / BLOG / GALERÍA
========================================================= */


/* =========================================================
   VARIABLES GENERALES
========================================================= */

const modal = document.getElementById("modal");
const modalContent = document.getElementById("modalContent");

let respuestas = {};
let preguntas = [];
let preguntaActual = 0;
let testActual = null;


/* =========================================================
   SCROLL ENTRE SECCIONES
========================================================= */

window.scrollSection = function (id) {

    const section = document.getElementById(id);

    if (!section) {
        console.warn(`No existe la sección #${id}`);
        return;
    }

    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

};


/* =========================================================
   MODAL GENERAL — GALERÍA
========================================================= */

window.closeModal = function () {

    if (!modal) return;

    modal.style.display = "none";

    if (modalContent) {
        modalContent.innerHTML = "";
    }

    document.body.classList.remove("modal-open");

};


/* =========================================================
   GALERÍA
========================================================= */
window.openGallery = async function (id) {

    try {

        const response = await fetch(`/galeria-modal/${id}/`);

        if (!response.ok) {
            throw new Error("Error al cargar la galería");
        }

        const item = await response.json();

        modal.style.display = "flex";

        let tagsHTML = "";

        if (item.tags) {

            tagsHTML = `
                <div class="gallery-modal-tags">

                    ${item.tags
                        .split(",")
                        .map(tag => `
                            <span>${tag.trim()}</span>
                        `)
                        .join("")}

                </div>
            `;

        }

        modalContent.innerHTML = `

            <button
                class="gallery-modal-close"
                onclick="closeModal()"
                aria-label="Cerrar">

                &times;

            </button>


            <div class="gallery-modal-layout">

                <!-- IMAGEN -->

                <div class="gallery-modal-photo">

                    <img
                        src="${item.imagen}"
                        alt="${item.titulo}">

                    <div class="gallery-photo-caption">
                        LÚMINA BEAUTY
                    </div>

                </div>


                <!-- INFORMACIÓN -->

                <div class="gallery-modal-info">

                    <span class="gallery-modal-kicker">
                        ${item.categoria}
                    </span>


                    <h2>
                        ${item.titulo}
                    </h2>


                    <div class="gallery-modal-line"></div>


                    <p class="gallery-modal-description">
                        ${item.descripcion || ""}
                    </p>


                    ${tagsHTML}


                    <div class="gallery-modal-footer">

                        <span>
                            INSPIRACIÓN LÚMINA
                        </span>

                        <span class="gallery-footer-star">
                            ✦
                        </span>

                    </div>

                </div>

            </div>

        `;

    }

    catch (error) {

        console.error(error);

        Swal.fire(
            "Error",
            "No se pudo cargar la imagen",
            "error"
        );

    }

};


/* =========================================================
   BLOG
========================================================= */
async function abrirBlog(id) {

    try {

        const response = await fetch(`/blog-modal/${id}/`);

        if (!response.ok) {
            throw new Error("No se pudo cargar el artículo");
        }

        const blog = await response.json();

        let seccionesHTML = "";

        if (blog.secciones && blog.secciones.length) {

            blog.secciones.forEach((seccion, index) => {

                seccionesHTML += `

                    <section class="lumina-blog-section">

                        <h2>
                            ${seccion.subtitulo}
                        </h2>

                        <div class="lumina-blog-divider"></div>

                        <div class="lumina-blog-text">
                            ${
                                seccion.contenido
                                    ? seccion.contenido.replace(/\n/g, "<br>")
                                    : ""
                            }
                        </div>

                        ${
                            seccion.imagen
                            ?
                            `
                                <div class="lumina-blog-image">

                                    <img
                                        src="${seccion.imagen}"
                                        alt="${seccion.subtitulo || blog.titulo}">

                                </div>
                            `
                            :
                            ""
                        }

                    </section>

                `;

            });

        } else {

            seccionesHTML = `

                <div class="lumina-blog-empty">

                    <div>✦</div>

                    <p>
                        Este artículo todavía no tiene contenido.
                    </p>

                </div>

            `;

        }


        document.getElementById("blogContenido").innerHTML = `

            <button
                class="lumina-blog-close"
                onclick="cerrarBlog()"
                aria-label="Cerrar artículo">

                <span></span>
                <span></span>

            </button>


            <div class="lumina-blog-top-decoration">
                <span></span>
                <b> LÚMINA </b>
                <span></span>
            </div>


            <header class="lumina-blog-hero">

                ${
                    blog.portada
                    ?
                    `
                    <div class="lumina-blog-cover">

                        <img
                            src="${blog.portada}"
                            alt="${blog.titulo}">

                        <div class="lumina-blog-cover-overlay"></div>

                    </div>
                    `
                    :
                    ""
                }


                <div class="lumina-blog-heading">

                    <span class="lumina-blog-category">
                        BEAUTY & TIPS
                    </span>

                    <h1>
                        ${blog.titulo}
                    </h1>

                    ${
                        blog.resumen
                        ?
                        `
                        <p>
                            ${blog.resumen}
                        </p>
                        `
                        :
                        ""
                    }

                    ${
                        blog.fecha
                        ?
                        `
                        <small>
                            ${blog.fecha}
                        </small>
                        `
                        :
                        ""
                    }

                </div>

            </header>


            <article class="lumina-blog-body">

                ${seccionesHTML}

            </article>


            <footer class="lumina-blog-end">

                <div class="lumina-blog-end-line"></div>

                <span>Hecho para ti por</span>

                <strong>Lúmina</strong>

                <i>✦</i>

            </footer>

        `;


        document.getElementById("blogModal").style.display = "flex";

        document.body.classList.add("modal-open");

    }

    catch (error) {

        console.error(error);

        Swal.fire(
            "Error",
            "No se pudo cargar el artículo",
            "error"
        );

    }

}


function cerrarBlog() {

    document.getElementById("blogModal").style.display = "none";

    document.getElementById("blogContenido").innerHTML = "";

    document.body.classList.remove("modal-open");

}

/* =========================================================
   CERRAR BLOG
========================================================= */

window.cerrarBlog = function () {

    const blogModal = document.getElementById("blogModal");
    const blogContenido = document.getElementById("blogContenido");

    if (blogModal) {
        blogModal.style.display = "none";
    }

    if (blogContenido) {
        blogContenido.innerHTML = "";
    }

    document.body.classList.remove("modal-open");

};


/* =========================================================
   ABRIR TEST
========================================================= */

window.abrirTest = async function (id) {

    const testModal = document.getElementById("testModal");
    const testContent = document.getElementById("testContent");

    if (!testModal || !testContent) return;

    try {

        testContent.innerHTML = `

            <div class="test-loading">

                <div class="loading-spinner"></div>

                <p>
                    Preparando tu beauty test...
                </p>

            </div>

        `;

        testModal.style.display = "flex";

        document.body.classList.add("modal-open");

        const response = await fetch(`/test/${id}/`);

        if (!response.ok) {
            throw new Error("No se pudo cargar el test.");
        }

        const data = await response.json();

        if (!data || !Array.isArray(data.preguntas)) {
            throw new Error("El test no tiene preguntas válidas.");
        }

        if (data.preguntas.length === 0) {
            throw new Error("Este test todavía no tiene preguntas.");
        }

        respuestas = {};
        preguntas = data.preguntas;
        preguntaActual = 0;
        testActual = data;

        /*
         * Algunos endpoints pueden no devolver el ID.
         * En ese caso utilizamos el ID recibido.
         */

        if (!testActual.id) {
            testActual.id = id;
        }

        mostrarPregunta();

    }

    catch (error) {

        console.error("Error al abrir test:", error);

        testContent.innerHTML = "";

        testModal.style.display = "none";

        document.body.classList.remove("modal-open");

        Swal.fire({
            icon: "error",
            title: "No pudimos abrir el test",
            text: error.message || "Ocurrió un problema al cargarlo.",
            confirmButtonText: "Entendido"
        });

    }

};


/* =========================================================
   MOSTRAR PREGUNTA
========================================================= */

function mostrarPregunta() {

    const testContent = document.getElementById("testContent");

    if (!testContent) return;

    const pregunta = preguntas[preguntaActual];

    if (!pregunta) {
        mostrarResultado();
        return;
    }

    const porcentaje =
        ((preguntaActual + 1) / preguntas.length) * 100;

    let html = `

        <button
            class="close-test"
            type="button"
            onclick="cerrarTest()"
            aria-label="Cerrar">

            <i class="fa-solid fa-xmark"></i>

        </button>

        <div class="quiz-header">

            <span class="quiz-label">
                BEAUTY TEST
            </span>

            <h2 class="quiz-title">
                ${testActual.titulo || "Tu Beauty Style"}
            </h2>

            <div class="quiz-progress-info">

                <span>
                    Pregunta ${preguntaActual + 1}
                    de ${preguntas.length}
                </span>

                <span>
                    ${Math.round(porcentaje)}%
                </span>

            </div>

            <div class="quiz-progress-bar">

                <div
                    class="quiz-progress-fill"
                    style="width:${porcentaje}%">
                </div>

            </div>

        </div>

        <div class="question-card">

            <span class="question-number">
                0${preguntaActual + 1}
            </span>

            <h3>
                ${pregunta.texto || "Selecciona una opción"}
            </h3>

            <div class="options">

    `;

    if (
        !pregunta.opciones ||
        pregunta.opciones.length === 0
    ) {

        html += `

            <div class="quiz-empty">

                <i class="fa-regular fa-circle-xmark"></i>

                <p>
                    Esta pregunta no tiene opciones disponibles.
                </p>

            </div>

        `;

    } else {

        pregunta.opciones.forEach((opcion, index) => {

            html += `

                <button
                    class="option-btn"
                    type="button"
                    onclick="seleccionarOpcion(${opcion.resultado.id})">

                    <span class="option-number">
                        ${String.fromCharCode(65 + index)}
                    </span>

                    <span class="option-text">
                        ${opcion.texto || ""}
                    </span>

                    <i class="fa-solid fa-arrow-right"></i>

                </button>

            `;

        });

    }

    html += `

            </div>

        </div>

    `;

    testContent.innerHTML = html;

}


/* =========================================================
   SELECCIONAR OPCIÓN
========================================================= */

window.seleccionarOpcion = function (idResultado) {

    if (!idResultado) {
        console.warn("La opción seleccionada no tiene resultado.");
        return;
    }

    respuestas[preguntaActual] = idResultado;

    preguntaActual++;

    if (preguntaActual < preguntas.length) {

        mostrarPregunta();

    } else {

        mostrarResultado();

    }

};


/* =========================================================
   MOSTRAR RESULTADO
========================================================= */

function mostrarResultado() {

    const testContent = document.getElementById("testContent");

    if (!testContent) return;

    const conteo = {};

    /*
     * Contamos cuántas veces apareció cada resultado.
     */

    Object.values(respuestas).forEach(id => {

        conteo[id] = (conteo[id] || 0) + 1;

    });


    /* -----------------------------------------------------
       BUSCAR EL RESULTADO GANADOR
    ----------------------------------------------------- */

    let ganador = null;
    let mayor = 0;

    for (const id in conteo) {

        if (conteo[id] > mayor) {

            mayor = conteo[id];
            ganador = id;

        }

    }


    /* -----------------------------------------------------
       BUSCAR EL OBJETO COMPLETO DEL RESULTADO
    ----------------------------------------------------- */

    let resultadoFinal = null;

    preguntas.forEach(pregunta => {

        if (!pregunta.opciones) return;

        pregunta.opciones.forEach(opcion => {

            if (
                String(opcion.resultado.id) === String(ganador) &&
                resultadoFinal === null
            ) {

                resultadoFinal = opcion.resultado;

            }

        });

    });


    if (!resultadoFinal) {

        Swal.fire({
            icon: "error",
            title: "No pudimos calcular tu resultado",
            text: "Intenta realizar nuevamente el test.",
            confirmButtonText: "Entendido"
        });

        return;

    }


    /* -----------------------------------------------------
       RESULTADO VISUAL
    ----------------------------------------------------- */

    testContent.innerHTML = `

        <button
            class="close-test"
            type="button"
            onclick="cerrarTest()"
            aria-label="Cerrar">

            <i class="fa-solid fa-xmark"></i>

        </button>

        <div class="result-card">

            <div class="result-label">
                TU RESULTADO
            </div>

            <div class="result-decoration">
                <span></span>
                <i class="fa-solid fa-sparkles"></i>
                <span></span>
            </div>

            <h2>
                ${resultadoFinal.nombre || "Tu Beauty Style"}
            </h2>

            ${
                resultadoFinal.imagen
                ?
                `
                <div class="result-image-wrapper">

                    <img
                        src="${resultadoFinal.imagen}"
                        alt="${resultadoFinal.nombre || "Resultado"}"
                        class="result-image">

                </div>
                `
                :
                ""
            }

            ${
                resultadoFinal.descripcion
                ?
                `
                <p class="result-description">
                    ${resultadoFinal.descripcion.trim()}
                </p>
                `
                :
                ""
            }

            <div class="result-actions">

                <button
                    class="btn-final"
                    type="button"
                    onclick="cerrarTest()">

                    <span>
                        Finalizar
                    </span>

                    <i class="fa-solid fa-arrow-right"></i>

                </button>

            </div>

        </div>

    `;


    /* -----------------------------------------------------
       GUARDAR RESULTADO
    ----------------------------------------------------- */

    if (
        testActual &&
        testActual.id &&
        resultadoFinal.id
    ) {

        guardarResultadoUsuario(
            testActual.id,
            resultadoFinal.id
        )
        .catch(error => {

            console.error(
                "No se pudo guardar el resultado:",
                error
            );

        });

    }

}


/* =========================================================
   CERRAR TEST
========================================================= */

window.cerrarTest = function () {

    const testModal = document.getElementById("testModal");
    const testContent = document.getElementById("testContent");

    if (testModal) {
        testModal.style.display = "none";
    }

    if (testContent) {
        testContent.innerHTML = "";
    }

    respuestas = {};
    preguntas = [];
    preguntaActual = 0;
    testActual = null;

    document.body.classList.remove("modal-open");

};


/* =========================================================
   CSRF
========================================================= */

function getCookie(name) {

    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {

        cookie = cookie.trim();

        if (cookie.startsWith(name + "=")) {

            return decodeURIComponent(
                cookie.substring(name.length + 1)
            );

        }

    }

    return null;

}


/* =========================================================
   GUARDAR RESULTADO DEL USUARIO
========================================================= */

async function guardarResultadoUsuario(
    testId,
    resultadoId
) {

    const csrfToken = getCookie("csrftoken");

    if (!csrfToken) {

        console.warn(
            "No se encontró el token CSRF."
        );

        return;

    }

    const formData = new FormData();

    formData.append("test_id", testId);
    formData.append("resultado_id", resultadoId);

    const response = await fetch(
        "/guardar-resultado/",
        {
            method: "POST",

            headers: {
                "X-CSRFToken": csrfToken
            },

            body: formData
        }
    );


    /*
     * Usuario no autenticado.
     */

    if (
        response.status === 403 ||
        response.redirected
    ) {

        console.warn(
            "El usuario debe iniciar sesión para guardar el resultado."
        );

        return;

    }


    let data;

    try {

        data = await response.json();

    }

    catch {

        throw new Error(
            "El servidor devolvió una respuesta inválida."
        );

    }


    if (!response.ok || !data.ok) {

        throw new Error(
            data.error ||
            "No se pudo guardar el resultado."
        );

    }

    console.log(
        "Resultado guardado:",
        data.resultado
    );

}


/* =========================================================
   CERRAR MODALES AL HACER CLICK EN EL FONDO
========================================================= */

window.addEventListener("click", function (event) {

    const blogModal =
        document.getElementById("blogModal");

    const testModal =
        document.getElementById("testModal");


    /* Galería */

    if (
        modal &&
        event.target === modal
    ) {

        closeModal();

    }


    /* Blog */

    if (
        blogModal &&
        event.target === blogModal
    ) {

        cerrarBlog();

    }


    /* Test */

    if (
        testModal &&
        event.target === testModal
    ) {

        cerrarTest();

    }

});


/* =========================================================
   ESC — CERRAR MODAL
========================================================= */

window.addEventListener("keydown", function (event) {

    if (event.key !== "Escape") return;

    const blogModal =
        document.getElementById("blogModal");

    const testModal =
        document.getElementById("testModal");


    if (
        modal &&
        modal.style.display === "flex"
    ) {

        closeModal();

    }

    if (
        blogModal &&
        blogModal.style.display === "flex"
    ) {

        cerrarBlog();

    }

    if (
        testModal &&
        testModal.style.display === "flex"
    ) {

        cerrarTest();

    }

});


/* =========================================================
   APERTURA AUTOMÁTICA DEL TEST
   URL: /tips/?test=1
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const params =
            new URLSearchParams(
                window.location.search
            );

        const testId =
            params.get("test");

        if (testId) {

            abrirTest(testId);

        }

    }
);