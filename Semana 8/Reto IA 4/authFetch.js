/**
 * Interceptor HTTP usando el patrón Decorator.
 * Envuelve el fetch() nativo para adjuntar automáticamente el token
 * y manejar silenciosamente los errores 401 haciendo un refresh y reintentando.
 */
async function authFetch(url, options = {}) {
    // 1. Adjuntar el token actual si la petición es a nuestra API
    // No adjuntar si es una petición de autenticación
    if (!url.includes('/api/auth/')) {
        options.headers = {
            ...options.headers,
            ...TokenManager.getAuthHeader()
        };
    }

    // 2. Hacer la petición original
    let response = await fetch(url, options);

    // 3. Manejo del 401 Reactivo
    if (response.status === 401) {
        // EL CASO DIFÍCIL: Si el mismo endpoint de refresh devuelve 401, no reintentamos
        // de lo contrario entraríamos en un loop infinito.
        if (url.includes('/api/auth/refresh')) {
            console.warn("El refresh_token es inválido o expiró.");
            TokenManager.logout();
            return response; // Devolvemos el 401 para que la capa superior lo maneje
        }

        console.log("Recibido 401 en", url, "-> Iniciando refreshAccessToken()");
        
        try {
            // Intentamos renovar (si ya está renovando, esperará a la cola)
            const refreshSuccess = await TokenManager.refreshAccessToken();
            
            if (refreshSuccess) {
                // Si tuvo éxito, adjuntamos el nuevo token y reintentamos la petición original
                console.log("Refresh exitoso. Reintentando petición original a", url);
                options.headers = {
                    ...options.headers,
                    ...TokenManager.getAuthHeader()
                };
                
                // REINTENTO (exactamente una vez)
                response = await fetch(url, options);
                
                // Si este reintento devuelve 401, significa que algo más pasa,
                // no volvemos a intentar. Llamaríamos a logout en un escenario estricto.
                if (response.status === 401) {
                     TokenManager.logout();
                }
            }
        } catch (err) {
            // Si TokenManager.refreshAccessToken() rechaza (lanza error),
            // el refresh falló.
            console.error("Fallo al renovar el token en interceptor:", err);
            TokenManager.logout();
        }
    }

    return response;
}
