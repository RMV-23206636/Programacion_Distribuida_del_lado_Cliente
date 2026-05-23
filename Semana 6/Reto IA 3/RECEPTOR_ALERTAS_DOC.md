# Reto IA 3 - Reflexiona

"""
RECEPTOR ALERTAS ECOMARKET — Decisiones de arquitectura (cliente)

Escenario A (10,000 usuarios, precios cambian 2-3 veces/hora):
SSE elegido sobre polling porque cada cliente mantendrá 1 conexión TCP en idle la mayor parte del tiempo, recibiendo actualizaciones instantáneas cuando ocurran. Polling generaría 10,000 peticiones cada N segundos (e.g. cada segundo = 600,000 req/min) la inmensa mayoría respondiendo 304 (sin cambios), derrochando red y saturando la CPU del servidor para procesar peticiones vacías.

Escenario B (Servidor legacy sin soporte de streaming):
Polling elegido sobre SSE porque es la única opción soportada. SSE requiere que el servidor pueda responder con `text/event-stream` y mantenga la conexión TCP abierta. Si el backend es una API REST clásica que cierra la conexión al responder, el cliente debe usar polling forzosamente.

Escenario C (Cliente móvil con conectividad inestable, interrupciones cada 20-30s):
Polling (o un híbrido) suele ser más robusto aquí, o bien SSE pero sabiendo que requerirá continuas reconexiones. Si la conexión cae cada 20s, un cliente SSE pasará más tiempo en la rutina de reconexión y timeouts. El pooling corto permite un control de estado más predecible en redes degradadas, ya que no depende de mantener el socket vivo, aunque consume más batería. (Nota: SSE reconectará, pero requerirá de Last-Event-ID y un historial en el backend).

Escenario D (Recibir alertas y enviar comandos en la misma sesión activa):
WebSocket elegido sobre SSE. SSE es estrictamente unidireccional (Servidor -> Cliente). Para enviar comandos o filtros complejos al servidor mientras la conexión está activa, con SSE se necesitaría hacer peticiones HTTP POST adicionales, perdiendo la cohesión. WebSocket provee un canal bidireccional puro a través de un solo socket.
"""
