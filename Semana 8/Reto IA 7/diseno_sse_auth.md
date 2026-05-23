# Estrategia de Autenticación para Conexiones SSE (Server-Sent Events)

## Contexto
En la semana 7 implementamos un `ClienteSSEMultiplex` para escuchar eventos del servidor. La limitación del estándar nativo `EventSource` en el browser es que **no permite enviar headers HTTP custom**, como nuestro `Authorization: Bearer <token>`. Para un SSE seguro, debemos pasar el token de otra forma y gestionar su ciclo de expiración sin desconectar agresivamente el flujo.

## Diseño y Mecanismo

### 1. Mecanismo para enviar el token al abrir la conexión SSE
Dado que no podemos usar headers con `EventSource` estándar:
* **Estrategia Elegida**: Enviar el token como un query parameter temporal al crear la instancia de conexión, ej: `new EventSource('/api/sse/events?token=' + TokenManager.getRawToken())`.
* *Alternativa si no queremos query parameters:* Utilizar `fetch` y la API de Streams del navegador en lugar de `EventSource` para tener control absoluto de los headers (incluyendo `Authorization`), pero requiere una reestructuración profunda de nuestro multiplexor. Optaremos por el query parameter con un token de acceso especial de vida muy corta (un ticket) o usando el `access_token` actual si el endpoint lo permite.

### 2. Flujo de reconexión y expiración de token (Diagrama Lógico)

```text
[ ClienteSSEMultiplex ]
       |
       | 1. TokenManager provee _accessToken actual.
       |    Conexión iniciada a /api/sse/events?token=eyJ...
       v
[ SSE CONECTADO ]
       |
       | 2. Pasan los minutos. TokenManager lanza su "Timer Proactivo".
       | 3. TokenManager renueva su token en el background a través del
       |    endpoint /api/auth/refresh sin interrumpir la conexión actual.
       v
[ SSE SIGUE ACTIVO (El Servidor debe validar expiración) ]
       |
       | 4. Ocurre una de dos cosas:
       |    A) El servidor SSE internamente tiene un hook que cierra la
       |       conexión cuando el JWT expira mandando un evento de error.
       |    B) El servidor soporta la conexión continua y confía que si el cliente
       |       está conectado legítimamente al principio, la conexión vive.
       |
       v
[ SI LA CONEXIÓN SE CORTA (Ej: 401 por SSE Event o Close) ]
       |
       | 5. EventSource dispara el callback "onerror".
       | 6. El Multiplex intercepta el cierre.
       | 7. Preguntamos al TokenManager: "Dame el header actual".
       |    (Si no es válido, el interceptor disparará un refresh y esperaremos).
       | 8. Instanciamos: new EventSource('/api/sse/events?token=' + nuevoToken).
       | 9. Restauramos la suscripción para el usuario silenciosamente.
```

### Reglas para el Reconectado Autenticado
- El `ClienteSSEMultiplex` debe subscribirse de alguna forma a un evento o saber que si falla, debe consultar a `TokenManager`.
- Cuando ocurra un evento de error, antes de iniciar la reconexión de su lado, validará con `TokenManager._isExpiringSoon()`. Si retorna verdadero, esperará explícitamente el resultado de `TokenManager.refreshAccessToken()` antes de intentar levantar el nuevo objeto `EventSource`.
- De esta manera evitamos que un bucle de reconexión intente repetidas veces re-conectarse con un `access_token` ya expirado, lo cual quemaría los reintentos y saturaría el backend.
