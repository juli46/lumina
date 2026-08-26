document.addEventListener("DOMContentLoaded", function () {

    const presupuesto = document.getElementById("presupuesto");
    const producto = document.getElementById("producto");
    const ventas = document.getElementById("ventas");

    const btnTest = document.getElementById("btnTest");
    const testError = document.getElementById("testError");

    const resultado = document.getElementById("resultado");

    const resultadoNombre = document.getElementById("resultadoNombre");
    const resultadoProducto = document.getElementById("resultadoProducto");
    const resultadoPresupuesto = document.getElementById("resultadoPresupuesto");
    const resultadoNivel = document.getElementById("resultadoNivel");
    const resultadoPlataforma = document.getElementById("resultadoPlataforma");
    const resultadoGanancia = document.getElementById("resultadoGanancia");
    const resultadoRoi = document.getElementById("resultadoRoi");
    const resultadoTexto = document.getElementById("resultadoTexto");

    const resultadoProductos = document.getElementById("resultadoProductos");
    const resultadoKits = document.getElementById("resultadoKits");

    const listaProductos = document.getElementById("listaProductos");
    const listaKits = document.getElementById("listaKits");

    const invTotal = document.getElementById("invTotal");
    const gananciaTotal = document.getElementById("gananciaTotal");
    const roi = document.getElementById("roi");

    const canvas = document.getElementById("graficoGanancias");

    let grafico = null;


    // =====================================================
    // RECOMENDACIONES QUE VIENEN DESDE DJANGO
    // =====================================================

    const recomendaciones = window.LUMINA_RECOMENDACIONES || [];


    // =====================================================
    // FORMATEAR DINERO
    // =====================================================

    function formatoPesos(valor) {

        if (valor === null || valor === undefined || valor === "") {
            return "$0";
        }

        return "$" + Number(valor).toLocaleString("es-CO");
    }


    // =====================================================
    // NOMBRES BONITOS
    // =====================================================

    const nombresProductos = {
        gloss: "Gloss",
        skincare: "Skincare",
        pestanas: "Pestañas",
        kits: "Kits beauty"
    };


    const nombresPlataformas = {
        instagram: "Instagram",
        tiktok: "TikTok",
        whatsapp: "WhatsApp"
    };


    // =====================================================
    // NIVEL SEGÚN INVERSIÓN
    // =====================================================

    function obtenerNivel(inversion) {

        inversion = Number(inversion);

        if (inversion <= 100000) {
            return "🌱 Principiante";
        }

        if (inversion <= 300000) {
            return "✨ Emprendedor en crecimiento";
        }

        return "💎 Emprendedor avanzado";
    }


    // =====================================================
    // BUSCAR RECOMENDACIÓN
    // =====================================================

    function buscarRecomendacion() {

        const presupuestoUsuario = Number(presupuesto.value);
        const productoUsuario = producto.value;
        const plataformaUsuario = ventas.value;


        console.log("=================================");
        console.log("BUSCANDO RECOMENDACIÓN");
        console.log("Presupuesto:", presupuestoUsuario);
        console.log("Producto:", productoUsuario);
        console.log("Plataforma:", plataformaUsuario);
        console.log("Recomendaciones:", recomendaciones);
        console.log("=================================");


        if (!recomendaciones.length) {

            console.warn(
                "No existen recomendaciones activas en la base de datos."
            );

            return null;
        }


        // -------------------------------------------------
        // 1. COINCIDENCIA PERFECTA
        // -------------------------------------------------

        let coincidencia = recomendaciones.find(function (rec) {

            const presupuestoCorrecto =
                presupuestoUsuario >= Number(rec.presupuesto_min) &&
                presupuestoUsuario <= Number(rec.presupuesto_max);

            const productoCorrecto =
                !rec.producto_interes ||
                rec.producto_interes === productoUsuario;

            const plataformaCorrecta =
                !rec.plataforma ||
                rec.plataforma === plataformaUsuario;

            return (
                presupuestoCorrecto &&
                productoCorrecto &&
                plataformaCorrecta
            );
        });


        if (coincidencia) {
            return coincidencia;
        }


        // -------------------------------------------------
        // 2. COINCIDENCIA POR PRESUPUESTO + PRODUCTO
        // -------------------------------------------------

        coincidencia = recomendaciones.find(function (rec) {

            const presupuestoCorrecto =
                presupuestoUsuario >= Number(rec.presupuesto_min) &&
                presupuestoUsuario <= Number(rec.presupuesto_max);

            const productoCorrecto =
                !rec.producto_interes ||
                rec.producto_interes === productoUsuario;

            return (
                presupuestoCorrecto &&
                productoCorrecto
            );
        });


        if (coincidencia) {
            return coincidencia;
        }


        // -------------------------------------------------
        // 3. COINCIDENCIA SOLO POR PRESUPUESTO
        // -------------------------------------------------

        coincidencia = recomendaciones.find(function (rec) {

            return (
                presupuestoUsuario >= Number(rec.presupuesto_min) &&
                presupuestoUsuario <= Number(rec.presupuesto_max)
            );
        });


        if (coincidencia) {
            return coincidencia;
        }


        // -------------------------------------------------
        // 4. BUSCAR LA MÁS CERCANA
        // -------------------------------------------------

        let recomendacionCercana = null;
        let diferenciaMenor = Infinity;


        recomendaciones.forEach(function (rec) {

            const minimo = Number(rec.presupuesto_min);
            const maximo = Number(rec.presupuesto_max);

            let diferencia = 0;

            if (presupuestoUsuario < minimo) {
                diferencia = minimo - presupuestoUsuario;
            }

            else if (presupuestoUsuario > maximo) {
                diferencia = presupuestoUsuario - maximo;
            }

            else {
                diferencia = 0;
            }


            if (diferencia < diferenciaMenor) {

                diferenciaMenor = diferencia;
                recomendacionCercana = rec;
            }

        });


        return recomendacionCercana;
    }


    // =====================================================
    // MOSTRAR PRODUCTOS
    // =====================================================

    function mostrarProductos(productos) {

        listaProductos.innerHTML = "";

        if (!productos || !productos.length) {

            resultadoProductos.hidden = true;

            return;
        }


        resultadoProductos.hidden = false;


        productos.forEach(function (producto) {

            const item = document.createElement("div");

            item.className = "lm-result-item";


            item.innerHTML = `
                <span>
                    💄 ${producto.nombre}
                </span>
                ${
                    producto.precio
                    ? `<strong>${formatoPesos(producto.precio)}</strong>`
                    : ""
                }
            `;


            listaProductos.appendChild(item);

        });

    }


    // =====================================================
    // MOSTRAR KITS
    // =====================================================

    function mostrarKits(kits) {

        listaKits.innerHTML = "";

        if (!kits || !kits.length) {

            resultadoKits.hidden = true;

            return;
        }


        resultadoKits.hidden = false;


        kits.forEach(function (kit) {

            const item = document.createElement("div");

            item.className = "lm-result-item";


            item.innerHTML = `
                <span>
                    📦 ${kit.nombre}
                </span>
                ${
                    kit.precio
                    ? `<strong>${formatoPesos(kit.precio)}</strong>`
                    : ""
                }
            `;


            listaKits.appendChild(item);

        });

    }


    // =====================================================
    // ACTUALIZAR GRÁFICO
    // =====================================================

    function actualizarGrafico(inversion, ganancia) {

        if (!canvas) {
            return;
        }


        if (grafico) {
            grafico.destroy();
        }


        grafico = new Chart(canvas, {

            type: "bar",

            data: {

                labels: [
                    "Inversión",
                    "Ganancia"
                ],

                datasets: [
                    {
                        label: "Proyección",
                        data: [
                            inversion,
                            ganancia
                        ]
                    }
                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        ticks: {

                            callback: function (value) {
                                return formatoPesos(value);
                            }

                        }

                    }

                }

            }

        });

    }


    // =====================================================
    // MOSTRAR RESULTADO
    // =====================================================

    function mostrarResultado(rec) {

        if (!rec) {

            resultado.hidden = false;

            resultadoNombre.textContent =
                "No encontramos una recomendación exacta.";

            resultadoProducto.textContent =
                nombresProductos[producto.value] || "Beauty";

            resultadoPresupuesto.textContent =
                formatoPesos(presupuesto.value);

            resultadoNivel.textContent =
                obtenerNivel(presupuesto.value);

            resultadoPlataforma.textContent =
                nombresPlataformas[ventas.value] || "Tu plataforma";

            resultadoGanancia.textContent = "$0";

            resultadoRoi.textContent = "0%";

            resultadoTexto.textContent =
                "Prueba con otro presupuesto o configura más recomendaciones desde el panel administrativo.";

            resultadoProductos.hidden = true;
            resultadoKits.hidden = true;

            invTotal.textContent = "$0";
            gananciaTotal.textContent = "$0";
            roi.textContent = "0%";

            return;
        }


        // =================================================
        // DATOS
        // =================================================

        const inversion = Number(rec.inversion_estimada || 0);

        const ganancia = Number(rec.ganancia_estimada || 0);

        const roiCalculado =
            inversion > 0
                ? ((ganancia / inversion) * 100)
                : 0;


        // =================================================
        // RESULTADO
        // =================================================

        resultado.hidden = false;


        resultadoNombre.textContent =
            rec.nombre || "Recomendación personalizada";


        resultadoProducto.textContent =
            nombresProductos[rec.producto_interes]
            || nombresProductos[producto.value]
            || "Productos beauty";


        resultadoPresupuesto.textContent =
            formatoPesos(inversion);


        resultadoNivel.textContent =
            obtenerNivel(inversion);


        resultadoPlataforma.textContent =
            nombresPlataformas[rec.plataforma]
            || nombresPlataformas[ventas.value]
            || "Redes sociales";


        resultadoGanancia.textContent =
            formatoPesos(ganancia);


        resultadoRoi.textContent =
            roiCalculado.toFixed(2) + "%";


        resultadoTexto.textContent =
            rec.recomendacion ||
            "Con esta inversión puedes comenzar tu emprendimiento beauty y crecer progresivamente.";


        // =================================================
        // PRODUCTOS Y KITS
        // =================================================

        mostrarProductos(rec.productos);

        mostrarKits(rec.kits);


        // =================================================
        // DASHBOARD
        // =================================================

        invTotal.textContent =
            formatoPesos(inversion);


        gananciaTotal.textContent =
            formatoPesos(ganancia);


        roi.textContent =
            roiCalculado.toFixed(2) + "%";


        actualizarGrafico(
            inversion,
            ganancia
        );


        // =================================================
        // SCROLL AL RESULTADO
        // =================================================

        setTimeout(function () {

            resultado.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        }, 100);

    }


    // =====================================================
    // BOTÓN TEST
    // =====================================================

    if (btnTest) {

        btnTest.addEventListener("click", function () {

            testError.textContent = "";


            // ---------------------------------------------
            // VALIDACIÓN
            // ---------------------------------------------

            if (!presupuesto.value) {

                testError.textContent =
                    "💸 Selecciona tu presupuesto.";

                presupuesto.focus();

                return;
            }


            if (!producto.value) {

                testError.textContent =
                    "💄 Selecciona qué quieres vender.";

                producto.focus();

                return;
            }


            if (!ventas.value) {

                testError.textContent =
                    "📱 Selecciona dónde quieres vender.";

                ventas.focus();

                return;
            }


            // ---------------------------------------------
            // BUSCAR
            // ---------------------------------------------

            const recomendacion =
                buscarRecomendacion();


            // ---------------------------------------------
            // MOSTRAR
            // ---------------------------------------------

            mostrarResultado(
                recomendacion
            );

        });

    }

});