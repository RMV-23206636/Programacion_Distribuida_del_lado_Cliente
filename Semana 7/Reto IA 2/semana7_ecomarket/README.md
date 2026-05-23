# Decisiones de diseño — entendidas antes de codificar

**1. "Si abro 3 objetos EventSource en un navegador hacia el mismo origen, y el límite es 6 conexiones por origen, ¿cuántas quedan libres para fetch()? ¿Qué pasa si también necesito hacer un fetch() de autenticación cada hora?"**
Si se abren 3 objetos EventSource, consumirán 3 de las 6 ranuras del pool de conexiones HTTP/1.1 del navegador. Esto dejaría 3 conexiones libres para otras operaciones `fetch()`. Si se realiza una autenticación, ocupará 1 ranura más, reduciendo a 2 las disponibles, lo cual podría llevar al encolado de peticiones si hay más operaciones concurrentes.

**2. "Si en lugar de un navegador uso Python con requests, ¿hay el mismo límite? ¿Qué limita las conexiones en ese caso?"**
En Python con bibliotecas como `requests`, no existe el mismo límite estricto de 6 conexiones por origen integrado en el navegador. En este caso, el límite lo determinan los recursos del sistema operativo (como el número de descriptores de archivo disponibles, ulimits) y la capacidad del servidor para aceptar y mantener las conexiones activas, así como el propio pool de conexiones configurado en la biblioteca.

**3. "Si el servidor envía este bloque SSE: ... y yo no tengo registrado ningún handler para 'precio-actualizado', ¿qué debería hacer mi cliente? ¿Lanzar excepción? ¿Ignorar? ¿Por qué?"**
El cliente debe ignorarlo silenciosamente y continuar con el stream. Esto permite que la API del servidor evolucione y agregue nuevos tipos de eventos en el futuro sin provocar un fallo en los clientes antiguos que no tengan implementados handlers para ellos. Esto asegura compatibilidad hacia atrás y tolerancia a fallos.

**4. "Si quiero añadir el módulo 'devoluciones' a mi conexión multiplexada mientras está activa (sin reconectar), ¿mi cliente puede hacerlo con los parámetros de URL? ¿Por qué sí o no?"**
No, no se puede hacer sin reconectar. En SSE, los parámetros que determinan la suscripción se envían en la cadena de consulta (query string) de la solicitud HTTP GET inicial que establece el canal. Dado que la conexión ya está establecida, la única manera de actualizar los parámetros de la URL y suscribirse a un nuevo módulo es cerrar la conexión activa y abrir una nueva con la URL actualizada.

**Síntesis:**
- La multiplexación de conexiones es crucial para no saturar el pool de conexiones del cliente y degradar el rendimiento del navegador.
- Es vital ignorar eventos desconocidos para lograr un diseño extensible que no dependa de acoplamiento estricto con el servidor.
- SSE opera de forma unidireccional tras la petición, obligando al cliente a reiniciar la conexión HTTP si la intención de suscripción (los parámetros URL) debe cambiar.
