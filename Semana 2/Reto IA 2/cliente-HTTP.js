const BASE_URL = 'http://127.0.0.1:4010';

// ==========================================
// 🪵 1. EL LOGGER (Sin cambios, se mantiene sólido)
// ==========================================
const Logger = {
  levels: { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 },
  currentLevel: 0,
  mask(data) {
    if (!data) return data;
    const sensitive = ['password', 'token', 'email', 'credit_card'];
    const masked = JSON.parse(JSON.stringify(data));
    const recursiveMask = (obj) => {
      for (let key in obj) {
        if (sensitive.includes(key.toLowerCase())) obj[key] = '***';
        else if (typeof obj[key] === 'object' && obj[key] !== null) recursiveMask(obj[key]);
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
// 🛡️ 2. MOTOR DE VALIDACIÓN (Traducción de validaciones2.py)
// ==========================================
const ValidadorEcoMarket = {
  validarProducto(data) {
    const CATEGORIAS_VALIDAS = ["frutas", "verduras", "lacteos", "miel", "conservas"];
    
    try {
      // A. Verificación de campos obligatorios y tipos básicos
      const reglas = {
        id: 'number',
        nombre: 'string',
        precio: 'number',
        categoria: 'string',
        disponible: 'boolean',
        creado_en: 'string',
        productor: 'object'
      };

      // CORRECCIÓN AQUÍ: Se eliminó la palabra 'squig'
      for (let [campo, tipo] of Object.entries(reglas)) {
        if (!(campo in data)) return { valido: false, error: `Falta campo: ${campo}` };
        if (typeof data[campo] !== tipo) return { valido: false, error: `Tipo incorrecto en ${campo}` };
      }

      // B. Reglas de negocio
      if (data.precio <= 0) return { valido: false, error: "Precio debe ser positivo" };
      if (!CATEGORIAS_VALIDAS.includes(data.categoria)) {
        return { valido: false, error: `Categoría no permitida: ${data.categoria}` };
      }

      // C. Validación de objeto anidado (Caso 6: Productor Camaleón)
      const p = data.productor;
      if (p === null || Array.isArray(p)) return { valido: false, error: "Productor debe ser un objeto válido" };
      if (typeof p.id !== 'number' || typeof p.nombre !== 'string') {
        return { valido: false, error: "Estructura de productor inválida (id/nombre)" };
      }

      // D. Validación de fecha ISO 8601
      const fecha = new Date(data.creado_en);
      if (isNaN(fecha.getTime()) || !data.creado_en.includes('T')) {
        return { valido: false, error: "Formato de fecha inválido" };
      }

      return { valido: true };
    } catch (e) {
      return { valido: false, error: `Error interno en validador: ${e.message}` };
    }
  }
};

// ==========================================
// 🌐 3. EL MOTOR (Actualizado con Validación)
// ==========================================
async function request(endpoint, { method = 'GET', body } = {}) {
  const startTime = performance.now();
  const headers = { 
    'Accept': 'application/json',
    'Authorization': 'Bearer token_secreto_ecomarket_2026',
    ...(body && { 'Content-Type': 'application/json' })
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method, headers, body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(5000)
    });

    const duration = Math.round(performance.now() - startTime);
    let data = await response.json().catch(() => null);
    const logCtx = { method, url: endpoint, status: response.status, duration_ms: duration };

    // 1. Error de Red/HTTP
    if (!response.ok) {
      Logger.write('ERROR', { ...logCtx, message: data?.mensaje || 'Error API' });
      throw new Error(`HTTP ${response.status}`);
    }

    // 2. NUEVA CAPA: Validación de Integridad de Datos
    // Solo validamos si es un producto (en este caso, GET o POST de producto)
    if (data && !Array.isArray(data)) { 
      const check = ValidadorEcoMarket.validarProducto(data);
      if (!check.valido) {
        Logger.write('ERROR', { ...logCtx, error_validacion: check.error, data_corrupta: data });
        throw new Error(`Datos corruptos: ${check.error}`);
      }
    }

    Logger.write('INFO', { ...logCtx, message: 'OK' });
    return data;

  } catch (error) {
    Logger.write('ERROR', { method, url: endpoint, error: error.message });
    throw error;
  }
}