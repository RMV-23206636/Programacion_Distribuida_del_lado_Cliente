# Reto IA 2

# \---

## Línea Temporal del Event Loop (Redibujada con Palabras Propias)

Código analizado:

```python
import asyncio
import aiohttp

async def obtener\_datos():
    async with aiohttp.ClientSession() as session:
        tarea1 = session.get("http://localhost:3000/api/productos")   # Paso A
        tarea2 = session.get("http://localhost:3000/api/categorias")  # Paso B
        resp1, resp2 = await asyncio.gather(tarea1, tarea2)           # Paso C
        productos  = await resp1.json()                               # Paso D
        categorias = await resp2.json()                               # Paso E
        return productos, categorias

asyncio.run(obtener\_datos())                                          # Paso 0
```

### Línea Temporal Numerada

```
\[Paso 0] asyncio.run(obtener\_datos())
  ▶ El runtime CREA un event loop nuevo.
  ▶ Crea la coroutine obtener\_datos() y la programa como la tarea principal.
  ▶ Inicia el loop: busca tareas listas para ejecutar.

  EJECUTANDO: obtener\_datos  |  ESPERANDO: (ninguna)  |  COMPLETAS: (ninguna)

──────────────────────────────────────────────

\[Paso 1] Entra al bloque  async with aiohttp.ClientSession() as session:
  ▶ Se crea el objeto ClientSession (incluye el TCPConnector con el pool de conexiones).
  ▶ NO hay await aquí → el event loop no cede el control, sigue ejecutando.

  EJECUTANDO: obtener\_datos  |  ESPERANDO: (ninguna)  |  COMPLETAS: (ninguna)

──────────────────────────────────────────────

\[Paso 2] tarea1 = session.get("…/productos")
  ▶ session.get() devuelve un objeto ClientResponse (coroutine/context manager).
  ▶ NO envía la petición todavía. Solo crea el objeto que describe QUÉ petición se hará.
  ▶ La petición se envía cuando se hace await sobre él.

  EJECUTANDO: obtener\_datos  |  ESPERANDO: (ninguna)  |  COMPLETAS: (ninguna)

──────────────────────────────────────────────

\[Paso 3] tarea2 = session.get("…/categorias")
  ▶ Igual que el paso anterior: solo crea el descriptor de la petición, NO la envía.

  EJECUTANDO: obtener\_datos  |  ESPERANDO: (ninguna)  |  COMPLETAS: (ninguna)

──────────────────────────────────────────────

\[Paso 4] await asyncio.gather(tarea1, tarea2)
  ▶ gather() convierte tarea1 y tarea2 en Tasks de asyncio y las registra en el loop.
  ▶ El loop ENVÍA ambas peticiones HTTP al sistema operativo (socket no-bloqueante).
  ▶ Llega el await → obtener\_datos CEDE el control al event loop.
  ▶ El loop pregunta: ¿quién más está listo? Nadie más → espera eventos de I/O.

  EJECUTANDO: (event loop esperando I/O)  |  ESPERANDO: tarea1, tarea2  |  COMPLETAS: (ninguna)

──────────────────────────────────────────────

\[Paso 5] El SO notifica: llegó respuesta de /categorias (digamos, 95 ms)
  ▶ El event loop despierta a tarea2.
  ▶ tarea2 procesa los headers de la respuesta HTTP.
  ▶ tarea2 aún no tiene el body completo → vuelve a esperar I/O (lectura del body).

  EJECUTANDO: tarea2 (headers)  |  ESPERANDO: tarea1  |  COMPLETAS: (ninguna)

──────────────────────────────────────────────

\[Paso 6] El SO notifica: llegó respuesta de /productos (digamos, 120 ms)
  ▶ El event loop despierta a tarea1.
  ▶ tarea1 procesa headers y body.
  ▶ tarea1 COMPLETA → ya tiene el objeto resp1 listo.

  EJECUTANDO: tarea1 (completa)  |  ESPERANDO: tarea2 (body)  |  COMPLETAS: tarea1

──────────────────────────────────────────────

\[Paso 7] tarea2 completa el body de /categorias.
  ▶ Ambas Tasks completas. gather() retorna (resp1, resp2).
  ▶ obtener\_datos REANUDA su ejecución en la línea después del await gather.

  EJECUTANDO: obtener\_datos  |  ESPERANDO: (ninguna)  |  COMPLETAS: tarea1, tarea2

──────────────────────────────────────────────

\[Paso 8] productos = await resp1.json()
  ▶ Leer el body como JSON es I/O (desserialización puede involucrar espera).
  ▶ Como ya se descargó el body completo, este await es casi instantáneo.
  ▶ Retorna la lista de productos.

\[Paso 9] categorias = await resp2.json()
  ▶ Igual que el paso anterior para /categorias.

\[Paso 10] return productos, categorias
  ▶ La coroutine termina. El event loop cierra la sesión (async with \_\_aexit\_\_).
  ▶ asyncio.run() recoge el resultado y destruye el loop.
  ▶ FIN.
```

\---

## Prints Agregados al Código y Orden Observado

```python
async def obtener\_datos():
    async with aiohttp.ClientSession() as session:
        print("\[1] Antes de crear tarea1")
        tarea1 = session.get("http://localhost:3000/api/productos")
        print("\[2] Antes de crear tarea2")
        tarea2 = session.get("http://localhost:3000/api/categorias")
        print("\[3] Antes de await gather")
        resp1, resp2 = await asyncio.gather(tarea1, tarea2)
        print("\[4] Después de await gather — ambas respuestas listas")
        productos  = await resp1.json()
        print("\[5] Después de await resp1.json()")
        categorias = await resp2.json()
        print("\[6] Después de await resp2.json()")
        return productos, categorias
```

**Salida en consola observada:**

```
\[1] Antes de crear tarea1
\[2] Antes de crear tarea2
\[3] Antes de await gather
\[4] Después de await gather — ambas respuestas listas
\[5] Después de await resp1.json()
\[6] Después de await resp2.json()
```

**Observación clave:** Los prints \[1], \[2] y \[3] aparecen sin ninguna pausa entre ellos porque no hay `await` entre esas líneas. La pausa (\~120 ms) ocurre entre el print \[3] y el \[4], que es exactamente cuando el event loop espera que ambas peticiones HTTP completen.

\---

## Concepto Corregido Después de la Experimentación

Antes de este ejercicio creía que `session.get()` enviaba la petición HTTP inmediatamente al ejecutarse, y que `await` solo servía para "esperar el resultado". Después de experimentar con los prints, comprendí que **`session.get()` solo crea un descriptor de la petición** — no abre ninguna conexión. Es `asyncio.gather()` quien convierte esos descriptores en Tasks activas y el `await` sobre `gather()` es el momento exacto en que el event loop cede el control, envía las peticiones al SO a través de sockets no bloqueantes, y queda libre para hacer otras cosas mientras espera. Este modelo mental es crucial: el `await` no es una espera pasiva, es una **cesión activa del control** al event loop.

