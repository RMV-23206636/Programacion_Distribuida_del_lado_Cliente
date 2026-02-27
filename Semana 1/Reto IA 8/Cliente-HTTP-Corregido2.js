const BASE_URL = 'http://127.0.0.1:4010';

// Función Helper Privada (MEJORADA)
async function request(endpoint, { method = 'GET', body } = {}) {
  const headers = {
    'Accept': 'application/json',
  };

  if (body) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    method,
    headers,
    signal: AbortSignal.timeout(5000),
    body: body ? JSON.stringify(body) : undefined
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);

    // --- 🛡️ MEJORA DEL CASO 3: Validación Estricta ---
    const contentType = response.headers.get("content-type");

    // Si el servidor NO devuelve JSON, lanzamos error inmediatamente.
    // Esto evita que la app intente procesar HTML o texto plano como datos válidos.
    if (!contentType || !contentType.includes("application/json")) {
        // Leemos un poco del texto para saber qué nos mandó el servidor (útil para debug)
        const text = await response.text(); 
        throw new Error(`Formato inesperado (No es JSON). Recibido: ${text.substring(0, 20)}...`);
    }

    // Si llegamos aquí, es seguro parsear
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data?.mensaje || `Error HTTP ${response.status}`);
    }

    return data;

  } catch (error) {
    if (error.name === 'TimeoutError') {
      console.error(`⏱️ La petición a ${endpoint} excedió el tiempo.`);
    }
    throw error; 
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
// (async () => {
//   console.log("🚀 Iniciando pruebas de integración...");

//   // A) LISTAR PRODUCTOS
//   // ----------------------------------------
//   console.log("\n--- TEST 1: Listar todo ---");
//   try {
//     const inventario = await listarProductos();
//     // Aquí podrías actualizar el DOM con 'inventario'
//   } catch (error) {
//     console.error("🔥 Error crítico en UI:", error.message);
//   }

//   // B) CREAR PRODUCTO (Caso Exitoso)
//   // ----------------------------------------
//   console.log("\n--- TEST 2: Crear producto válido ---");
//   try {
//     const nuevo = {
//       nombre: "Café de Grano",
//       precio: 15.50,
//       stock: 50
//     };
//     await crearProducto(nuevo);
//   } catch (error) {
//     console.error("Fallo al crear:", error.message);
//   }

//   // C) CREAR PRODUCTO (Caso Error de Validación 400)
//   // ----------------------------------------
//   console.log("\n--- TEST 3: Crear producto inválido (sin precio) ---");
//   try {
//     const incompleto = { nombre: "Producto Fantasma" };
//     await crearProducto(incompleto);
//   } catch (error) {
//     // Este catch captura tanto errores de red como validaciones del servidor
//     console.log("✅ El sistema detectó el error correctamente:", error.message);
//   }

//   // D) OBTENER PRODUCTO (Sanitización de URL)
//   // ----------------------------------------
//   console.log("\n--- TEST 4: ID con caracteres extraños ---");
//   // Probamos que encodeURIComponent funcione.
//   // El ID "auriculares/negros" no romperá la URL gracias al fix.
//   await obtenerProducto("auriculares/negros");

// })();
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

// ==========================================
//      PRUEBAS DE CAOS (Usando TU lógica)
// ==========================================

(async () => {
  console.log("🛡️ --- INICIANDO TEST DE RESILIENCIA EN TU CLIENTE --- 🛡️");

  // ESCENARIO 1: RED LENTA
  // Tu código tiene timeout de 5000ms. El servidor tarda 5000ms.
  // Es una carrera muy justa. Para probar que tu timeout funciona,
  // pasaremos un config extra (si tu función lo permitiera) o confiamos en que el overhead de red lo haga fallar.
  console.log("\n1️⃣  Probando Latencia (/slow)...");
  try {
    await request('/slow'); 
    console.log("⚠️ Cuidado: La petición pasó (tal vez llegó justo a tiempo).");
  } catch (error) {
    console.log("✅ Tu cliente cortó la conexión correctamente:", error.message);
  }

  // ESCENARIO 2: INTERMITENCIA
  console.log("\n2️⃣  Probando Intermitencia (/flaky)...");
  // Hacemos 3 intentos manuales para ver cómo reacciona tu código
  for (let i = 1; i <= 3; i++) {
    try {
      console.log(`   Intento ${i}:`);
      await request('/flaky');
      console.log("   -> Éxito");
    } catch (error) {
      console.log("   -> Error capturado por tu cliente:", error.message);
    }
  }

  // ESCENARIO 3: FORMATO INESPERADO (HTML)
  // Aquí veremos si tu lógica de `contentType.includes("application/json")` funciona
  console.log("\n3️⃣  Probando HTML Inesperado (/html)...");
  try {
    const respuesta = await request('/html');
    console.log("Resultado:", respuesta); 
    // OJO AQUÍ: Si sale 'null' y no error, significa que tu cliente
    // ignoró el cuerpo pero dio por buena la petición (status 200).
  } catch (error) {
    console.log("✅ Error detectado:", error.message);
  }

  // ESCENARIO 4: CORTE DE CONEXIÓN
  console.log("\n4️⃣  Probando Corte de Conexión (/cut)...");
  try {
    await request('/cut');
  } catch (error) {
    console.log("✅ Tu cliente manejó el corte:", error.message);
  }

})();