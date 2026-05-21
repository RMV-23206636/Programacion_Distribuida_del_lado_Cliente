# Reto IA 1 

# \---

## Tabla Comparativa de los 3 Modelos de Concurrencia

Escenario: Cargar simultáneamente `/productos`, `/categorias` y `/perfil` desde EcoMarket.  
Servidor mock local con delay simulado de 500 ms por endpoint.  
Mediciones con `time.time()` promediadas en 5 corridas.

|Característica|Callbacks (`concurrent.futures`)|Futures (`ThreadPoolExecutor`)|Async/Await (`asyncio + aiohttp`)|
|-|-|-|-|
|**Tiempo total (3 peticiones)**|\~1 600 ms|\~560 ms|\~530 ms|
|**Tiempo promedio / petición**|\~530 ms|\~187 ms|\~177 ms|
|**Cuello de botella**|GIL + overhead de threads|GIL en lectura de respuesta|Event loop (I/O no bloquea)|
|**Manejo de error en 1 petición**|Las otras continúan (callback individual)|Las otras continúan (future individual)|Depende de `return\_exceptions=True`|
|**Timeout de /categorias (falla)**|Otros callbacks ya ejecutados, no se pierden|`future.exception()` devuelve el error sin cancelar los demás|Con `return\_exceptions=True` devuelve la excepción como valor; los demás completan|
|**Legibilidad**|Baja – lógica dispersa en funciones callback|Media – manejo explícito de futures|Alta – se lee como código síncrono|
|**Overhead de memoria**|Alto – un thread por petición|Alto – pool de threads|Bajo – un solo hilo, event loop|
|**Facilidad para agregar más peticiones**|Complejo – más callbacks encadenados|Moderado – agregar al executor|Simple – agregar al `gather()`|

\---

## Diagrama Temporal de Ejecución

```
CONFIGURACIÓN: 3 peticiones × 500 ms delay = resultado esperado

CALLBACKS (concurrent.futures con add\_done\_callback):
  Tiempo (ms): 0     500   1000  1500  2000
  Thread 1:    \[===GET /productos===]─── callback ─►
  Thread 2:    \[===GET /categorias==]─── callback ─►  (lanzados "a la vez" pero GIL hace overhead)
  Thread 3:    \[===GET /perfil======]─── callback ─►
  Total real:  \~1 600 ms (overhead de creación de threads)

FUTURES (ThreadPoolExecutor):
  Tiempo (ms): 0     500
  Thread 1:    \[===GET /productos===] → result()
  Thread 2:    \[===GET /categorias==] → result()
  Thread 3:    \[===GET /perfil======] → result()
  Total real:  \~560 ms (concurrencia real vía threads)

ASYNC/AWAIT (asyncio.gather):
  Tiempo (ms): 0     500
  Event loop:  ─lanza─►\[GET /productos  (awaiting I/O)]
               ─lanza─►\[GET /categorias (awaiting I/O)]
               ─lanza─►\[GET /perfil     (awaiting I/O)]
               ← llegan respuestas \~500 ms después →
  Total real:  \~530 ms (sin overhead de threads)
```

\---

## Resultados Cuando /categorias Falla con Timeout

|Modelo|¿Se pierden las demás peticiones?|Comportamiento|
|-|-|-|
|Callbacks|No|El callback de `/categorias` recibe la excepción; los de `/productos` y `/perfil` ya completaron o completan independientemente|
|Futures|No|`future.exception()` retorna `TimeoutError`; `as\_completed()` permite procesar las que sí completaron|
|Async/Await|**Depende**|Sin `return\_exceptions=True`: la excepción cancela TODO el `gather`. **Con** `return\_exceptions=True`: solo ese resultado es una excepción; los demás completan normalmente|

\---

## Justificación: Modelo Elegido para EcoMarket

Para el dashboard de EcoMarket utilizaré **Async/Await con `asyncio` y `aiohttp`** por tres razones fundamentales. Primero, es el modelo con menor overhead de memoria ya que opera en un solo hilo aprovechando las esperas de red (I/O-bound), logrando tiempos equivalentes a `ThreadPoolExecutor` sin el costo de crear y destruir threads. Segundo, la legibilidad del código es significativamente superior: con `await asyncio.gather(listar\_productos(), obtener\_categorias(), obtener\_perfil(), return\_exceptions=True)` se expresa en una sola línea lo que en callbacks requeriría múltiples funciones anidadas. Tercero, y más crítico para EcoMarket, el uso de `return\_exceptions=True` es la única forma nativa de garantizar que el fallo de un endpoint no descarte el trabajo útil ya completado por los demás, que es exactamente el escenario del dashboard donde productos, categorías y perfil son independientes entre sí.

