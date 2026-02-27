const BASE_URL = 'http://127.0.0.1:4010';

// ==========================================
// 🪵 1. EL LOGGER (La "Caja Negra" del avión)
// ==========================================
const Logger = {
  levels: { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 },
  currentLevel: 0, // 0 para ver todo en desarrollo

  mask(data) {
    if (!data) return data;
    const sensitive = ['password', 'token', 'email', 'credit_card'];
    const masked = JSON.parse(JSON.stringify(data));
    const recursiveMask = (obj) => {
      for (let key in obj) {
        if (sensitive.includes(key.toLowerCase())) obj[key] = '***';
        else if (typeof obj[key] === 'object') recursiveMask(obj[key]);
      }
    };
    recursiveMask(masked);
    return masked;
  },

  write(level, payload) {
    if (this.levels[level] < this.currentLevel) return;
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level,
      ...payload
    }));
  }
};

// ==========================================
// 🌐 2. EL MOTOR (Request con Logging)
// ==========================================
async function request(endpoint, { method = 'GET', body } = {}) {
  const startTime = performance.now();
  
  const headers = { 
    'Accept': 'application/json',
    'Authorization': 'Bearer token_secreto_ecomarket_2026' 
  };
  if (body) headers['Content-Type'] = 'application/json';

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method,
      headers,
      signal: AbortSignal.timeout(5000),
      body: body ? JSON.stringify(body) : undefined
    });

    const duration = Math.round(performance.now() - startTime);
    const contentType = response.headers.get("content-type");
    
    let data = null;
    let responseSize = 0;

    // Validación de JSON y extracción de tamaño
    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
      responseSize = JSON.stringify(data).length;
    } else {
      const text = await response.text();
      responseSize = text.length;
      if (!response.ok) throw new Error(`Formato no válido: ${text.substring(0, 20)}`);
    }

    // Contexto base para el log
    const logCtx = { method, url: endpoint, status: response.status, duration_ms: duration, size_bytes: responseSize };

    // --- CLASIFICACIÓN PROFESIONAL ---
    if (!response.ok) {
      Logger.write('ERROR', { ...logCtx, message: data?.mensaje || 'Error en API' });
      throw new Error(data?.mensaje || `Error HTTP ${response.status}`);
    }

    if (duration > 2000) {
      Logger.write('WARN', { ...logCtx, message: 'Petición Lenta Detectada' });
    } else {
      Logger.write('INFO', { ...logCtx, message: 'OK' });
      Logger.write('DEBUG', { ...logCtx, payload_enviado: Logger.mask(body) });
    }

    return data;

  } catch (error) {
    const duration = Math.round(performance.now() - startTime);
    Logger.write('ERROR', {
      method,
      url: endpoint,
      duration_ms: duration,
      error: error.name === 'TimeoutError' ? 'Timeout (5s)' : error.message
    });
    throw error;
  }
}

// ==========================================
// 🛒 3. API PÚBLICA (Se mantiene limpia)
// ==========================================

async function listarProductos() {
  try {
    return await request('/productos');
  } catch (error) {
    // Aquí solo manejas la lógica de UI, el log ya se hizo en request()
    console.error("❌ Error de UI: No pudimos mostrar los productos.");
  }
}

async function crearProducto(nuevoProducto) {
  try {
    return await request('/productos', { method: 'POST', body: nuevoProducto });
  } catch (error) {
    console.error("❌ Error de UI: Fallo al crear producto.");
  }
}

// ==========================================
// 🚀 PRUEBA DE FUEGO (Ejecución real)
// ==========================================
(async () => {
    console.error("--- Iniciando pruebas con Logs Estructurados ---\n");

    // 1. Probar petición exitosa
    await listarProductos();

    // 2. Probar creación (con ofuscación de datos)
    await crearProducto({
        nombre: "Café Orgánico",
        precio: 25.50,
        token: "ESTO_NO_DEBE_VERSE", // El logger lo ocultará
        password: "mi_password_123"  // El logger lo ocultará
    });

    // 3. Probar un error (petición a algo que no existe)
    try {
        await request('/endpoint-que-falla');
    } catch (e) {
        // El error ya se logueó dentro de request()
    }
})();