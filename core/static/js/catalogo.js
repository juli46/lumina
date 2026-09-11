
document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =========================================
           ELEMENTOS
        ========================================= */

        const buscador =
            document.getElementById(
                "buscarCatalogo"
            );

        const limpiarBusqueda =
            document.getElementById(
                "limpiarBusqueda"
            );

        const filtroTipo =
            document.getElementById(
                "filtroTipo"
            );

        const filtroCategoria =
            document.getElementById(
                "filtroCategoria"
            );

        const filtroMarca =
            document.getElementById(
                "filtroMarca"
            );

        const filtroColeccion =
            document.getElementById(
                "filtroColeccion"
            );

        const ordenCatalogo =
            document.getElementById(
                "ordenCatalogo"
            );

        const limpiarFiltros =
            document.getElementById(
                "limpiarFiltros"
            );

        const btnLimpiarSinResultados =
            document.getElementById(
                "btnLimpiarSinResultados"
            );

        const productosContainer =
            document.getElementById(
                "catalogoProductos"
            );

        const sinResultados =
            document.getElementById(
                "sinResultadosCatalogo"
            );

        const cantidadProductos =
            document.getElementById(
                "cantidadProductos"
            );

        const filtrosActivos =
            document.getElementById(
                "filtrosActivos"
            );

        const etiquetaToggle =
            document.getElementById(
                "filtroEtiquetaToggle"
            );

        const etiquetaTexto =
            document.getElementById(
                "filtroEtiquetaTexto"
            );

        const etiquetasPanel =
            document.getElementById(
                "etiquetasPanel"
            );

        const paginacion =
            document.getElementById(
                "catalogoPaginacion"
            );


        if (!productosContainer) {
            return;
        }


        /* =========================================
           PRODUCTOS
        ========================================= */

        const productos =
            Array.from(
                productosContainer.querySelectorAll(
                    ".producto-card"
                )
            );


        let etiquetasSeleccionadas =
            new Set();


        /* =========================================
           PAGINACIÓN
        ========================================= */

        const PRODUCTOS_POR_PAGINA = 12;

        let paginaActual = 1;


        /* =========================================
           CONSTRUIR FILTRO DE ETIQUETAS
        ========================================= */

        function construirFiltroEtiquetas() {

            if (!etiquetasPanel) {
                return;
            }


            const todas =
                new Set();


            productos.forEach(
                function (producto) {

                    const lista =
                        (
                            producto.dataset.etiquetas ||
                            ""
                        )
                            .trim()
                            .split(/\s+/)
                            .filter(Boolean);


                    lista.forEach(
                        function (tag) {

                            todas.add(tag);

                        }
                    );

                }
            );


            const ordenadas =
                Array.from(todas).sort();


            etiquetasPanel.innerHTML = "";


            ordenadas.forEach(
                function (tag) {

                    const item =
                        document.createElement(
                            "label"
                        );


                    item.className =
                        "etiqueta-item";


                    item.innerHTML = `
                        <input
                            type="checkbox"
                            value="${tag}"
                        >

                        <span>
                            ${tag}
                        </span>
                    `;


                    const checkbox =
                        item.querySelector(
                            "input"
                        );


                    checkbox.addEventListener(
                        "change",
                        function (e) {

                            if (
                                e.target.checked
                            ) {

                                etiquetasSeleccionadas.add(
                                    tag
                                );

                            } else {

                                etiquetasSeleccionadas.delete(
                                    tag
                                );

                            }


                            actualizarTextoEtiquetas();

                            aplicarCatalogo();

                        }
                    );


                    etiquetasPanel.appendChild(
                        item
                    );

                }
            );

        }


        /* =========================================
           TEXTO DEL BOTÓN DE ETIQUETAS
        ========================================= */

        function actualizarTextoEtiquetas() {

            if (!etiquetaTexto) {
                return;
            }


            const cantidad =
                etiquetasSeleccionadas.size;


            etiquetaTexto.textContent =
                cantidad === 0
                    ? "Todas las etiquetas"
                    : `${cantidad} etiqueta${cantidad > 1 ? "s" : ""} seleccionada${cantidad > 1 ? "s" : ""}`;

        }


        /* =========================================
           ABRIR / CERRAR DROPDOWN
        ========================================= */

        if (
            etiquetaToggle &&
            etiquetasPanel
        ) {

            etiquetaToggle.addEventListener(
                "click",
                function (e) {

                    e.stopPropagation();


                    etiquetasPanel.hidden =
                        !etiquetasPanel.hidden;

                }
            );


            document.addEventListener(
                "click",
                function (e) {

                    if (
                        !etiquetasPanel.hidden &&
                        !etiquetasPanel.contains(
                            e.target
                        ) &&
                        e.target !== etiquetaToggle
                    ) {

                        etiquetasPanel.hidden =
                            true;

                    }

                }
            );

        }


        /* =========================================
           APLICAR FILTROS
        ========================================= */

        function aplicarCatalogo(
            reiniciarPagina = true
        ) {


            const texto =
                buscador
                    ? buscador.value
                        .toLowerCase()
                        .trim()
                    : "";


            const tipo =
                filtroTipo
                    ? filtroTipo.value
                    : "";


            const categoria =
                filtroCategoria
                    ? filtroCategoria.value
                    : "";


            const marca =
                filtroMarca
                    ? filtroMarca.value
                    : "";


            const coleccion =
                filtroColeccion
                    ? filtroColeccion.value
                    : "";


            let visibles = [];


            productos.forEach(
                function (producto) {


                    const nombre =
                        producto.dataset.nombre ||
                        "";


                    const productoTipo =
                        producto.dataset.tipo ||
                        "producto";


                    const productoMarca =
                        producto.dataset.marca ||
                        "";


                    const productoCategoria =
                        producto.dataset.categoria ||
                        "";


                    const productoColeccion =
                        producto.dataset.coleccion ||
                        "";


                    const etiquetas =
                        producto.dataset.etiquetas ||
                        "";


                    /* ==========================
                       BUSCADOR
                    ========================== */

                    const coincideTexto =
                        !texto ||

                        nombre.includes(texto) ||

                        productoMarca.includes(texto) ||

                        productoCategoria.includes(texto) ||

                        productoColeccion.includes(texto) ||

                        etiquetas.includes(texto);


                    /* ==========================
                       TIPO
                    ========================== */

                    const coincideTipo =
                        !tipo ||
                        productoTipo === tipo;


                    /* ==========================
                       CATEGORÍA
                    ========================== */

                    const coincideCategoria =
                        !categoria ||
                        productoCategoria === categoria;


                    /* ==========================
                       MARCA
                    ========================== */

                    const coincideMarca =
                        !marca ||
                        productoMarca === marca;


                    /* ==========================
                       COLECCIÓN
                    ========================== */

                    const coincideColeccion =
                        !coleccion ||
                        productoColeccion === coleccion;


                    /* ==========================
                       ETIQUETAS
                    ========================== */

                    const coincideEtiquetas =
                        etiquetasSeleccionadas.size === 0 ||

                        Array.from(
                            etiquetasSeleccionadas
                        ).some(
                            function (tag) {

                                return etiquetas.includes(
                                    tag
                                );

                            }
                        );


                    /* ==========================
                       RESULTADO FINAL
                    ========================== */

                    const mostrar =
                        coincideTexto &&
                        coincideTipo &&
                        coincideCategoria &&
                        coincideMarca &&
                        coincideColeccion &&
                        coincideEtiquetas;


                    producto.dataset.filtrado =
                        mostrar
                            ? "false"
                            : "true";


                    if (mostrar) {

                        visibles.push(
                            producto
                        );

                    }

                }
            );


            /* =====================================
               ORDENAMIENTO
            ===================================== */

            ordenarProductos();


            /* =====================================
               REINICIAR PÁGINA
            ===================================== */

            if (reiniciarPagina) {

                paginaActual = 1;

            }


            /* =====================================
               CONTADOR
            ===================================== */

            if (cantidadProductos) {

                cantidadProductos.textContent =
                    visibles.length;

            }


            /* =====================================
               SIN RESULTADOS
            ===================================== */

            if (sinResultados) {

                sinResultados.hidden =
                    visibles.length !== 0;

            }


            /* =====================================
               BOTÓN LIMPIAR BÚSQUEDA
            ===================================== */

            if (limpiarBusqueda) {

                limpiarBusqueda.hidden =
                    texto === "";

            }


            /* =====================================
               FILTROS ACTIVOS
            ===================================== */

            mostrarFiltrosActivos();


            /* =====================================
               MOSTRAR PÁGINA
            ===================================== */

            mostrarPagina();

        }


        /* =========================================
           ORDENAR PRODUCTOS
        ========================================= */

        function ordenarProductos() {

            const orden =
                ordenCatalogo
                    ? ordenCatalogo.value
                    : "recientes";


            const ordenados =
                [...productos];


            ordenados.sort(
                function (a, b) {


                    const nombreA =
                        a.dataset.nombre ||
                        "";


                    const nombreB =
                        b.dataset.nombre ||
                        "";


                    const precioA =
                        parseFloat(
                            a.dataset.precio ||
                            0
                        );


                    const precioB =
                        parseFloat(
                            b.dataset.precio ||
                            0
                        );


                    const fechaA =
                        parseInt(
                            a.dataset.fecha ||
                            0
                        );


                    const fechaB =
                        parseInt(
                            b.dataset.fecha ||
                            0
                        );


                    switch (orden) {


                        case "nombre-az":

                            return nombreA.localeCompare(
                                nombreB
                            );


                        case "nombre-za":

                            return nombreB.localeCompare(
                                nombreA
                            );


                        case "precio-menor":

                            return precioA -
                                precioB;


                        case "precio-mayor":

                            return precioB -
                                precioA;


                        case "recientes":

                        default:

                            return fechaB -
                                fechaA;

                    }

                }
            );


            ordenados.forEach(
                function (producto) {

                    productosContainer.appendChild(
                        producto
                    );

                }
            );

        }


        /* =========================================
           MOSTRAR PÁGINA
        ========================================= */

        function mostrarPagina() {


            const visibles =
                productos.filter(
                    function (producto) {

                        return (
                            producto.dataset.filtrado !==
                            "true"
                        );

                    }
                );


            const totalPaginas =
                Math.ceil(
                    visibles.length /
                    PRODUCTOS_POR_PAGINA
                );


            /* ==============================
               SIN RESULTADOS
            ============================== */

            if (
                totalPaginas === 0
            ) {

                paginaActual = 1;


                productos.forEach(
                    function (producto) {

                        producto.hidden =
                            true;

                    }
                );


                construirPaginacion(0);

                return;

            }


            /* ==============================
               EVITAR PÁGINA FUERA DE RANGO
            ============================== */

            if (
                paginaActual >
                totalPaginas
            ) {

                paginaActual =
                    totalPaginas;

            }


            /* ==============================
               POSICIONES
            ============================== */

            const inicio =
                (paginaActual - 1) *
                PRODUCTOS_POR_PAGINA;


            const fin =
                inicio +
                PRODUCTOS_POR_PAGINA;


            /* ==============================
               OCULTAR TODOS
            ============================== */

            productos.forEach(
                function (producto) {

                    producto.hidden =
                        true;

                }
            );


            /* ==============================
               MOSTRAR PÁGINA
            ============================== */

            visibles
                .slice(
                    inicio,
                    fin
                )
                .forEach(
                    function (producto) {

                        producto.hidden =
                            false;

                    }
                );


            /* ==============================
               CONSTRUIR BOTONES
            ============================== */

            construirPaginacion(
                totalPaginas
            );

        }


        /* =========================================
           CONSTRUIR PAGINACIÓN
        ========================================= */

        function construirPaginacion(
            totalPaginas
        ) {

            if (!paginacion) {
                return;
            }


            paginacion.innerHTML = "";


            /*
             * Una sola página:
             * no mostrar botones.
             */

            if (
                totalPaginas <= 1
            ) {

                return;

            }


            /* =====================================
               ANTERIOR
            ===================================== */

            const botonAnterior =
                document.createElement(
                    "button"
                );


            botonAnterior.type =
                "button";


            botonAnterior.className =
                "paginacion-btn";


            botonAnterior.innerHTML =
                '<i class="fa-solid fa-chevron-left"></i>';


            botonAnterior.setAttribute(
                "aria-label",
                "Página anterior"
            );


            botonAnterior.disabled =
                paginaActual === 1;


            botonAnterior.addEventListener(
                "click",
                function () {

                    if (
                        paginaActual > 1
                    ) {

                        paginaActual--;

                        mostrarPagina();

                        desplazarseCatalogo();

                    }

                }
            );


            paginacion.appendChild(
                botonAnterior
            );


            /* =====================================
               NÚMEROS
            ===================================== */

            const paginas =
                obtenerNumerosPaginas(
                    totalPaginas
                );


            paginas.forEach(
                function (pagina) {


                    /*
                     * Puntos suspensivos
                     */

                    if (
                        pagina === "..."
                    ) {

                        const puntos =
                            document.createElement(
                                "span"
                            );


                        puntos.className =
                            "paginacion-ellipsis";


                        puntos.textContent =
                            "...";


                        paginacion.appendChild(
                            puntos
                        );


                        return;

                    }


                    /*
                     * Botón de página
                     */

                    const boton =
                        document.createElement(
                            "button"
                        );


                    boton.type =
                        "button";


                    boton.className =
                        "paginacion-btn";


                    boton.textContent =
                        pagina;


                    if (
                        pagina ===
                        paginaActual
                    ) {

                        boton.classList.add(
                            "activo"
                        );


                        boton.setAttribute(
                            "aria-current",
                            "page"
                        );

                    }


                    boton.addEventListener(
                        "click",
                        function () {

                            paginaActual =
                                pagina;


                            mostrarPagina();

                            desplazarseCatalogo();

                        }
                    );


                    paginacion.appendChild(
                        boton
                    );

                }
            );


            /* =====================================
               SIGUIENTE
            ===================================== */

            const botonSiguiente =
                document.createElement(
                    "button"
                );


            botonSiguiente.type =
                "button";


            botonSiguiente.className =
                "paginacion-btn";


            botonSiguiente.innerHTML =
                '<i class="fa-solid fa-chevron-right"></i>';


            botonSiguiente.setAttribute(
                "aria-label",
                "Página siguiente"
            );


            botonSiguiente.disabled =
                paginaActual ===
                totalPaginas;


            botonSiguiente.addEventListener(
                "click",
                function () {

                    if (
                        paginaActual <
                        totalPaginas
                    ) {

                        paginaActual++;

                        mostrarPagina();

                        desplazarseCatalogo();

                    }

                }
            );


            paginacion.appendChild(
                botonSiguiente
            );

        }


        /* =========================================
           NÚMEROS DE PÁGINA
        ========================================= */

        function obtenerNumerosPaginas(
            totalPaginas
        ) {


            /*
             * Hasta 7 páginas:
             * mostrar todas.
             */

            if (
                totalPaginas <= 7
            ) {

                return Array.from(
                    {
                        length:
                            totalPaginas
                    },
                    function (_, i) {

                        return i + 1;

                    }
                );

            }


            const paginas = [];


            /* Primera */

            paginas.push(1);


            /* Puntos */

            if (
                paginaActual > 4
            ) {

                paginas.push("...");

            }


            /* Cercanas */

            const inicio =
                Math.max(
                    2,
                    paginaActual - 1
                );


            const fin =
                Math.min(
                    totalPaginas - 1,
                    paginaActual + 1
                );


            for (
                let i = inicio;
                i <= fin;
                i++
            ) {

                paginas.push(i);

            }


            /* Puntos */

            if (
                paginaActual <
                totalPaginas - 3
            ) {

                paginas.push("...");

            }


            /* Última */

            paginas.push(
                totalPaginas
            );


            return paginas;

        }


        /* =========================================
           DESPLAZARSE AL CATÁLOGO
        ========================================= */

        function desplazarseCatalogo() {

            if (!productosContainer) {
                return;
            }


            const posicion =
                productosContainer.getBoundingClientRect()
                    .top +
                window.scrollY -
                120;


            window.scrollTo({

                top: posicion,

                behavior: "smooth"

            });

        }


        /* =========================================
           MOSTRAR FILTROS ACTIVOS
        ========================================= */

        function mostrarFiltrosActivos() {


            if (!filtrosActivos) {
                return;
            }


            filtrosActivos.innerHTML = "";


            const filtros = [];


            /* =====================================
               TIPO
            ===================================== */

            if (
                filtroTipo &&
                filtroTipo.value
            ) {

                filtros.push({

                    texto:
                        filtroTipo
                            .options[
                                filtroTipo.selectedIndex
                            ]
                            .text,

                    tipo:
                        "tipoProducto"

                });

            }


            /* =====================================
               CATEGORÍA
            ===================================== */

            if (
                filtroCategoria &&
                filtroCategoria.value
            ) {

                filtros.push({

                    texto:
                        filtroCategoria
                            .options[
                                filtroCategoria.selectedIndex
                            ]
                            .text,

                    tipo:
                        "categoria"

                });

            }


            /* =====================================
               MARCA
            ===================================== */

            if (
                filtroMarca &&
                filtroMarca.value
            ) {

                filtros.push({

                    texto:
                        filtroMarca
                            .options[
                                filtroMarca.selectedIndex
                            ]
                            .text,

                    tipo:
                        "marca"

                });

            }


            /* =====================================
               COLECCIÓN
            ===================================== */

            if (
                filtroColeccion &&
                filtroColeccion.value
            ) {

                filtros.push({

                    texto:
                        filtroColeccion
                            .options[
                                filtroColeccion.selectedIndex
                            ]
                            .text,

                    tipo:
                        "coleccion"

                });

            }


            /* =====================================
               ETIQUETAS
            ===================================== */

            etiquetasSeleccionadas.forEach(
                function (tag) {

                    filtros.push({

                        texto:
                            tag,

                        tipo:
                            "etiqueta"

                    });

                }
            );


            /* =====================================
               CREAR FILTROS
            ===================================== */

            filtros.forEach(
                function (filtro) {


                    const etiqueta =
                        document.createElement(
                            "span"
                        );


                    etiqueta.className =
                        "filtro-activo";


                    etiqueta.innerHTML = `

                        ${filtro.texto}

                        <button
                            type="button"
                            data-filtro="${filtro.tipo}"
                            aria-label="Eliminar filtro"
                        >

                            <i
                                class="fa-solid fa-xmark"
                            ></i>

                        </button>

                    `;


                    etiqueta
                        .querySelector(
                            "button"
                        )
                        .addEventListener(
                            "click",
                            function () {


                                /* ==================
                                   TIPO
                                ================== */

                                if (
                                    filtro.tipo ===
                                    "tipoProducto"
                                ) {

                                    filtroTipo.value =
                                        "";

                                }


                                /* ==================
                                   CATEGORÍA
                                ================== */

                                if (
                                    filtro.tipo ===
                                    "categoria"
                                ) {

                                    filtroCategoria.value =
                                        "";

                                }


                                /* ==================
                                   MARCA
                                ================== */

                                if (
                                    filtro.tipo ===
                                    "marca"
                                ) {

                                    filtroMarca.value =
                                        "";

                                }


                                /* ==================
                                   COLECCIÓN
                                ================== */

                                if (
                                    filtro.tipo ===
                                    "coleccion"
                                ) {

                                    filtroColeccion.value =
                                        "";

                                }


                                /* ==================
                                   ETIQUETA
                                ================== */

                                if (
                                    filtro.tipo ===
                                    "etiqueta"
                                ) {

                                    etiquetasSeleccionadas.delete(
                                        filtro.texto
                                    );


                                    if (
                                        etiquetasPanel
                                    ) {

                                        const checkbox =
                                            Array.from(
                                                etiquetasPanel
                                                    .querySelectorAll(
                                                        "input"
                                                    )
                                            ).find(
                                                function (input) {

                                                    return input.value ===
                                                        filtro.texto;

                                                }
                                            );


                                        if (checkbox) {

                                            checkbox.checked =
                                                false;

                                        }

                                    }


                                    actualizarTextoEtiquetas();

                                }


                                aplicarCatalogo();

                            }
                        );


                    filtrosActivos.appendChild(
                        etiqueta
                    );

                }
            );

        }


        /* =========================================
           LIMPIAR TODO
        ========================================= */

        function limpiarTodo() {


            if (buscador) {

                buscador.value =
                    "";

            }


            if (filtroTipo) {

                filtroTipo.value =
                    "";

            }


            if (filtroCategoria) {

                filtroCategoria.value =
                    "";

            }


            if (filtroMarca) {

                filtroMarca.value =
                    "";

            }


            if (filtroColeccion) {

                filtroColeccion.value =
                    "";

            }


            if (ordenCatalogo) {

                ordenCatalogo.value =
                    "recientes";

            }


            etiquetasSeleccionadas.clear();


            if (etiquetasPanel) {

                etiquetasPanel
                    .querySelectorAll(
                        "input"
                    )
                    .forEach(
                        function (cb) {

                            cb.checked =
                                false;

                        }
                    );

            }


            actualizarTextoEtiquetas();


            paginaActual =
                1;


            aplicarCatalogo();

        }


        /* =========================================
           EVENTOS
        ========================================= */

        if (buscador) {

            buscador.addEventListener(
                "input",
                function () {

                    aplicarCatalogo();

                }
            );

        }


        if (filtroTipo) {

            filtroTipo.addEventListener(
                "change",
                function () {

                    aplicarCatalogo();

                }
            );

        }


        if (filtroCategoria) {

            filtroCategoria.addEventListener(
                "change",
                function () {

                    aplicarCatalogo();

                }
            );

        }


        if (filtroMarca) {

            filtroMarca.addEventListener(
                "change",
                function () {

                    aplicarCatalogo();

                }
            );

        }


        if (filtroColeccion) {

            filtroColeccion.addEventListener(
                "change",
                function () {

                    aplicarCatalogo();

                }
            );

        }


        if (ordenCatalogo) {

            ordenCatalogo.addEventListener(
                "change",
                function () {

                    aplicarCatalogo();

                }
            );

        }


        /* =========================================
           LIMPIAR BÚSQUEDA
        ========================================= */

        if (limpiarBusqueda) {

            limpiarBusqueda.addEventListener(
                "click",
                function () {


                    if (buscador) {

                        buscador.value =
                            "";

                    }


                    paginaActual =
                        1;


                    aplicarCatalogo();


                    if (buscador) {

                        buscador.focus();

                    }

                }
            );

        }


        /* =========================================
           LIMPIAR FILTROS
        ========================================= */

        if (limpiarFiltros) {

            limpiarFiltros.addEventListener(
                "click",
                function () {

                    limpiarTodo();

                }
            );

        }


        /* =========================================
           LIMPIAR SIN RESULTADOS
        ========================================= */

        if (btnLimpiarSinResultados) {

            btnLimpiarSinResultados.addEventListener(
                "click",
                function () {

                    limpiarTodo();

                }
            );

        }


        /* =========================================
           INICIALIZAR
        ========================================= */

        construirFiltroEtiquetas();


        /*
         * Marcar inicialmente todos los productos
         * como disponibles.
         */

        productos.forEach(
            function (producto) {

                producto.dataset.filtrado =
                    "false";

            }
        );


        /* =========================================
           CATEGORÍA RECIBIDA DESDE INICIO
        ========================================= */

        const parametrosURL =
            new URLSearchParams(
                window.location.search
            );


        const categoriaURL =
            parametrosURL.get(
                "categoria"
            );


        if (
            categoriaURL &&
            filtroCategoria
        ) {


            const categoriaNormalizada =
                categoriaURL
                    .toLowerCase()
                    .trim();


            const opcionCategoria =
                Array.from(
                    filtroCategoria.options
                ).find(
                    function (opcion) {

                        return opcion.value
                            .toLowerCase()
                            .trim() ===
                            categoriaNormalizada;

                    }
                );


            if (opcionCategoria) {

                filtroCategoria.value =
                    opcionCategoria.value;

            }

        }


        /* =========================================
           APLICAR FILTROS INICIALES
        ========================================= */

        aplicarCatalogo();

    }

);

