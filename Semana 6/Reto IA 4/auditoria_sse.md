# Auditoría SSE - Reto IA 4

## 1. Error de Buffer sin limpieza adecuada
**Descripción:** El buffer de acumulación de datos no se resetea por completo o no se inicializa un buffer nuevo al encontrar un doble salto de línea `\n\n`. A veces se acumulan eventos concatenando las líneas de varios eventos separados.
**Cómo falla en producción:** Si llegan eventos seguidos (ej. evento A y evento B), el evento B procesado contendrá los datos del evento B junto con los datos del evento A previo, lo cual romperá la estructura JSON o procesará un evento gigante inválido.
**Invariante violado:** El buffer de líneas debe resetearse completamente después de cada mensaje procesado.
**Evidencia de manifestación:**
```text
2026-05-22 17:05:01 - INFO - Evento Recibido: {"precio": 45.0}{"stock": 0} -> JSONDecodeError
```
**Código Corregido:**
```python
if not line:
    if buffer["data"]:
        self._procesar_evento(buffer)
    # CORECCIÓN: Resetear el buffer completamente
    buffer = {"id": None, "event": "message", "data": ""}
    continue
```

## 2. Bucle infinito de reconexión sin backoff ni límite
**Descripción:** El cliente atrapa un error de red y se reconecta inmediatamente dentro de un `while True:` sin ningún tipo de espera (backoff) o sin un límite máximo de intentos.
**Cómo falla en producción:** Si el servidor se cae, el cliente enviará cientos o miles de peticiones HTTP por segundo en un bucle cerrado consumiendo el 100% de CPU y saturando la red. Cuando el servidor intente levantarse, se encontrará con un ataque DDoS de sus propios clientes.
**Invariante violado:** Reconexión debe tener un máximo de intentos y usar backoff, respetando `retry:`.
**Evidencia de manifestación:**
```text
(En terminal miles de líneas por segundo):
2026-05-22 17:05:01 - INFO - Conectando...
2026-05-22 17:05:01 - WARNING - Error. Reintentando...
2026-05-22 17:05:01 - INFO - Conectando...
```
**Código Corregido:**
```python
intentos = 0
max_intentos = 5
while self.activo and intentos < max_intentos:
    # ... intento de conexión ...
    except Exception:
        intentos += 1
        await asyncio.sleep(self.retry_ms / 1000.0) # CORRECCIÓN: esperar retry_ms
```

## 3. Ausencia de Timeout a nivel de cliente HTTP
**Descripción:** El cliente instancia un `httpx.AsyncClient` sin configurar un parámetro `timeout` explícito, asumiendo que la conexión SSE siempre será rápida o siempre notificará cierres.
**Cómo falla en producción:** Si la red se cae sin enviar un paquete FIN/RST (por ejemplo, el usuario entra en un túnel en el metro), la conexión TCP quedará "colgada" indefinidamente. El cliente pensará que está escuchando, pero no recibirá nada y tampoco reconectará.
**Invariante violado:** Timeout debe estar configurado para evitar conexiones zombies.
**Evidencia de manifestación:**
(Terminal congelada infinitamente sin logs tras simular corte de red con iptables o similar, no se ve "Timeout exception" en logs).
**Código Corregido:**
```python
# CORRECCIÓN: Timeout configurado (ej: 30 segundos sin bytes nuevos)
timeout = httpx.Timeout(30.0)
async with httpx.AsyncClient(timeout=timeout) as client:
```

## 4. Excepciones en el handler rompen la lectura del stream
**Descripción:** Si la lógica que procesa el evento (`_procesar_evento`) falla (por ejemplo, accede a un campo del JSON que no existe) y lanza un `KeyError`, esta excepción se propaga y corta el ciclo `async for line in response.aiter_lines():`.
**Cómo falla en producción:** Un solo mensaje malformado por parte del servidor provocará que el cliente crashee o cierre la conexión TCP de forma forzada, requiriendo un reinicio completo o disparando el ciclo de reconexión de forma innecesaria por un error que era puramente lógico, no de red.
**Invariante violado:** Una excepción al procesar un evento no debe cerrar la conexión.
**Evidencia de manifestación:**
```text
2026-05-22 17:06:12 - ERROR - KeyError: 'producto'
2026-05-22 17:06:12 - INFO - Conexión cerrada. Reconectando...
```
**Código Corregido:**
```python
def _procesar_evento(self, evento: dict):
    try:
        # Lógica de procesamiento
        pass
    except Exception as e:
        # CORRECCIÓN: Solo loguear y evitar que crashee el bucle principal
        logging.error(f"Error procesando evento: {e}")
```
