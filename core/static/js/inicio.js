/* =========================================
   INICIALIZAR
========================================= */
/* =========================================
   INICIALIZAR
========================================= */

construirFiltroEtiquetas();

/* =========================================
   CATEGORÍA DESDE LA URL
========================================= */

const parametrosURL = new URLSearchParams(window.location.search);
const categoriaURL = parametrosURL.get("categoria");

if (categoriaURL && filtroCategoria) {

    filtroCategoria.value = categoriaURL.toLowerCase();

}

aplicarCatalogo()