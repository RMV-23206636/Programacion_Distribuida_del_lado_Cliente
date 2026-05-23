# Reto IA 1 - Comprende

## Traza Mental del flujo SSE

```text
# TRAZA SSE:
# t=0   → GET /api/alertas + Accept:text/event-stream → servidor responde 200 OK y mantiene la conexión abierta
# t=2s  → Servidor envía evento (id: 10, event: precio-actualizado, data: {"precio": 45.0})
# t=5s  → Servidor envía comentario de keep-alive (: texto), el cliente lo ignora pero mantiene la conexión
# t=8s  → Servidor envía evento (id: 11, event: stock-critico, data: {"stock": 0})
# t=10s → Servidor envía evento (id: 12, event: precio-actualizado, data: {"precio": 43.0})
# t=12s → Interrupción de red (timeout / conexión cerrada inesperadamente)
# t=15s → Cliente espera tiempo de retry (3000ms por defecto) y reconecta
# t=15s → GET /api/alertas + Last-Event-ID: 12 → servidor responde 200 OK y reanuda enviando evento 13
```

## Diferencia entre SSE y Polling

SSE reduce drásticamente las peticiones vacías (y el overhead de CPU/Red) porque invierte la dirección de la comunicación: en lugar de que el cliente pregunte constantemente al servidor (como en el polling, lo que genera un gran número de respuestas 304 o vacías), en SSE el cliente abre una sola conexión y es el servidor el que "empuja" los datos hacia el cliente, únicamente cuando realmente existe un cambio, manteniendo una conexión eficiente.
