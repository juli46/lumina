const modal = document.getElementById("modal");
const modalContent = document.getElementById("modalContent");

/* =========================
   VARIABLES TEST
========================= */

let respuestas = {};
let preguntas = [];
let preguntaActual = 0;
let testActual = null;

/* =========================
   SCROLL
========================= */

window.scrollSection = function (id) {

    const section = document.getElementById(id);

    if (section) {

        section.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }

};

/* =========================
   MODAL
========================= */

window.closeModal = function () {

    modal.style.display = "none";
    modalContent.innerHTML = "";

};

window.onclick = function (e) {

    if (e.target === modal) {

        closeModal();

    }

};

/* =========================
   GALERÍA
========================= */

window.openGallery = async function (id) {

    try {

        const response = await fetch(`/galeria-modal/${id}/`);

        if (!response.ok) {

            throw new Error("Error al cargar la galería");

        }

        const item = await response.json();

        modal.style.display = "flex";

        modalContent.innerHTML = `

            <button
                class="close-btn"
                onclick="closeModal()">

                ✖

            </button>

            <img
                src="${item.imagen}"
                alt="${item.titulo}"
                style="
                    width:100%;
                    max-height:70vh;
                    object-fit:contain;
                    border-radius:20px;
                ">

            <h2 style="margin-top:15px;">
                ${item.titulo}
            </h2>

            <p>

                <strong>Categoría:</strong>

                ${item.categoria}

            </p>

            <p>

                ${item.descripcion}

            </p>

            ${item.tags ?

                `<div class="galeria-tags">

                    ${item.tags
                    .split(",")
                    .map(tag => `<span class="tag">${tag.trim()}</span>`)
                    .join("")}

                </div>`

                : ""

            }

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

/* =========================
   BLOG
========================= */

async function abrirBlog(id) {

    try {

        const response = await fetch(`/blog-modal/${id}/`);

        if (!response.ok) {

            throw new Error();

        }

        const blog = await response.json();

        let html = `

            <h1>${blog.titulo}</h1>

            <p>${blog.resumen}</p>

        `;

        if (blog.secciones) {

            blog.secciones.forEach(seccion => {

                html += `

                    <div class="blog-seccion">

                        <h2>${seccion.subtitulo}</h2>

                        <div class="blog-contenido">

                            ${seccion.contenido.replace(/\n/g, "<br>")}

                        </div>

                        ${seccion.imagen ?

                        `<img src="${seccion.imagen}">`

                        :

                        ""

                    }

                    </div>

                `;

            });

        }

        document.getElementById("blogContenido").innerHTML = html;

        document.getElementById("blogModal").style.display = "flex";

    }

    catch {

        Swal.fire(
            "Error",
            "No se pudo cargar el artículo",
            "error"
        );

    }

}

function cerrarBlog() {

    document.getElementById("blogModal").style.display = "none";

}

/* =========================
   ABRIR TEST
========================= */

window.abrirTest = async function (id) {

    const response = await fetch(`/test/${id}/`);

    const data = await response.json();

    respuestas = {};

    preguntas = data.preguntas;

    preguntaActual = 0;

    testActual = data;

    if (!testActual.id) {
        testActual.id = id;
    }

    document.getElementById("testModal").style.display = "flex";

    mostrarPregunta();

}

/* =========================
   MOSTRAR PREGUNTA
========================= */

function mostrarPregunta() {

    const pregunta = preguntas[preguntaActual];

    let html = `

        <button
            class="close-test"
            onclick="cerrarTest()">

            &times;

        </button>

        <h2 class="quiz-title">

            ${testActual.titulo}

        </h2>

        <div class="quiz-progress">

            Pregunta ${preguntaActual + 1} de ${preguntas.length}

        </div>

        <div class="question-card">

            <h3>

                ${pregunta.texto}

            </h3>

            <div class="options">

    `;

    pregunta.opciones.forEach(opcion => {

        html += `

            <button
                class="option-btn"
                onclick="seleccionarOpcion(${opcion.resultado.id})">

                ${opcion.texto}

            </button>

        `;

    });

    html += `

            </div>

        </div>

    `;

    document.getElementById("testContent").innerHTML = html;

}

/* =========================
   SIGUIENTE PREGUNTA
========================= */

function seleccionarOpcion(idResultado) {

    respuestas[preguntaActual] = idResultado;

    preguntaActual++;

    if (preguntaActual < preguntas.length) {

        mostrarPregunta();

    } else {

        mostrarResultado();

    }

}

/* =========================
   MOSTRAR RESULTADO
========================= */

function mostrarResultado() {

    const conteo = {};

    Object.values(respuestas).forEach(id => {

        conteo[id] = (conteo[id] || 0) + 1;

    });

    let ganador = null;
    let mayor = 0;

    for (const id in conteo) {

        if (conteo[id] > mayor) {

            mayor = conteo[id];
            ganador = id;

        }

    }

    let resultadoFinal = null;

    preguntas.forEach(pregunta => {

        pregunta.opciones.forEach(opcion => {

            if (
                opcion.resultado.id == ganador &&
                resultadoFinal === null
            ) {

                resultadoFinal = opcion.resultado;

            }

        });

    });

    if (!resultadoFinal) {

        Swal.fire({

            icon: "error",
            title: "Error",
            text: "No fue posible calcular el resultado."

        });

        return;

    }

    document.getElementById("testContent").innerHTML = `

        <div class="result-card">

            <h2>

                 ${resultadoFinal.nombre}

            </h2>

            ${resultadoFinal.imagen
            ?

            `<img
                    src="${resultadoFinal.imagen}"
                    alt="${resultadoFinal.nombre}"
                    class="result-image">`

            :

            ""
        }

            <p>

                ${resultadoFinal.descripcion.trim()}

            </p>

            <button
                class="btn-final"
                onclick="cerrarTest()">

                Finalizar

            </button>

        </div>

    `;

    if (testActual && testActual.id && resultadoFinal.id) {

        guardarResultadoUsuario(testActual.id, resultadoFinal.id)
            .catch(error => console.error("No se pudo guardar el resultado:", error));

    }

}

/* =========================
   CERRAR TEST
========================= */

function cerrarTest() {

    document.getElementById("testModal").style.display = "none";

    document.getElementById("testContent").innerHTML = "";

    respuestas = {};
    preguntas = [];
    preguntaActual = 0;
    testActual = null;

}

/* =========================
   CERRAR BLOG
========================= */

window.onclick = function (e) {

    if (e.target === document.getElementById("blogModal")) {

        cerrarBlog();

    }

    if (e.target === document.getElementById("testModal")) {

        cerrarTest();

    }

    if (e.target === modal) {

        closeModal();

    }

};

/* =========================
   GUARDAR RESULTADO USUARIO
========================= */

function getCookie(name) {
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
        cookie = cookie.trim();

        if (cookie.startsWith(name + "=")) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }

    return null;
}

async function guardarResultadoUsuario(testId, resultadoId) {
    const formData = new FormData();

    formData.append("test_id", testId);
    formData.append("resultado_id", resultadoId);

    const response = await fetch("/guardar-resultado/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: formData
    });

    if (response.status === 403 || response.redirected) {
        console.warn("El usuario debe iniciar sesión para guardar el resultado.");
        return;
    }

    const data = await response.json();

    if (!response.ok || !data.ok) {
        console.error(data.error || "No se pudo guardar el resultado");
        return;
    }

    console.log("Resultado guardado:", data.resultado);
}

document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const testId = params.get("test");

    if (testId) {
        abrirTest(testId);
    }
});