# Reporte de Validación: TokenManager

| Caso de Prueba | Escenario | Resultado Esperado | Resultado Obtenido (TokenManager) | ¿Coincide? |
| -------------- | --------- | ------------------ | --------------------------------- | ---------- |
| 1 | Petición normal (token vigente) | Token adjuntado en `Authorization` header, servidor responde `200 OK`. | Petición se envía y resuelve exitosamente. | ✅ Sí |
| 2 | Petición y token a punto de expirar | Refresh proactivo corre antes de la expiración, `access_token` se actualiza. | Petición original encola, refresh corre, y el nuevo token se usa. | ✅ Sí |
| 3 | Petición con 401 Reactivo | Servidor devuelve 401, el interceptor pausa, hace refresh, reintenta con token nuevo y devuelve 200 OK al caller. | El cliente reintenta con el nuevo JWT y funciona de forma transparente para el componente origen. | ✅ Sí |
| 4 | Refresh devuelve 401 (Refresh token expirado) | Interceptor detecta que `/api/auth/refresh` falló con 401, limpia estado (`logout()`) y no reintenta. | Estado limpio, Promesas rechazadas, logout ejecutado sin loop infinito. | ✅ Sí |
| 5 | Token malformado en payload | La función `_decodePayload` no crashea, en su lugar retorna `null` y fuerza el refresco o logout preventivo. | Se manejó correctamente usando el bloque `try/catch` y la validación de `parts.length !== 3`. | ✅ Sí |
| 6 | 5 peticiones concurrentes devuelven 401 (Singleton) | Solo se dispara 1 POST a `/api/auth/refresh`. Las otras 4 esperan. Las 5 se resuelven o rechazan juntas. | Se ejecutó un solo refresh gracias a la bandera `_isRefreshing` y la `_refreshQueue`. | ✅ Sí |

### Bug Identificado y Corregido
**Descripción del bug:** Inicialmente, si la petición `POST` del `refreshAccessToken` fallaba con `401` y rechazaba las promesas encoladas, dejaba el flag `_isRefreshing = true` debido a que la función retornaba temprano (early return) antes de reestablecerlo.
**Causa raíz:** Falta de bloque `finally` para asegurar la limpieza del estado concurrente sin importar el resultado del refresh.
**Fix aplicado:** Envolví la lógica asíncrona de la petición de refresh dentro de una estructura `try-catch-finally`, forzando el reinicio de `_isRefreshing = false` y limpiando la `_refreshQueue = []` siempre, en la ejecución del bloque `finally`.
