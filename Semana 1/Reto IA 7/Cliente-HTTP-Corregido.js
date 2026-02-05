const BASE_URL = 'http://127.0.0.1:4010';

// Función Helper Privada (Centraliza lógica, timeouts y errores)
async function request(endpoint, { method = 'GET', body } = {}) {
  const headers = {
    'Accept': 'application/json', // Buena práctica
  };

  // Parseo Seguro de JSON (La correción crítica)
  if (body) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    method,
    headers,
    signal: AbortSignal.timeout(5000), // Timeout por defecto para TODOS
    body: body ? JSON.stringify(body) : undefined
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);

    // Manejo seguro de JSON (evita crash si no hay cuerpo)
    let data = null;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        data = await response.json();
    }

    if (!response.ok) {
      // Lanzamos un error personalizado con datos del servidor si existen
      throw new Error(data?.mensaje || `Error HTTP ${response.status}`);
    }

    return data;

  } catch (error) {
    // Aquí decidimos si logueamos o transformamos el error, pero SIEMPRE relanzamos
    if (error.name === 'TimeoutError') {
      console.error(`⏱️ La petición a ${endpoint} excedió el tiempo.`);
    }
    throw error; // CRÍTICO: Propagar el error
  }
}

// --- API Pública (Más limpia) ---

async function listarProductos() {
  try {
    const productos = await request('/productos');
    console.table(productos);
    return productos; // Retornar datos para quien lo use
  } catch (error) {
    console.error("No se pudo cargar el inventario.");
    // Manejo de UI aquí si fuera necesario
  }
}

async function obtenerProducto(id) {
  try {
    // Sanitización de input
    return await request(`/productos/${encodeURIComponent(id)}`);
  } catch (error) {
    console.warn(`Error obteniendo producto ${id}: ${error.message}`);
  }
}

async function crearProducto(nuevoProducto) {
  try {
    const resultado = await request('/productos', {
      method: 'POST',
      body: nuevoProducto
    });
    console.log("✨ Creado:", resultado);
    return resultado;
  } catch (error) {
    console.error("Error creando producto:", error.message);
  }
}

// ==========================================
//          EJEMPLOS DE EJECUCIÓN
// ==========================================
/*
 * NOTA IMPORTANTE:
 * Como ahora nuestras funciones lanzan errores (throw) cuando algo falla,
 * siempre debemos consumirlas usando .then/.catch o dentro de un bloque try/catch.
 */
// --- 1. FLUJO COMPLETO (Async/Await Wrapper) ---
(async () => {
  console.log("🚀 Iniciando pruebas de integración...");

  // A) LISTAR PRODUCTOS
  // ----------------------------------------
  console.log("\n--- TEST 1: Listar todo ---");
  try {
    const inventario = await listarProductos();
    // Aquí podrías actualizar el DOM con 'inventario'
  } catch (error) {
    console.error("🔥 Error crítico en UI:", error.message);
  }

  // B) CREAR PRODUCTO (Caso Exitoso)
  // ----------------------------------------
  console.log("\n--- TEST 2: Crear producto válido ---");
  try {
    const nuevo = {
      nombre: "Café de Grano",
      precio: 15.50,
      stock: 50
    };
    await crearProducto(nuevo);
  } catch (error) {
    console.error("Fallo al crear:", error.message);
  }

  // C) CREAR PRODUCTO (Caso Error de Validación 400)
  // ----------------------------------------
  console.log("\n--- TEST 3: Crear producto inválido (sin precio) ---");
  try {
    const incompleto = { nombre: "Producto Fantasma" };
    await crearProducto(incompleto);
  } catch (error) {
    // Este catch captura tanto errores de red como validaciones del servidor
    console.log("✅ El sistema detectó el error correctamente:", error.message);
  }

  // D) OBTENER PRODUCTO (Sanitización de URL)
  // ----------------------------------------
  console.log("\n--- TEST 4: ID con caracteres extraños ---");
  // Probamos que encodeURIComponent funcione.
  // El ID "auriculares/negros" no romperá la URL gracias al fix.
  await obtenerProducto("auriculares/negros");

})();
// --- 2. USO SIMPLIFICADO (Promesas clásicas) ---

/*
listarProductos()
  .then(data => console.log("Total productos cargados:", data.length))
  .catch(err => console.error("Error fatal:", err));
*/

/*
obtenerProducto(99999) // ID que no existe (404)
  .then(() => console.log("Búsqueda terminada."));
*/