console.log("emprender.js v11 cargado — si no ves este mensaje, el navegador está usando una versión vieja en caché");

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    for (let cookie of document.cookie.split(";")) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : getCookie("csrftoken");
}

// Redondea al múltiplo más cercano (por defecto 100) para que las cifras
// se vean "bonitas" en vez de números como 14.976.
function redondearCOP(valor, paso = 100) {
  if (!valor) return 0;
  return Math.round(valor / paso) * paso;
}

function formatoCOP(valor) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(redondearCOP(valor));
}

function textoSugerenciaSobrante(sugerencia) {
  if (!sugerencia || !sugerencia.monto || sugerencia.monto <= 0) return "";

  if (sugerencia.producto_sugerido) {
    return (
      ` Con los ${formatoCOP(sugerencia.monto)} que sobran, podrías sumar ` +
      `1x ${sugerencia.producto_sugerido.nombre} (${formatoCOP(sugerencia.producto_sugerido.costo)}) ` +
      `y dejar toda tu inversión en mercancía, o guardarlos para cubrir el envío.`
    );
  }

  return (
    ` Los ${formatoCOP(sugerencia.monto)} que sobran no alcanzan para sumar otro ` +
    `producto de esta selección, así que puedes destinarlos a cubrir el envío.`
  );
}

// --------------------------------------------------
// PRESUPUESTO: input numérico libre con formato de
// miles (es-CO) + chips de montos sugeridos, en vez
// del select con 5 valores fijos.
// --------------------------------------------------

function soloDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

function formatearMiles(digitos) {
  if (!digitos) return "";
  return new Intl.NumberFormat("es-CO").format(Number(digitos));
}

function obtenerPresupuestoNumerico() {
  const input = document.getElementById("presupuesto");
  return input ? soloDigitos(input.value) : "";
}

function inicializarInputPresupuesto() {
  const input = document.getElementById("presupuesto");
  if (!input) return;

  input.addEventListener("input", () => {
    const posicionOriginal = input.selectionStart;
    const largoAntes = input.value.length;

    const digitos = soloDigitos(input.value);
    input.value = formatearMiles(digitos);

    // Mantener el cursor cerca de donde estaba pese a que el
    // formateo cambia el largo del texto (puntos de miles).
    const largoDespues = input.value.length;
    const diferencia = largoDespues - largoAntes;
    const nuevaPosicion = Math.max(0, (posicionOriginal || 0) + diferencia);
    input.setSelectionRange(nuevaPosicion, nuevaPosicion);

    const testError = document.getElementById("testError");
    if (testError) testError.textContent = "";
  });

  document.querySelectorAll(".lm-chip-monto").forEach((btn) => {
    btn.addEventListener("click", () => {
      input.value = formatearMiles(btn.dataset.monto);
      const testError = document.getElementById("testError");
      if (testError) testError.textContent = "";
      input.focus();
    });
  });
}

let graficoGanancias = null;

// Se guardan el último resultado y los filtros usados para poder
// descargarlo en PDF o guardarlo en la cuenta sin volver a pedirlos.
let ultimoResultado = null;
let ultimosFiltros = null;

document.addEventListener("DOMContentLoaded", () => {
  const btnTest = document.getElementById("btnTest");
  if (btnTest) btnTest.addEventListener("click", ejecutarTest);

  inicializarInputPresupuesto();

  const resultadoEl = document.getElementById("resultado");
  const testErrorEl = document.getElementById("testError");
  if (resultadoEl) resultadoEl.setAttribute("aria-live", "polite");
  if (testErrorEl) testErrorEl.setAttribute("aria-live", "polite");

  const btnImprimir = document.getElementById("btnImprimirPdf");
  if (btnImprimir) btnImprimir.addEventListener("click", () => window.print());

  const btnGuardar = document.getElementById("btnGuardarReporte");
  if (btnGuardar) btnGuardar.addEventListener("click", guardarReporte);
});

async function ejecutarTest() {
  const presupuesto = obtenerPresupuestoNumerico();
  const producto = document.getElementById("producto").value;
  const ventas = document.getElementById("ventas").value;
  const testError = document.getElementById("testError");
  const resultado = document.getElementById("resultado");

  testError.textContent = "";

  if (!presupuesto || Number(presupuesto) <= 0) {
    testError.textContent = "Ingresa un presupuesto válido para ver tu recomendación.";
    return;
  }

  if (!producto || !ventas) {
    testError.textContent = "Responde las 3 preguntas para ver tu recomendación.";
    return;
  }

  const btnTest = document.getElementById("btnTest");
  const textoOriginal = btnTest.textContent;
  btnTest.disabled = true;
  btnTest.textContent = "Buscando...";

  try {
    const response = await fetch("/api/recomendar-emprendimiento/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCsrfToken(),
      },
      body: new URLSearchParams({ presupuesto, producto, plataforma: ventas }),
    });

    const data = await response.json();

    if (!response.ok || !data.encontrada) {
      resultado.hidden = true;
      testError.textContent =
        data.mensaje ||
        "No encontramos una recomendación para esa combinación. Intenta con otros valores.";
      return;
    }

    ultimoResultado = data;
    ultimosFiltros = { presupuesto, producto, plataforma: ventas };

    pintarResultado(data);
    resultado.hidden = false;
    resultado.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    testError.textContent = "Ocurrió un error al buscar tu recomendación. Intenta de nuevo.";
  } finally {
    btnTest.disabled = false;
    btnTest.textContent = textoOriginal;
  }
}

async function guardarReporte() {
  const btnGuardar = document.getElementById("btnGuardarReporte");
  const msgEl = document.getElementById("guardarReporteMsg");

  if (!ultimoResultado || !ultimosFiltros) return;

  const textoOriginal = btnGuardar.textContent;
  btnGuardar.disabled = true;
  btnGuardar.textContent = "Guardando...";
  msgEl.textContent = "";

  try {
    const response = await fetch(window.LUMINA_URL_GUARDAR_REPORTE, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        data: ultimoResultado,
        presupuesto: ultimosFiltros.presupuesto,
        producto: ultimosFiltros.producto,
        plataforma: ultimosFiltros.plataforma,
      }),
    });

    const resultado = await response.json();

    if (!response.ok || !resultado.ok) {
      msgEl.textContent = resultado.mensaje || "No se pudo guardar el reporte. Intenta de nuevo.";
      return;
    }

    msgEl.textContent = "✅ Reporte guardado. Puedes verlo en tu cuenta, sección 'Mis reportes de emprendimiento'.";
  } catch (err) {
    msgEl.textContent = "Ocurrió un error al guardar el reporte. Intenta de nuevo.";
  } finally {
    btnGuardar.disabled = false;
    btnGuardar.textContent = textoOriginal;
  }
}

function pintarResultado(data) {
  document.getElementById("resultadoNombre").textContent = data.nombre;
  document.getElementById("resultadoProducto").textContent = data.producto_interes_display;
  document.getElementById("resultadoPresupuesto").textContent = formatoCOP(
    data.inversion_estimada
  );
  document.getElementById("resultadoNivel").textContent = data.nivel;
  document.getElementById("resultadoPlataforma").textContent = data.plataforma_display;
  document.getElementById("resultadoGanancia").textContent = formatoCOP(
    data.ganancia_estimada
  );
  document.getElementById("resultadoRoi").textContent = `${data.roi}%`;
  document.getElementById("resultadoTexto").textContent = data.recomendacion || "";

  const tieneListaCompra = data.lista_compra && data.lista_compra.length > 0;

  // Pintamos la lista de compra ANTES de armar el texto de explicación,
  // para poder reutilizar los mismos totales ya redondeados (costo/venta
  // por unidad) y que el texto siempre cuadre con lo que ve el usuario
  // abajo, sin desfases de unos pesos por redondeos distintos.
  const totalesCompra = pintarListaCompra(
    data.lista_compra,
    data.presupuesto_sobrante,
    data.presupuesto_sobrante_sugerencia
  );

  const explicacionEl = document.getElementById("resultadoExplicacion");
  if (explicacionEl) {
    let texto;

    if (tieneListaCompra) {
      const gananciaCompra = totalesCompra.totalVenta - totalesCompra.totalCosto;

      texto =
        `Con ${formatoCOP(totalesCompra.totalCosto)} compras exactamente los productos ` +
        `que ves abajo. Si los vendes todos al precio sugerido, recibirías ` +
        `${formatoCOP(totalesCompra.totalVenta)}, lo que te deja ` +
        `${formatoCOP(gananciaCompra)} de ganancia.`;

      if (data.presupuesto_sobrante && data.presupuesto_sobrante > 0) {
        texto += ` Te quedan ${formatoCOP(data.presupuesto_sobrante)} sin usar (no alcanza para otra unidad de estos productos).`;
      }
    } else {
      const venta = data.inversion_estimada + data.ganancia_estimada;
      texto =
        `Con ${formatoCOP(data.inversion_estimada)} compras productos, y si los vendes todos, ` +
        `recibirías cerca de ${formatoCOP(venta)}. Es decir: recuperas lo que invertiste y te ` +
        `queda ${formatoCOP(data.ganancia_estimada)} de ganancia. Esta cifra es un promedio ` +
        `típico de este rango de inversión, no de productos específicos.`;
    }

    if (data.kits_estimados) {
      texto += ` Si prefieres kits, con este presupuesto alcanzas cerca de ${data.kits_estimados} kit${data.kits_estimados === 1 ? "" : "s"} completo${data.kits_estimados === 1 ? "" : "s"} (estimado).`;
      texto += textoSugerenciaSobrante(data.kits_sobrante_sugerencia);
    }

    if (data.formula_precio_venta && data.margen_porcentaje != null) {
      const margenDecimal = data.margen_porcentaje / 100;
      const ejemploCosto = 10000;
      const ejemploVenta = margenDecimal < 1 ? ejemploCosto / (1 - margenDecimal) : ejemploCosto;
      texto +=
        ` Así se calcula el precio de venta sugerido: ${data.formula_precio_venta}. ` +
        `En tu tramo el margen sugerido es del ${data.margen_porcentaje}%: ` +
        `por ejemplo, un producto que te cuesta comprarle a Lúmina ${formatoCOP(ejemploCosto)} se vendería en ${formatoCOP(ejemploVenta)}.`;
    }

    texto +=
      ` Ten en cuenta que esto no incluye gastos como envío.`;

    explicacionEl.textContent = texto;
  }

  const nombreEl = document.getElementById("resultadoNombre");
  if (data.generica && nombreEl) {
    nombreEl.textContent = `${data.nombre} (estimación general para tu presupuesto)`;
  }

  pintarListaProductos(data.productos);
  pintarListaKits(data.kits);

  actualizarDashboard(data);

  const btnGuardar = document.getElementById("btnGuardarReporte");
  const msgEl = document.getElementById("guardarReporteMsg");
  if (btnGuardar) {
    btnGuardar.hidden = !window.LUMINA_USER_AUTENTICADO;
  }
  if (msgEl) msgEl.textContent = "";
}

function pintarListaCompra(lineas, sobrante, sugerencia) {
  const contenedor = document.getElementById("resultadoListaCompra");
  const lista = document.getElementById("listaCompraItems");
  const sobranteEl = document.getElementById("resultadoSobrante");

  if (!contenedor || !lista) return { totalCosto: 0, totalVenta: 0 };

  lista.innerHTML = "";

  if (!lineas || !lineas.length) {
    contenedor.hidden = true;
    return { totalCosto: 0, totalVenta: 0 };
  }

  let totalCosto = 0;
  let totalVenta = 0;

  lineas.forEach((item) => {
    // Redondeamos el costo y el precio de venta POR UNIDAD a un múltiplo
    // de 100 (igual que el resto de las cifras) para que el margen que se
    // muestra siga siendo fiel al margen real. Con pasos más grandes (500,
    // 1000) el redondeo puede desviar el margen mostrado varios puntos
    // respecto al margen sugerido real. El subtotal se calcula
    // multiplicando estos mismos valores ya redondeados, para que el
    // unitario y el subtotal siempre cuadren entre sí.
    const costoUnitario = redondearCOP(item.costo_unitario, 100);
    const ventaUnitario = redondearCOP(item.precio_venta_unitario, 100);
    const subtotalCosto = costoUnitario * item.cantidad;
    const subtotalVenta = ventaUnitario * item.cantidad;

    totalCosto += subtotalCosto;
    totalVenta += subtotalVenta;

    const row = document.createElement("div");
    row.className = "lm-result-item";
    row.innerHTML = `
      <span class="lm-result-item-nombre">${item.cantidad}x ${item.nombre}</span>
      <span class="lm-result-item-precio">
        ${formatoCOP(subtotalCosto)} → ${formatoCOP(subtotalVenta)}
        <small style="display:block;opacity:.7;">
          Margen sugerido: ${item.margen_porcentaje}% · te cuesta ${formatoCOP(costoUnitario)} → vendés a ${formatoCOP(ventaUnitario)}
        </small>
      </span>
    `;
    lista.appendChild(row);
  });

  if (sobranteEl) {
    let textoSobrante =
      sobrante && sobrante > 0
        ? `Sobran ${formatoCOP(sobrante)} sin invertir en esta combinación.`
        : "Usas prácticamente todo tu presupuesto en estos productos.";
    textoSobrante += textoSugerenciaSobrante(sugerencia);
    sobranteEl.textContent = textoSobrante;
  }

  contenedor.hidden = false;

  return { totalCosto, totalVenta };
}

function pintarLista(contenedorId, listaId, items) {
  const contenedor = document.getElementById(contenedorId);
  const lista = document.getElementById(listaId);
  lista.innerHTML = "";

  if (!items || !items.length) {
    contenedor.hidden = true;
    return;
  }

  items.forEach((item) => {
    const link = document.createElement("a");
    link.href = item.url;
    link.className = "lm-result-item";
    link.innerHTML = `
      <span class="lm-result-item-nombre">${item.nombre}</span>
      <span class="lm-result-item-precio">${formatoCOP(item.precio)}</span>
    `;
    lista.appendChild(link);
  });

  contenedor.hidden = false;
}

function pintarListaKits(items) {
  const contenedor = document.getElementById("resultadoKits");
  const lista = document.getElementById("listaKits");
  lista.innerHTML = "";

  if (!items || !items.length) {
    contenedor.hidden = true;
    return;
  }

  items.forEach((item) => {
    const wrap = document.createElement("div");
    wrap.className = "lm-result-item";

    const comp = item.composicion;
    const reventa = item.reventa_individual;

    let detalleComposicion = "";
    if (comp) {
      const listaProductos = comp.productos
        .map((p) => `${p.cantidad}x ${p.nombre}`)
        .join(", ");
      detalleComposicion = `
        <small style="display:block;opacity:.7;">
          Trae ${comp.num_productos_distintos} producto${comp.num_productos_distintos === 1 ? "" : "s"}
          (${comp.unidades_totales} unidad${comp.unidades_totales === 1 ? "" : "es"} en total): ${listaProductos}.
          Ahorras ${comp.ahorro_porcentaje}% (${formatoCOP(comp.ahorro)}) vs. comprarlos sueltos al precio de catálogo.
        </small>
      `;
    }

    let detalleReventa = "";
    if (reventa) {
      detalleReventa = `
        <small style="display:block;opacity:.7;margin-top:2px;">
          Si prefieres venderlos por separado con el margen sugerido, en total sumarían
          ${formatoCOP(reventa.total_venta)} (el kit te cuesta ${formatoCOP(item.precio)}).
        </small>
      `;
    }

    wrap.innerHTML = `
      <a href="${item.url}" class="lm-result-item-nombre">${item.nombre}</a>
      <span class="lm-result-item-precio">${formatoCOP(item.precio)}</span>
      ${detalleComposicion}
      ${detalleReventa}
    `;
    lista.appendChild(wrap);
  });

  contenedor.hidden = false;
}

function actualizarDashboard(data) {
  document.getElementById("invTotal").textContent = formatoCOP(data.inversion_estimada);
  document.getElementById("gananciaTotal").textContent = formatoCOP(data.ganancia_estimada);
  document.getElementById("roi").textContent = `${data.roi}%`;

  const ctx = document.getElementById("graficoGanancias");
  if (!ctx) return;

  const meses = ["Mes 1", "Mes 2", "Mes 3", "Mes 4", "Mes 5", "Mes 6"];
  const inversion = data.inversion_estimada;
  const gananciaMensual = data.ganancia_estimada;
  const proyeccion = meses.map((_, i) => redondearCOP(inversion + gananciaMensual * (i + 1)));

  if (graficoGanancias) {
    graficoGanancias.data.labels = meses;
    graficoGanancias.data.datasets[0].data = proyeccion;
    graficoGanancias.update();
    return;
  }

  graficoGanancias = new Chart(ctx, {
    type: "line",
    data: {
      labels: meses,
      datasets: [
        {
          label: "Proyección de ganancias acumuladas",
          data: proyeccion,
          borderColor: "#df6d86",
          backgroundColor: "rgba(223, 109, 134, 0.15)",
          fill: true,
          tension: 0.35,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { callback: (v) => formatoCOP(v) } },
      },
    },
  });
}

function pintarListaProductos(items) {
  const contenedor = document.getElementById("resultadoProductos");
  const lista = document.getElementById("listaProductos");
  lista.innerHTML = "";

  if (!items || !items.length) {
    contenedor.hidden = true;
    return;
  }

  items.forEach((item) => {
    const link = document.createElement("a");
    link.href = item.url;
    link.className = "lm-result-item";

    const detalleCosto =
      item.costo != null
        ? ` · Te cuesta: ${formatoCOP(item.costo)} · Margen sugerido: ${item.margen_porcentaje}%`
        : "";

    link.innerHTML = `
      <span class="lm-result-item-nombre">${item.nombre}</span>
      <span class="lm-result-item-precio">
        Reventa sugerida: ${formatoCOP(item.precio_sugerido)}
        <small style="display:block;opacity:.7;">Precio de catálogo: ${formatoCOP(item.precio_catalogo)}${detalleCosto}</small>
      </span>
    `;
    lista.appendChild(link);
  });

  contenedor.hidden = false;
}