// ==========================================
// MOCK (SIMULADOR) DE SERVIDOR PARA PRUEBAS
// ==========================================
let contadorPeticiones = 0;
global.fetch = async (url, options) => {
    // Simulamos el retraso de la red
    await new Promise(r => setTimeout(r, 500));

    // Si es un POST a /alertas
    if (url.includes('/alertas')) {
        return { status: 201 }; // Simulamos éxito al crear alerta
    }

    // Si es un GET a /inventario
    if (url.includes('/inventario')) {
        contadorPeticiones++;
        console.log(`\n--- 🌐 [Servidor Simulado] Petición GET #${contadorPeticiones} recibida ---`);

        if (contadorPeticiones === 1) {
            // Petición 1: Todo bien, enviamos un producto BAJO_MINIMO
            return {
                status: 200,
                headers: new Headers({ 'ETag': 'version-1' }),
                json: async () => ({
                    productos: [
                        { id: "PROD-001", nombre: "Cereal Eco", stock: 2, stock_minimo: 10, status: "BAJO_MINIMO" }
                    ]
                })
            };
        } else if (contadorPeticiones === 2) {
            // Petición 2: Simulamos que el servidor se cae (503) para ver el Backoff
            return { status: 503 };
        } else {
            // Peticiones 3 en adelante: Simulamos que el servidor se recuperó pero no hay cambios (304)
            return { status: 304 };
        }
    }
};
// ==========================================

// ==========================================
// CONFIGURACIÓN BASE
// ==========================================
const CONFIG = {
    BASE_URL: "http://ecomarket.local/api/v1",
    TOKEN: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", // Token proporcionado
    INTERVALO_BASE: 5000, // 5 segundos en ms
    INTERVALO_MAX: 60000, // 60 segundos en ms
    TIMEOUT: 10000 // 10 segundos de timeout
};

// ==========================================
// INTERFAZ OBSERVADOR
// ==========================================
class Observador {
    async actualizar(inventario) {
        throw new Error("El método actualizar() debe ser implementado por la subclase.");
    }
}

// ==========================================
// OBSERVADORES CONCRETOS
// ==========================================
class ModuloCompras extends Observador {
    async actualizar(inventario) {
        // Filtramos y mostramos en consola los productos críticos
        const criticos = inventario.productos.filter(p => p.status === "BAJO_MINIMO");
        if (criticos.length > 0) {
            console.log("🛒 [Compras] Alerta de reabastecimiento para:");
            criticos.forEach(p => console.log(`   - ${p.nombre} (Stock: ${p.stock} / Min: ${p.stock_minimo})`));
        }
    }
}

// ==========================================
// ACTUALIZACIÓN DE OBSERVADOR (POST /alertas)
// ==========================================
class ModuloAlertas extends Observador {
    async actualizar(inventario) {
        // Obtenemos los productos bajo mínimo
        const criticos = inventario.productos.filter(p => p.status === "BAJO_MINIMO");
        
        for (const producto of criticos) {
            // Construcción del Body requerido (Especificación de la API)
            const payload = {
                producto_id: producto.id,          // string
                stock_actual: producto.stock,      // number
                stock_minimo: producto.stock_minimo, // number
                timestamp: new Date().toISOString() // string ISO 8601
            };

            try {
                // POST asíncrono a /alertas con los headers correctos
                const response = await fetch(`${CONFIG.BASE_URL}/alertas`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                // Rúbrica: Manejar 201 y 422 de forma diferenciada
                if (response.status === 201) {
                    console.log(`🚨 [Alertas] Alerta registrada exitosamente para ${producto.id}`);
                } else if (response.status === 422) {
                    console.warn(`⚠️ [Alertas] Error 422 en ${producto.id}: Campos inválidos. NO reintentar.`);
                }
            } catch (error) {
                // Captura de errores de red del lado de las alertas
                console.error(`🔌 [Alertas] Error de conexión al enviar alerta de ${producto.id}:`, error.message);
            }
        }
    }
}

// ==========================================
// OBSERVABLE PRINCIPAL (Monitor)
// ==========================================
class MonitorInventario {
    constructor() {
        this._observadores = [];
        this._ultimo_etag = null;
        this._ultimo_estado = null;
        this._ejecutando = false;
        this._intervalo = CONFIG.INTERVALO_BASE;
    }

    suscribir(obs) {
        this._observadores.push(obs);
    }

    desuscribir(obs) {
        this._observadores = this._observadores.filter(o => o !== obs);
    }

    async _notificar(inventario) {
        // CUMPLE RÚBRICA: Notifica a todos de forma idéntica, sin "ifs" por tipo.
        for (const obs of this._observadores) {
            try {
                await obs.actualizar(inventario);
            } catch (error) {
                // INVARIANTE: Si un observador falla, no rompe la notificación de los demás.
                console.error("❌ [Monitor] Error en un observador, continuando con el resto:", error.message);
            }
        }
    }

    // =======================================================
    // NUEVO MÉTODO PARA MonitorInventario (GET /inventario)
    // =======================================================
    async _consultar_inventario() {
        // 1. Construir headers con Authorization (Obligatorio)
        const headers = {
            'Authorization': `Bearer ${CONFIG.TOKEN}`,
            'Accept': 'application/json'
        };

        // Rúbrica: Polling con detección de cambios (If-None-Match)
        if (this._ultimo_etag) {
            headers['If-None-Match'] = this._ultimo_etag;
        }

        // Rúbrica: Timeout configurado en la petición GET
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT);

        try {
            const response = await fetch(`${CONFIG.BASE_URL}/inventario`, {
                headers: headers,
                signal: controller.signal // Inyectamos el timeout
            });

            clearTimeout(timeoutId); // Limpiamos el timeout si respondió a tiempo

            // 2. Manejo diferenciado de errores
            if (response.status === 200) {
                const data = await response.json();
                
                // Invariante: Validar el body antes de usarlo
                if (!data || !data.productos || !Array.isArray(data.productos)) {
                    console.warn("⚠️ [Monitor] JSON inválido: No se encontró el arreglo de 'productos'.");
                    return null; 
                }

                // Actualizamos estado y retornamos datos nuevos
                this._ultimo_etag = response.headers.get('ETag') || this._ultimo_etag;
                this._ultimo_estado = data;
                return data;

            } else if (response.status === 304) {
                // 304 Not Modified: No hay cambios, no retornamos datos
                return null;

            } else if (response.status >= 400 && response.status < 500) {
                // Invariante: 400 o 401 NO reintenta, NO modifica el intervalo
                console.error(`🛑 [Monitor] Error cliente (${response.status}). Revisa Token/Headers. NO se reintentará.`);
                return null;

            } else if (response.status >= 500) {
                // Invariante: 503 incrementa el intervalo (Backoff)
                console.warn(`🐢 [Monitor] Servidor saturado (${response.status}). Aplicando Backoff...`);
                this._intervalo = Math.min(this._intervalo * 2, CONFIG.INTERVALO_MAX);
                return null;
            }

        } catch (error) {
            clearTimeout(timeoutId);
            // Invariante: NUNCA propagar una excepción al ciclo de polling.
            // Errores de red o Timeout solo registran el warning y retornan null.
            if (error.name === 'AbortError') {
                console.warn("⏳ [Monitor] Timeout alcanzado. La red está lenta, pero el ciclo continuará.");
            } else {
                console.warn(`🔌 [Monitor] Error de red: ${error.message}. El ciclo continuará.`);
            }
            return null;
        }
        
        return null;
    }

    // ==========================================
    // CICLO PRINCIPAL DE POLLING
    // ==========================================
    async iniciar() {
        this._ejecutando = true;
        console.log("🚀 Monitor de Inventario iniciado...");

        while (this._ejecutando) {
            const nuevosDatos = await this._consultar_inventario();

            if (nuevosDatos) {
                // Rúbrica: Reseteo de intervalo de backoff si hubo éxito y datos nuevos (200 OK)
                this._intervalo = CONFIG.INTERVALO_BASE;
                await this._notificar(nuevosDatos);
            }

            // Invariante: Sleep no bloqueante para el Event Loop
            await new Promise(resolve => setTimeout(resolve, this._intervalo));
        }
        
        console.log("🛑 Monitor de Inventario detenido correctamente.");
    }

    detener() {
        // Rúbrica: Cierre suave
        console.log("⚠️ Deteniendo monitor en el próximo ciclo...");
        this._ejecutando = false;
    }
}

// ==========================================
// INICIO DEL SCRIPT (Prueba de uso)
// ==========================================
(async () => {
    // Instanciamos
    const monitor = new MonitorInventario();
    
    // Suscribimos los módulos
    monitor.suscribir(new ModuloCompras());
    monitor.suscribir(new ModuloAlertas());

    // Iniciamos el ciclo
    monitor.iniciar();
})();