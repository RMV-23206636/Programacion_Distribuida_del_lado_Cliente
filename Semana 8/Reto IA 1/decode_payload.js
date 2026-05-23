/**
 * Decodifica el payload de un JWT sin verificar la firma.
 * 
 * ¿Por qué el cliente puede hacer esto sin verificar la firma?
 * El payload de un JWT está codificado en Base64URL, no está cifrado.
 * Cualquier persona puede leerlo. El cliente lo decodifica para leer
 * claims como "exp" (tiempo de expiración) o "sub" (usuario), lo cual
 * es útil para gestionar la sesión en la UI. La verificación de la firma
 * (para asegurar que el token es auténtico y no fue manipulado) es
 * responsabilidad exclusiva del servidor.
 */
function decodePayload(token) {
    if (!token || typeof token !== 'string') {
        throw new Error("Token no válido");
    }
    
    const parts = token.split('.');
    if (parts.length !== 3) {
        throw new Error("El token no tiene 3 partes");
    }
    
    const payloadB64Url = parts[1];
    
    // Convertir Base64URL a Base64 estándar
    const b64 = payloadB64Url.replace(/-/g, '+').replace(/_/g, '/');
    
    // Añadir padding hasta múltiplo de 4
    const padded = b64 + '='.repeat((4 - b64.length % 4) % 4);
    
    try {
        // atob decodifica Base64, JSON.parse convierte la cadena a objeto
        const payloadStr = atob(padded);
        const claims = JSON.parse(payloadStr);
        return claims;
    } catch (e) {
        throw new Error("Error al decodificar o parsear el payload: " + e.message);
    }
}

// Simulación para mostrar el tiempo restante en minutos
const mockToken = "header.eyJzdWIiOiJ1c2VyXzEiLCJleHAiOjE5MDk5OTk5OTksImlhdCI6MTcxNDAwMH0.firma";
try {
    const claims = decodePayload(mockToken);
    console.log("Claims:", claims);
    
    if (claims.exp) {
        const ahoraUnix = Math.floor(Date.now() / 1000);
        const segundosRestantes = claims.exp - ahoraUnix;
        const minutosRestantes = Math.floor(segundosRestantes / 60);
        console.log(`Tiempo restante hasta expiración: ${minutosRestantes} minutos.`);
    }
} catch (error) {
    console.error(error.message);
}
