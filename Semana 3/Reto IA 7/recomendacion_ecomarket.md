# Recomendación de Estrategia de Coordinación para EcoMarket

**Alumno:** Ricardo Matos Vizcarra 
**Materia:** Programación Distribuida del Lado del Cliente  
**Semana 3 – Reto IA 7**

---

## Análisis de Estrategias de Coordinación

Tras implementar y comparar las 4 estrategias principales (`gather`, `wait(FIRST_COMPLETED)`, `as_completed`, y `wait(FIRST_EXCEPTION)`), he observado los siguientes comportamientos:

1. **asyncio.gather()**:
   - **Pros**: Sintaxis muy sencilla y limpia. Excelente cuando necesitamos todos los resultados juntos (ej. un array ordenado de respuestas). Soporta `return_exceptions=True` para manejar errores sin abortar el resto.
   - **Contras**: Bloquea la ejecución hasta que *todas* las promesas se resuelven. No es útil si queremos renderizar la UI progresivamente.

2. **asyncio.wait(return_when=FIRST_COMPLETED)**:
   - **Pros**: Permite procesar las respuestas en lotes conforme llegan. Muy útil para actualizar el dashboard de EcoMarket parcialmente.
   - **Contras**: Requiere gestionar manualmente los sets de tareas (pendientes y terminadas), haciendo el código más verboso.

3. **asyncio.as_completed()**:
   - **Pros**: Proporciona un iterador que retorna los resultados exactamente en el orden en que se completan. Ideal para un flujo constante de datos hacia la UI.
   - **Contras**: Se pierde la correlación directa entre la corrutina original y el resultado (a menos que el resultado incluya un identificador). 

4. **asyncio.wait(return_when=FIRST_EXCEPTION)**:
   - **Pros**: Perfecto para escenarios de "todo o nada". Si una petición crítica falla (como la validación del token de usuario), podemos abortar e invalidar rápidamente las demás para ahorrar recursos.
   - **Contras**: Demasiado agresivo para vistas donde algunas fallas son tolerables (ej. si falla el banner de promociones, el usuario aún debería ver los productos).

## Recomendación Justificada para EcoMarket

Para la arquitectura general del **Dashboard de EcoMarket**, mi recomendación es utilizar una **estrategia híbrida**, dependiendo del endpoint específico que se esté consultando:

*   **Para los datos críticos iniciales (Perfil de Usuario y Configuración Base):** Recomiendo usar `asyncio.gather()` (o `wait` con `FIRST_EXCEPTION`). El dashboard no puede renderizarse correctamente si el perfil del usuario falla. Queremos esperar todo esto al mismo tiempo y abortar si ocurre un error grave.
*   **Para la carga de la vista principal (Productos, Categorías, Notificaciones, Recomendaciones):** Recomiendo encarecidamente utilizar **`asyncio.as_completed()`** o **`asyncio.wait(FIRST_COMPLETED)`**.
    
    *   **Justificación UX:** EcoMarket debe sentirse rápido y responsivo. Si el microservicio de "Recomendaciones" está lento y tarda 3 segundos, no deberíamos bloquear la renderización de la lista de "Productos" que respondió en 200ms. Utilizando `as_completed()`, el cliente HTTP puede pasar inmediatamente los productos al frontend para que sean dibujados en pantalla, mejorando drásticamente el *First Meaningful Paint (FMP)* y la percepción de velocidad del usuario. Las recomendaciones aparecerán en su sección correspondiente un par de segundos después sin congelar la app.

Por lo tanto, la robustez de EcoMarket se maximiza combinando estrategias según la criticidad del dato que se está solicitando, priorizando el renderizado progresivo para el contenido pesado.
