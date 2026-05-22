# Reto 1: Traza mental del ciclo de polling

## Ciclo de Short Polling con ETag

|Tiempo|Cliente|Servidor|Acción del Cliente|Intervalo Actual|
|-|-|-|-|-|
|0s|GET `/api/productos`|200 OK, ETag: `abc123`, Datos: `\\\[...JSON...]`|Guarda `abc123`, notifica datos actualizados|5s (reset)|
|5s|GET `/api/productos` con `If-None-Match: abc123`|304 Not Modified|No hay cambios, no notifica|5s \* 1.5 = 7.5s|
|12.5s|GET `/api/productos` con `If-None-Match: abc123`|304 Not Modified|No hay cambios, no notifica|7.5 \* 1.5 = 11.25s|
|23.75s|GET `/api/productos` con `If-None-Match: abc123`|200 OK, ETag: `def456`, Datos: `\\\[...NUEVO JSON...]`|Alguien actualizó un precio. Guarda `def456`, notifica datos actualizados|5s (reset)|

### ¿Por qué ETag es más eficiente?

ETag es más eficiente que comparar datos completos porque en lugar de que el servidor envíe todo el JSON (cientos de bytes o kilobytes) en cada petición, solo envía el código de estado HTTP 304 (Not Modified) sin cuerpo. Esto ahorra significativamente ancho de banda y tiempo de procesamiento en el cliente y servidor.

