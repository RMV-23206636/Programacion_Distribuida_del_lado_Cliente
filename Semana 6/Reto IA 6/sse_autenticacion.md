# Reto IA 6 - Autenticación en SSE

## Pregunta Central
**¿Puede la API nativa EventSource del navegador enviar un header "Authorization: Bearer TOKEN"?**

**NO.** La API nativa `EventSource` del navegador (definida en el estándar HTML del WHATWG) **no admite la configuración de encabezados HTTP personalizados** como `Authorization`. Por diseño, `EventSource` asume una interfaz minimalista destinada principalmente a conexiones donde la autenticación se maneja vía cookies, delegando el manejo subyacente al navegador (como si fuera la carga de una imagen o un iframe), sin exponer control de los headers al desarrollador.

## Alternativas para Contexto B (Navegador)

| Alternativa | Pros | Contras | Recomendado para panel interno? |
|-------------|------|---------|--------------------------------|
| **`withCredentials: true` (Cookies)** | Método oficial y seguro (las cookies httpOnly y SameSite protegen contra XSS/CSRF). El token fluye transparente al navegador. | Requiere que el backend esté adaptado para autenticación por sesión/cookies, no puramente stateless JWT en headers. | **SÍ.** Es la mejor arquitectura y más segura para paneles internos corporativos unificados. |
| **Token en query param (`?token=XYZ`)** | Muy fácil de implementar y funciona nativamente con EventSource. | **Inseguro y mala práctica.** Los tokens se exponen en los logs de acceso del servidor, proxies, en el historial del navegador, y pueden fugarse vía encabezados Referer. | **NO.** Totalmente desaconsejado en entornos reales de producción por fugas de seguridad. |
| **Librería `@microsoft/fetch-event-source`** | Permite enviar el header `Authorization` usando debajo de la mesa el API `fetch()` nativo. Proporciona más control en el ciclo de vida (reconectar manualmente etc.) | Dependencia externa. Rompe ligeramente la semántica pura de "Server-Sent Events" a nivel de herramienta, implementando un lector asíncrono manual de stream. | **Opcional.** Si el backend exige tokens vía header, es la única manera segura de hacerlo desde JS. |
| **Service Worker interceptor** | Transparente para la app principal. Se inyecta el token de forma centralizada en cualquier petición de red (incluido el flujo EventSource original). | Complejidad altísima para una solución simple de autenticación. Demasiada carga cognitiva ("overkill"). | **NO.** Menos viable para proyectos simples o estudiantes debido a su ciclo de vida y dificultades de caché. |

*Recomendación para EcoMarket:* Si es un panel corporativo interno donde podemos controlar la arquitectura completa, usar cookies httpOnly + CSRF (`withCredentials: true`) es la más robusta. Si es un API puramente JWT stateless estricto que solo acepta Authorization Bearer Headers, usar la librería auxiliar `fetch-event-source`.

## Flujo de Renovación de Token (Cliente Python/Node.js)

En un cliente manual (Ruta A), al enviar peticiones vía código como `httpx`, **SÍ** se pueden incluir headers personalizados.

```python
# Pseudocódigo del flujo de renovación de token en cliente Python

async def cliente_sse_con_auth(url, credenciales):
    token = await auth_manager.obtener_token_valido()
    
    while activo:
        headers = {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {token}",
            "Last-Event-ID": last_event_id
        }
        
        try:
            async with httpx.stream('GET', url, headers=headers) as response:
                if response.status_code == 401:
                    # Token expirado o inválido a mitad del stream
                    logging.info("Recibido HTTP 401: Token expirado.")
                    token = await auth_manager.renovar_token()
                    # El bucle while intentará reconectar usando el nuevo token 
                    continue
                
                async for line in response.aiter_lines():
                    # Parsear lineas...
                    pass
        except Exception:
            # Backoff y reintento
            pass
```

## Limitación Fundamental de las Conexiones Persistentes
**¿Qué limitación fundamental hace que la renovación de tokens sea más compleja que en polling?**

En el modelo REST/polling, el estado de la conexión es "efímero" (stateless): con cada petición nueva se valida el token vigente.
En conexiones **persistentes** (SSE / WebSocket), la autenticación y los headers se validan **únicamente durante el handshake inicial (conexión inicial)**. Si el token expira mientras el socket sigue abierto fluyendo datos, los paquetes HTTP intermedios o frames de WebSockets no tienen una manera estandarizada de re-enviar headers. 
Por lo tanto, la aplicación debe implementar mecanismos manuales (como el servidor cerrando la conexión con código 401/403 forzando al cliente a reconectar con un nuevo handshake, o un protocolo propietario donde el cliente envíe el nuevo token dentro de la carga útil (lo cual solo funciona en sockets bidireccionales, no en SSE)) haciendo que un problema trivial de la red se convierta en una complicación arquitectónica y de estado.
