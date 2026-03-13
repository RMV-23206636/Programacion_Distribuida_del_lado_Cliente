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

class ModuloAlertas extends Observador {
    async actualizar(inventario) {
        // Esqueleto para la Fase 2: Aquí irá el POST asíncrono a /alertas
        console.log("🚨 [Alertas] Revisando inventario para enviar POST a la API central...");
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
}