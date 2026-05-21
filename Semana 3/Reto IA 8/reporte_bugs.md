# Reporte de Bugs - Testing Asíncrono de EcoMarket

**Alumno:** Ricardo Matos Vizcarra
**Materia:** Programación Distribuida del Lado del Cliente  
**Semana 3 – Reto IA 8**

---

Durante el desarrollo y ejecución de la suite de pruebas asíncronas (`test_cliente_async.py`), se identificaron varios problemas en el cliente base que no eran evidentes en la implementación síncrona.

## Bugs Encontrados y Soluciones Aplicadas

### Bug 1: Fuga de Conexiones (Connection Leak)
**Descripción:** Al ejecutar el test concurrente con 50+ peticiones, la suite de pruebas comenzaba a fallar esporádicamente lanzando errores de socket cerrado o timeouts inesperados. 
**Causa:** No se estaban cerrando correctamente las instancias de `ClientSession` ni los cuerpos de las respuestas HTTP (`response.json()` no se consumía en rutas de error).
**Corrección Aplicada:** Se estandarizó el uso de contextos `async with` tanto para la creación de la sesión como para la petición HTTP individual. Esto asegura que el método `__aexit__` de aiohttp devuelva la conexión TCP al pool o la cierre limpiamente incluso si se lanza una excepción.

### Bug 2: Timeouts no silenciados bloqueando la ejecución principal
**Descripción:** En las pruebas donde se simulaban latencias extremas, si una función `fetch_producto()` lanzaba `asyncio.TimeoutError`, el bloque `asyncio.gather()` abortaba toda la ejecución, interrumpiendo peticiones válidas.
**Causa:** El uso por defecto de `gather()` sin parámetros adicionales aborta ante la primera excepción.
**Corrección Aplicada:** Se instruyó el uso del parámetro `return_exceptions=True` en llamadas concurrentes clave, permitiendo iterar sobre los resultados y aislando los errores por petición. Esto se verificó mediante la prueba `test_gather_con_return_exceptions`.

### Bug 3: Procesamiento incorrecto de respuestas no-JSON
**Descripción:** Cuando el servidor mock simulaba un Error 500 de pasarela devolviendo un payload en HTML (ej. de Nginx), el método `await response.json()` crasheaba la aplicación entera con un error de decodificación JSON en lugar de manejar el error HTTP.
**Causa:** Se intentaba decodificar el cuerpo de la respuesta antes de validar el código de estado HTTP o el `Content-Type`.
**Corrección Aplicada:** Se modificaron las funciones CRUD para invocar `response.raise_for_status()` inmediatamente después de recibir la respuesta y *antes* de llamar a `.json()`. Esto asegura que los errores HTTP se eleven como excepciones de red manejables, como se comprueba en el test `test_json_invalido`.
