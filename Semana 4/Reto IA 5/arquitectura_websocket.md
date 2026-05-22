# Diseño de la Migración a WebSocket (EcoMarket)

## 1. Contrato del Cliente
Para que los observadores no cambien ni una sola línea, la clase `ServicioWebSocket` debe implementar exactamente los mismos métodos públicos que `ServicioPolling`, extendiendo `Observable`.

**Interfaz común (`MonitorInventario` / `Observable`):**
- `suscribir(evento, callback)`
- `desuscribir(evento, callback)`
- `notificar(evento, datos)`
- `iniciar()`
- `detener()`

Al implementar `ServicioWebSocket`, sobreescribimos `iniciar()` para conectarnos al socket y escuchar mensajes en lugar de un ciclo `while` de polling, y `detener()` para cerrar la conexión.

## 2. Manejo de Conexión en el Cliente
- **Detección de Caída:** WebSocket tiene eventos `onclose` o `onerror`. Cuando se dispara `onclose`, el cliente sabe instantáneamente que la conexión se cerró.
- **Degradación:** En caso de que WebSocket no funcione (ej: fallan reconexiones), el cliente puede hacer un *fallback* iniciando `ServicioPolling`.
- **Notificación a la UI:** Agregamos nuevos eventos: `notificar("modo_degradado")` o `notificar("websocket_desconectado")`. La UI se suscribe a esto para mostrar "Modo offline o degradado".

## 3. Estado Interno del Cliente
El nuevo estado interno que maneja `ServicioWebSocket`:
- **`estado_conexion`**: `CONECTANDO`, `CONECTADO`, `DESCONECTADO`, `RECONECTANDO`.
- **`contador_reconexiones`**: Cuántas veces intentó reconectar antes de aplicar el fallback a polling.
- **`cola_mensajes`**: (Opcional) Si el cliente necesita enviar datos mientras el socket intenta reconectar.
