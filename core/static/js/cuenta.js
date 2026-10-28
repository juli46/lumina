document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // ELIMINAR DIRECCIÓN (formulario POST + confirmación)
    // Si el JS fallara, el formulario igual se envía por POST.
    // =========================
    document.querySelectorAll(".delete-address-form").forEach(formEl => {

        formEl.addEventListener("submit", function (e) {

            e.preventDefault();

            Swal.fire({
                title: "¿Eliminar dirección?",
                text: "Esta acción no se puede deshacer.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Sí, eliminar",
                cancelButtonText: "Cancelar",
                confirmButtonColor: "#df6d77",
                cancelButtonColor: "#9ca3af"
            }).then(result => {

                if (result.isConfirmed) {
                    formEl.submit();
                }

            });

        });

    });

    // =========================
    // MODAL
    // =========================
    const modal = document.getElementById("addressModal");

    window.openModal = () => {
        modal?.classList.add("active");
    };

    window.closeModal = () => {
        modal?.classList.remove("active");
    };

    window.addEventListener("click", (e) => {

        if (e.target === modal) {
            modal.classList.remove("active");
        }

    });

    // =========================
    // DEPARTAMENTOS Y CIUDADES
    // =========================
    const data = {

        "Antioquia": [
            "Medellín","Bello","Itagüí","Envigado","Rionegro",
            "Apartadó","Turbo","La Ceja","Caldas","Sabaneta"
        ],

        "Cundinamarca": [
            "Bogotá","Soacha","Chía","Zipaquirá",
            "Facatativá","Madrid","Mosquera",
            "Fusagasugá","Girardot"
        ],

        "Valle del Cauca": [
            "Cali","Palmira","Buenaventura",
            "Tuluá","Buga","Cartago",
            "Jamundí","Yumbo"
        ],

        "Atlántico": [
            "Barranquilla","Soledad",
            "Malambo","Sabanalarga",
            "Puerto Colombia"
        ],

        "Bolívar": [
            "Cartagena","Magangué",
            "Turbaco","Arjona",
            "El Carmen de Bolívar"
        ],

        "Santander": [
            "Bucaramanga","Floridablanca",
            "Girón","Piedecuesta",
            "Barrancabermeja"
        ],

        "Norte de Santander": [
            "Cúcuta","Ocaña",
            "Pamplona","Villa del Rosario"
        ],

        "Tolima": [
            "Ibagué","Espinal",
            "Melgar","Honda"
        ],

        "Huila": [
            "Neiva","Pitalito","Garzón"
        ],

        "Caldas": [
            "Manizales","La Dorada","Chinchiná"
        ],

        "Risaralda": [
            "Pereira","Dosquebradas",
            "Santa Rosa de Cabal"
        ],

        "Quindío": [
            "Armenia","Calarcá","Montenegro"
        ],

        "Meta": [
            "Villavicencio","Acacías","Granada"
        ],

        "Córdoba": [
            "Montería","Lorica","Sahagún"
        ],

        "Sucre": [
            "Sincelejo","Corozal","Sampués"
        ],

        "Nariño": [
            "Pasto","Ipiales","Tumaco"
        ],

        "Boyacá": [
            "Tunja","Duitama",
            "Sogamoso","Chiquinquirá"
        ],

        "Cesar": [
            "Valledupar","Aguachica","Codazzi"
        ],

        "La Guajira": [
            "Riohacha","Maicao","Fonseca"
        ],

        "Chocó": [
            "Quibdó","Istmina","Tadó"
        ],

        "Amazonas": [
            "Leticia"
        ],

        "San Andrés y Providencia": [
            "San Andrés"
        ]
    };

    const form = document.getElementById("direccionForm");
    const depto = document.getElementById("departamento");
    const ciudad = document.getElementById("ciudad");

    // =========================
    // CARGAR DEPARTAMENTOS
    // =========================
    if (depto) {

        Object.keys(data).forEach(dep => {

            const option =
                document.createElement("option");

            option.value = dep;
            option.textContent = dep;

            depto.appendChild(option);

        });

    }

    // =========================
    // CAMBIO DE CIUDADES
    // =========================
    depto?.addEventListener("change", () => {

        ciudad.innerHTML =
            '<option value="">Selecciona una ciudad</option>';

        if (!data[depto.value]) return;

        data[depto.value].forEach(c => {

            const option =
                document.createElement("option");

            option.value = c;
            option.textContent = c;

            ciudad.appendChild(option);

        });

    });

    // =========================
    // FUNCIONES DE ERROR
    // =========================
    function error(input, msg) {

        const small =
            input.parentElement.querySelector(".error");

        if (small) {
            small.textContent = msg;
        }

        input.classList.add("input-error");
    }

    function ok(input) {

        const small =
            input.parentElement.querySelector(".error");

        if (small) {
            small.textContent = "";
        }

        input.classList.remove("input-error");
    }

    // =========================
    // SOLO LETRAS NOMBRE
    // =========================
    const nombreInput =
        form?.querySelector("[name='nombre_receptor']");

    nombreInput?.addEventListener("input", () => {

        nombreInput.value =
            nombreInput.value.replace(
                /[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g,
                ""
            );

    });

    // =========================
    // SOLO NÚMEROS TELÉFONO
    // =========================
    const telefonoInput =
        form?.querySelector("[name='telefono']");

    telefonoInput?.addEventListener("input", () => {

        telefonoInput.value =
            telefonoInput.value.replace(/\D/g, "");

    });

    // =========================
    // VALIDAR FORMULARIO
    // =========================
    form?.addEventListener("submit", (e) => {

        let errores = 0;

        const nombre =
            form.querySelector("[name='nombre_receptor']");

        const telefono =
            form.querySelector("[name='telefono']");

        const direccion =
            form.querySelector("[name='direccion']");

        // NOMBRE
        if (!nombre.value.trim()) {

            error(nombre, "El nombre es obligatorio");
            errores++;

        } else if (nombre.value.trim().length < 3) {

            error(nombre, "Mínimo 3 caracteres");
            errores++;

        } else {

            ok(nombre);

        }

        // TELÉFONO
        if (!telefono.value.trim()) {

            error(telefono, "El teléfono es obligatorio");
            errores++;

        } else if (!/^[0-9]{10}$/.test(telefono.value)) {

            error(
                telefono,
                "Debe contener 10 números"
            );

            errores++;

        } else {

            ok(telefono);

        }

        // DIRECCIÓN
        if (!direccion.value.trim()) {

            error(
                direccion,
                "La dirección es obligatoria"
            );

            errores++;

        } else if (direccion.value.trim().length < 8) {

            error(
                direccion,
                "Dirección demasiado corta"
            );

            errores++;

        } else if (!/\d/.test(direccion.value)) {

            error(
                direccion,
                "Debe contener al menos un número"
            );

            errores++;

        } else {

            ok(direccion);

        }

        // DEPARTAMENTO
        if (!depto.value) {

            depto.classList.add("input-error");
            errores++;

        } else {

            depto.classList.remove("input-error");

        }

        // CIUDAD
        if (!ciudad.value) {

            ciudad.classList.add("input-error");
            errores++;

        } else {

            ciudad.classList.remove("input-error");

        }

        // BLOQUEAR ENVÍO
        if (errores > 0) {

            e.preventDefault();

            Swal.fire({
                icon: "error",
                title: "Formulario incompleto",
                text: "Corrige los campos marcados antes de continuar.",
                confirmButtonColor: "#df6d77"
            });

        }

    });

});

function abrirRutina(titulo, descripcion){

    document.getElementById("tituloRutina").textContent = titulo;

    document.getElementById("contenidoRutina").innerHTML =
        descripcion.replace(/\n/g,"<br>");

    document.getElementById("modalRutina").classList.add("active");

}

function cerrarRutina(){

    document.getElementById("modalRutina").classList.remove("active");

}

document.querySelectorAll(".eliminar-resultado").forEach(boton => {

    boton.addEventListener("click", function(e){

        e.preventDefault();

        const url = this.href;

        Swal.fire({

            title: "¿Eliminar resultado?",
            text: "Esta acción no se puede deshacer.",

            icon: "warning",

            showCancelButton: true,

            confirmButtonColor: "#df6d77",
            cancelButtonColor: "#999",

            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar"

        }).then((result)=>{

            if(result.isConfirmed){

                window.location.href = url;

            }

        });

    });

});


/* =========================================================
   RESEÑAS DE PRODUCTOS (modal en "Mis pedidos")
   Las reseñas se publican de inmediato (sin revisión previa).
   ========================================================= */
(function () {

    const modal = document.getElementById("rvModal");
    if (!modal) return;   // usuario no logueado

    const cuerpo = document.getElementById("rvCuerpo");
    const titulo = document.getElementById("rvTitulo");
    const CSRF   = modal.querySelector("[name=csrfmiddlewaretoken]").value;

    const URL_MIA   = modal.dataset.urlMia;
    const URL_CREAR = modal.dataset.urlCrear;
    const URL_ELIM  = modal.dataset.urlEliminar;   // /api/resenas/0/eliminar/

    const ESTADOS = {
        pendiente: "En revisión",
        aprobada: "Publicada",
        rechazada: "Oculta"
    };

    // Crea elementos con textContent (nunca innerHTML) para evitar XSS
    const el = (tag, cls, txt) => {
        const e = document.createElement(tag);
        if (cls) e.className = cls;
        if (txt !== undefined) e.textContent = txt;
        return e;
    };

    const abrir  = () => { modal.hidden = false; };
    const cerrar = () => { modal.hidden = true; cuerpo.replaceChildren(); };

    document.getElementById("rvCerrar").onclick = cerrar;

    modal.addEventListener("click", (e) => {
        if (e.target === modal) cerrar();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !modal.hidden) cerrar();
    });

    // ---------- LISTA DE PRODUCTOS DEL PEDIDO ----------
    async function mostrarLista(pedidoId) {

        titulo.textContent = "Reseñar productos";
        cuerpo.replaceChildren(el("p", "rv-aviso", "Cargando…"));

        // Quita duplicados por slug (mismo producto en varios tonos)
        const vistos = new Map();

        document.querySelectorAll(`#rv-datos-${pedidoId} span`).forEach((s) => {
            vistos.set(s.dataset.slug, s.dataset.nombre);
        });

        let filas = [];

        try {
            filas = await Promise.all([...vistos].map(async ([slug, nombre]) => {
                const r = await fetch(URL_MIA.replace("SLUG", slug), {
                    credentials: "same-origin"
                });
                const d = await r.json();
                return { slug, nombre, resena: d.resena, puede: d.puede_resenar };
            }));
        } catch (err) {
            cuerpo.replaceChildren(
                el("p", "rv-aviso", "No se pudieron cargar tus productos. Intenta de nuevo.")
            );
            return;
        }

        cuerpo.replaceChildren();

        if (!filas.length) {
            cuerpo.append(el("p", "rv-aviso",
                "Este pedido no tiene productos individuales para reseñar."));
            return;
        }

        filas.forEach((f) => {

            const fila = el("div", "rv-fila");
            const info = el("div");

            info.append(el("strong", "", f.nombre));
            info.append(el("small", "", f.resena
                ? `${"★".repeat(f.resena.calificacion)} · ${ESTADOS[f.resena.estado]}`
                : "Sin reseña"));

            fila.append(info);

            if (f.puede) {
                const b = el("button", "rv-btn", f.resena ? "Editar" : "Reseñar");
                b.type = "button";
                b.onclick = () => mostrarForm(pedidoId, f);
                fila.append(b);
            }

            cuerpo.append(fila);
        });
    }

    // ---------- FORMULARIO ----------
    function mostrarForm(pedidoId, f) {

        titulo.textContent = f.nombre;
        cuerpo.replaceChildren();

        const mia = f.resena;
        let nota = mia ? mia.calificacion : 0;

        if (mia) {
            const avisos = {
                pendiente: "Tu reseña está en revisión.",
                aprobada: "Tu reseña está publicada. Puedes editarla cuando quieras.",
                rechazada: "El equipo de Lúmina ocultó tu reseña. Puedes editarla, pero seguirá oculta."
            };
            cuerpo.append(el("p", "rv-aviso", avisos[mia.estado] || ""));
        }

        // Estrellas
        const pick = el("div", "rv-pick");
        const botones = [];
        const pintar = () =>
            botones.forEach((b, i) => b.classList.toggle("on", i < nota));

        for (let i = 1; i <= 5; i++) {
            const b = el("button", "", "★");
            b.type = "button";
            b.setAttribute("aria-label", `${i} estrellas`);
            b.onclick = () => { nota = i; pintar(); };
            botones.push(b);
            pick.append(b);
        }

        pintar();
        cuerpo.append(pick);

        // Título y comentario
        const tit = el("input");
        tit.type = "text";
        tit.maxLength = 120;
        tit.placeholder = "Título (opcional)";
        tit.value = mia ? mia.titulo : "";

        const com = el("textarea");
        com.rows = 4;
        com.maxLength = 2000;
        com.placeholder = "Cuéntanos qué tal te pareció el producto";
        com.value = mia ? mia.comentario : "";

        cuerpo.append(tit, com);

        const msg = el("div", "rv-msg");
        const acc = el("div", "rv-acciones");

        // Enviar
        const enviar = el("button", "rv-btn", mia ? "Actualizar" : "Publicar");
        enviar.type = "button";

        enviar.onclick = async () => {

            if (!nota) {
                msg.textContent = "Elige una calificación.";
                return;
            }

            enviar.disabled = true;

            try {
                const r = await fetch(URL_CREAR.replace("SLUG", f.slug), {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": CSRF
                    },
                    body: JSON.stringify({
                        calificacion: nota,
                        titulo: tit.value,
                        comentario: com.value
                    })
                });

                const resp = await r.json().catch(() => ({}));

                if (r.ok) {
                    cerrar();
                    Swal.fire({
                        icon: "success",
                        text: resp.estado === "aprobada"
                            ? "¡Gracias! Tu reseña ya está publicada."
                            : "Tu reseña se guardó, pero sigue oculta por el equipo de Lúmina.",
                        confirmButtonColor: "#df6d77"
                    });
                } else {
                    msg.textContent = resp.error || "No se pudo guardar la reseña.";
                }
            } catch (err) {
                msg.textContent = "Error de conexión. Intenta de nuevo.";
            }

            enviar.disabled = false;
        };

        acc.append(enviar);

        // Eliminar (solo si ya existe una reseña)
        if (mia) {
            const borrar = el("button", "rv-btn sec", "Eliminar");
            borrar.type = "button";

            borrar.onclick = async () => {

                const conf = await Swal.fire({
                    title: "¿Eliminar tu reseña?",
                    text: "Esta acción no se puede deshacer.",
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#df6d77",
                    cancelButtonColor: "#999",
                    confirmButtonText: "Sí, eliminar",
                    cancelButtonText: "Cancelar"
                });

                if (!conf.isConfirmed) return;

                await fetch(URL_ELIM.replace("/0/", `/${mia.id}/`), {
                    method: "POST",
                    credentials: "same-origin",
                    headers: { "X-CSRFToken": CSRF }
                });

                mostrarLista(pedidoId);
            };

            acc.append(borrar);
        }

        // Volver
        const volver = el("button", "rv-btn sec", "Volver");
        volver.type = "button";
        volver.onclick = () => mostrarLista(pedidoId);
        acc.append(volver);

        cuerpo.append(acc, msg);
    }

    // Botones "Reseñar productos" de cada pedido
    document.querySelectorAll(".rv-abrir").forEach((b) => {
        b.onclick = () => {
            abrir();
            mostrarLista(b.dataset.pedido);
        };
    });

})();