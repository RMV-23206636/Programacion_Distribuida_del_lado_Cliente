// TokenManager.js — Módulo singleton para el cliente del panel EcoMarket
// ARQUITECTURA: Sub-ruta B — refresh_token en cookie HttpOnly

const TokenManager = (() => {
  // DECISIÓN: Almacenar _accessToken solo en memoria.
  // ¿Por qué? Limita la ventana de ataque XSS a 15 min y el token no persiste en disco/storage.
  let _accessToken = null;      
  
  // DECISIÓN: Usar un flag _isRefreshing y una cola _refreshQueue para implementar Singleton.
  // ¿Por qué? Evita múltiples peticiones concurrentes de refresh cuando varias llamadas fallan 
  // con 401 al mismo tiempo, evitando un "thundering herd" y posible rotación múltiple inválida.
  let _isRefreshing = false;
  let _refreshQueue = [];       
  const REFRESH_ENDPOINT = "/api/auth/refresh";
  const EXPIRY_MARGIN_SEC = 300; // 5 minutos
  
  // DECISIÓN: Mantener referencia al timer proactivo para poder cancelarlo en el logout.
  let _proactiveTimer = null;

  /**
   * Decodifica el payload de un JWT sin verificar firma.
   * DECISIÓN: Validar las 3 partes y agregar padding.
   * ¿Por qué? Un token malformado o un Base64URL sin padding en atob() lanzará error que podría romper la UI.
   */
  function _decodePayload(token) {
    if (!token || typeof token !== 'string') return null;
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    const raw = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = raw + '='.repeat((4 - raw.length % 4) % 4);
    try {
      return JSON.parse(atob(padded));
    } catch (e) {
      return null;
    }
  }

  /**
   * Comprueba si el token está a punto de expirar.
   * DECISIÓN: Comparar en segundos y no en milisegundos.
   * ¿Por qué? Date.now() retorna ms, pero el claim 'exp' de JWT es segundos Unix.
   */
  function _isExpiringSoon() {
    if (!_accessToken) return true;
    const payload = _decodePayload(_accessToken);
    if (!payload || !payload.exp) return true;
    
    const ahoraSec = Math.floor(Date.now() / 1000);
    return (payload.exp - ahoraSec) < EXPIRY_MARGIN_SEC;
  }

  /**
   * Recibe y almacena el token.
   * DECISIÓN: Configurar temporizador proactivo aquí.
   * ¿Por qué? Así automatizamos el ciclo y evitamos llegar al estado reactivo 401 en lo posible.
   */
  function storeTokens(accessToken) {
    _accessToken = accessToken;
    
    // Configurar timer proactivo (opcional pero recomendado)
    if (_proactiveTimer) clearTimeout(_proactiveTimer);
    const payload = _decodePayload(_accessToken);
    if (payload && payload.exp) {
        const ahoraSec = Math.floor(Date.now() / 1000);
        let tiempoParaRefresh = (payload.exp - ahoraSec - EXPIRY_MARGIN_SEC) * 1000;
        if (tiempoParaRefresh > 0) {
            _proactiveTimer = setTimeout(() => {
                if (_isExpiringSoon()) refreshAccessToken();
            }, tiempoParaRefresh);
        }
    }
  }

  /**
   * Retorna el header de autorización.
   * DECISIÓN: Comprobar si hay token antes de devolver.
   * ¿Por qué? Evitamos enviar "Bearer null" que podría causar errores extraños.
   */
  function getAuthHeader() {
    if (!_accessToken) return {};
    return { "Authorization": "Bearer " + _accessToken };
  }

  /**
   * Refresh singleton con cola de espera.
   * DECISIÓN: Promise compartida para todos los solicitantes cuando _isRefreshing es true.
   * ¿Por qué? Garantiza que solo hagamos una llamada a la red para renovar.
   */
  async function refreshAccessToken() {
    if (_isRefreshing) {
      return new Promise((resolve, reject) => _refreshQueue.push({resolve, reject}));
    }
    
    _isRefreshing = true;
    try {
      const response = await fetch(REFRESH_ENDPOINT, { 
        method: 'POST',
        credentials: 'include' // Envia cookie HttpOnly automáticamente
      });
      
      if (!response.ok) {
        throw new Error("Refresh fallido");
      }
      
      const data = await response.json();
      storeTokens(data.access_token);
      
      // Liberar cola: éxito
      _refreshQueue.forEach(p => p.resolve(_accessToken));
      return true;
    } catch (error) {
      logout();
      // Liberar cola: rechazo
      _refreshQueue.forEach(p => p.reject(error));
      return false;
    } finally {
      _isRefreshing = false;
      _refreshQueue = [];
    }
  }

  /**
   * Limpia todo el estado de autenticación.
   * DECISIÓN: Limpiar timers y variables de estado.
   * ¿Por qué? Prevenir "tokens fantasma" y peticiones residuales al servidor.
   */
  function logout() {
    _accessToken = null;
    if (_proactiveTimer) {
        clearTimeout(_proactiveTimer);
        _proactiveTimer = null;
    }
    // Llamada simulada al backend para destruir la cookie HttpOnly
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(()=>{});
    console.log("Sesión finalizada");
  }

  return { storeTokens, getAuthHeader, refreshAccessToken, logout, _isExpiringSoon };
})();

// Prueba Manual
(async function test() {
    console.log("--- Inicio de prueba manual TokenManager ---");
    const mockToken = "header.eyJzdWIiOiJ1c2VyXzEiLCJleHAiOjE5OTk5OTk5OTksImlhdCI6MTcxNDAwMH0.firma";
    TokenManager.storeTokens(mockToken);
    
    const headers = TokenManager.getAuthHeader();
    console.log("Header de autenticación generado:", headers);
    
    const expiraPronto = TokenManager._isExpiringSoon();
    console.log("¿Expira pronto?", expiraPronto);
    
    // Como el token dura mucho, no expira pronto.
    console.log("Llamando a logout...");
    TokenManager.logout();
    console.log("Header post-logout:", TokenManager.getAuthHeader());
})();
