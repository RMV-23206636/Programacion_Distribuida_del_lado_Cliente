# Reto 1: Diagnóstico Pre-Examen

**🤖 IA (Mentor Técnico Senior):** ¡Hola! Vamos a diagnosticar tus conocimientos antes del Examen Práctico 1.

**PREGUNTA 1: Sobre HTTP** 
Explica con tus propias palabras qué diferencia hay entre manejar un error de red (el servidor no respondió) y manejar un error HTTP 4xx (el servidor respondió pero rechazó mi petición). ¿Qué debe hacer mi cliente en cada caso?

**👨‍💻 Estudiante:** Un error de red es como intentar llamar a alguien y que el teléfono ni siquiera dé tono (ej. sin conexión a internet o el servidor está caído); aquí el cliente puede esperar un momento y volver a intentar (reintentos). Un error 4xx es cuando te contestan pero te dicen que marcaste el número equivocado; aquí el cliente no debe reintentar porque el error fue suyo al enviar una petición incorrecta.

**🤖 IA:** ¡Excelente analogía! Tienes muy clara la diferencia.
- *Lo que está bien:* Distinguir entre fallo de comunicación vs. petición rechazada, y entender que un 4xx NO se reintenta.
- *Lo que falta:* Aunque en el error de red dijiste "esperar y reintentar", faltó aclarar que el reintento debe tener un *backoff* para no abrumar al servidor.

---

**PREGUNTA 2: Sobre validación de respuesta**
Describe qué pasos realiza mi cliente DESPUÉS de recibir un 200 OK antes de usar los datos. ¿Qué puede salir mal?

**👨‍💻 Estudiante:** Después de recibir el 200 OK, el cliente debe decodificar el JSON. Luego debe revisar que los campos esperados (como "pedidos") existan y no sean `null`. Lo que puede salir mal es que el servidor envíe un JSON malformado, o que falten propiedades que la UI asume que existen, causando un crash en el cliente.

**🤖 IA:** ¡Muy bien!
- *Lo que está bien:* Sabes que un 200 OK no garantiza que el contenido sea seguro de usar directamente.
- *Lo que falta:* Recordar que si el JSON no es válido, puede saltar un error al intentar deserializarlo (ej. `JSONDecodeError`), por lo que ese paso debe estar dentro de un bloque `try-except`.

---

**PREGUNTA 3: Sobre async/await**
¿Qué pasa si llamo a una función async sin await en Python? ¿Cómo lo detecto? ¿Cómo lo corrijo?

**👨‍💻 Estudiante:** Si la llamo sin `await`, la función no se ejecuta, solo devuelve un objeto corrutina. Lo detecto porque el código que debería ejecutarse no hace nada, o porque Python imprime un warning diciendo "coroutine was never awaited". Lo corrijo poniendo `await` antes de la llamada a la función dentro de otra función async.

**🤖 IA:** ¡Perfecto!
- *Lo que está bien:* Explicaste claramente qué retorna y cómo corregirlo.
- *Lo que falta/Aclaración:* En algunos casos, si no lo esperas (`await`), el script puede terminar antes de que la tarea asíncrona siquiera tenga oportunidad de entrar al event loop.

---

**PREGUNTA 4: Sobre timeout**
¿Por qué configuro un timeout de X segundos en mis peticiones? ¿Qué pasa en el cliente si no hay timeout o si es muy corto?

**👨‍💻 Estudiante:** El timeout evita que el cliente se quede congelado infinitamente esperando una respuesta. Si no hay timeout, la aplicación entera puede detenerse y quedar inutilizable. Si es demasiado corto, el cliente cancelará peticiones que iban a ser exitosas solo porque la red estaba un poco lenta, mostrando errores falsos.

**🤖 IA:** ¡Excelente respuesta!
- *Lo que está bien:* Entiendes el trade-off exacto entre congelar recursos vs cancelar operaciones válidas.
- *Lo que falta:* Nada esencial. Tienes este concepto perfectamente dominado.

---

**PREGUNTA 5: Sobre polling**
¿Para qué sirve el campo ETag y qué responde el servidor si no cambió? ¿Qué hace el cliente?

**👨‍💻 Estudiante:** El ETag es como una "versión" de los datos. En vez de descargar todo siempre, pregunto si cambió esa versión usando `If-None-Match`. Si no cambió, el servidor responde `304 Not Modified` sin datos en el body. El cliente entonces no hace nada (no notifica a la UI) y aplica backoff para consultar con menos frecuencia.

**🤖 IA:** Muy buena explicación.
- *Lo que está bien:* Comprender la optimización de ancho de banda y el uso del código 304.
- *Lo que falta:* Recordar que, aunque no notifiques, tu ciclo de polling DEBE mantener registro del último estado o ETag para futuras consultas.

---

**PREGUNTA 6: Sobre Observer**
¿Cuál es la diferencia entre "el polling notifica a los observadores" y "el polling llama directamente a la UI"?

**👨‍💻 Estudiante:** Si llama directamente a la UI, el código de polling tiene que conocer cómo funciona la UI (están acoplados). Si uso Observer, el polling solo grita "hubo un cambio" sin importarle quién escucha. Esto permite añadir más cosas (como una alerta o un logger) sin tocar el código de polling.

**🤖 IA:** ¡Exacto!
- *Lo que está bien:* Diste en el clavo con el "desacoplamiento".
- *Lo que falta:* Asegurarte de que al notificar a los observadores, lo haces mediante un método estándar como `actualizar(datos)`.

---
**Diagnóstico Final:**
¡Estás muy bien preparado! Tu comprensión de HTTP, async, polling y Observer es sólida. El área que podría requerir un repaso rápido es el **manejo de excepciones específicas durante la validación de respuestas (Bloque 1/2)**.
*Recomendación:* Revisa cómo implementar el `try/except` envolviendo el parseo JSON para que respuestas corruptas no crasheen tu aplicación.
