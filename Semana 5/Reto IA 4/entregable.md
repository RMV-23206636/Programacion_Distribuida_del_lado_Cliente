# Reto 4: Diagnóstico de Escenarios Críticos

## Escenario A: Servidor tarda 45s (Timeout 10s)
1. **Excepción/Código:** Se levanta una excepción `asyncio.TimeoutError`.
2. **Línea/Manejo:** Es capturada por el bloque `except asyncio.TimeoutError` dentro de `_consultar_pedidos()`.
3. **Comportamiento Esperado:** El cliente imprime un *Warning* advirtiendo de la lentitud en la red (o lo registra en logs). Devuelve algo como `"NETWORK_ERROR"`, el ciclo de polling NO se detiene y aplica un backoff aumentando el tiempo de espera para reintentar más tarde.

## Escenario B: Servidor responde HTTP 422
1. **Excepción/Código:** Código HTTP `422 Unprocessable Entity` (Error del cliente / validación).
2. **Línea/Manejo:** Lo atrapa la lógica `elif response.status >= 400:` en `_consultar_pedidos()`.
3. **Comportamiento Esperado:** Se registra el error por haber mandado una petición mal formada. El cliente devuelve `None`. El ciclo de polling continúa, pero **NO reintenta directamente** la petición errónea en un ciclo infinito de fallos rápidos. 

## Escenario C: Servidor responde 200 OK con body `{"pedidos": null}`
1. **Excepción/Código:** Se recibe un código `200 OK`, pero la estructura del JSON es anómala (`pedidos` es `null`).
2. **Línea/Manejo:** El chequeo `if 'pedidos' in data and data['pedidos'] is not None:` dentro de la parte exitosa.
3. **Comportamiento Esperado:** Evitamos intentar iterar sobre `null` (lo cual causaría un `TypeError` fatal en el evento). Se ignora limpiamente la respuesta defectuosa o se retorna `None`. No se notifica a los observadores con datos dañados.

## Escenario D: Servidor responde 503 Service Unavailable
1. **Excepción/Código:** Código HTTP `503`.
2. **Línea/Manejo:** Condicional `elif response.status >= 500:` que identifica errores internos o indisponibilidad del servidor.
3. **Comportamiento Esperado:** El cliente asume que el servidor necesita tiempo. Devuelve `"SERVER_ERROR"`. El ciclo de polling toma esto y entra en **Backoff Adaptativo**, doblando su intervalo de espera. Si alcanza un límite máximo, podría notificar "Servicio no disponible", pero nunca crashear de golpe.

## Escenario E: Servidor responde 304 Not Modified
1. **Excepción/Código:** Código HTTP `304`.
2. **Línea/Manejo:** La línea `elif response.status == 304:` manejada en base a la solicitud enviada con `If-None-Match`.
3. **Comportamiento Esperado:** Retorna un flag como `"NOT_MODIFIED"`. El ciclo de polling no llama a `_notificar()` (no interrumpe a los observadores) e idealmente aplica también backoff para no preguntar tan frecuentemente si los datos son muy estáticos.
