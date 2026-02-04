// Configuración base de la API
const BASE_URL = 'http://127.0.0.1:4010';

/**
 * 1. LISTAR TODOS LOS PRODUCTOS
 * Usa console.table para que la lectura sea súper cómoda.
 */
async function listarProductos() {
  try {
    const respuesta = await fetch(`${BASE_URL}/productos`, {
      signal: AbortSignal.timeout(5000) // Manejo de timeout (5 segundos)
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    const productos = await respuesta.json();
    console.log("--- Inventario de EcoMarket ---");
    console.table(productos); // Imprime los productos en una tabla legible

  } catch (error) {
    if (error.name === 'TimeoutError') {
      console.error("❌ La petición tardó demasiado. Revisa tu conexión.");
    } else {
      console.error("❌ Error de red o servidor no disponible:", error.message);
    }
  }
}

/**
 * 2. OBTENER UN PRODUCTO POR ID
 * Maneja específicamente el error 404.
 */
async function obtenerProducto(id) {
  try {
    const respuesta = await fetch(`${BASE_URL}/productos/${id}`);

    if (respuesta.status === 404) {
      console.warn(`⚠️ El producto con ID ${id} no existe en nuestra base de datos.`);
      return;
    }

    if (!respuesta.ok) {
      throw new Error("Algo salió mal en la búsqueda.");
    }

    const producto = await respuesta.json();
    console.log("✅ Producto encontrado:", producto);

  } catch (error) {
    console.error("❌ Mensaje amigable: No pudimos conectar con la tienda. Intenta más tarde.");
  }
}

/**
 * 3. CREAR UN NUEVO PRODUCTO
 * Envía datos JSON y maneja validaciones (400).
 */
async function crearProducto(nuevoProducto) {
  try {
    const respuesta = await fetch(`${BASE_URL}/productos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json' // Indicamos que enviamos JSON
      },
      body: JSON.stringify(nuevoProducto) // Convertimos el objeto JS a string JSON
    });

    const resultado = await respuesta.json();

    if (respuesta.status === 201) {
      console.log("✨ ¡Éxito! Producto creado:", resultado);
    } else if (respuesta.status === 400) {
      console.error("🚫 Error de validación:", resultado.mensaje || "Datos incorrectos.");
    } else {
      throw new Error("Error inesperado al crear.");
    }

  } catch (error) {
    console.error("❌ Error al intentar conectar con el servidor.");
  }
}

// --- EJEMPLOS DE EJECUCIÓN ---

// listarProductos();


// obtenerProducto(42);

/*
crearProducto({
  nombre: "Manzanas Orgánicas",
  precio: 2.50,
  stock: 100
});
*/

listarProductos();
obtenerProducto(24);