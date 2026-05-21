# Reto IA 6 – Crítico de Decisiones de Concurrencia
**Alumno:** Ricardo Matos Vizcarra  
**Materia:** Programación Distribuida del Lado del Cliente  
**Semana 3 – Fase 3: Reflexiona**

---

## ADR: Architecture Decision Records – Cliente Asíncrono EcoMarket

---

### ADR-001: Estrategia de Coordinación de Peticiones

**Contexto:**  
El dashboard de EcoMarket necesita cargar datos de 3-4 endpoints simultáneamente.
Las opciones principales son: `asyncio.gather()`, `asyncio.wait()`, y `asyncio.as_completed()`.

**Decisión:**  
Usar `asyncio.gather(return_exceptions=True)` como estrategia principal.

**Razonamiento detallado (Diálogo socrático con IA):**

*IA preguntó: "¿Por qué elegiste gather? ¿Cuándo sería mejor wait()?"*

Mi respuesta: Elegí `gather()` porque el dashboard necesita **todos** los datos antes de renderizar. Si elegiera `wait()` con `FIRST_COMPLETED`, tendría que manejar un bucle y estado parcial, lo que añade complejidad sin beneficio para este caso. La pregunta me hizo identificar que `gather()` tiene un punto débil: si una petición tarda mucho, **bloquea mostrar los datos que ya llegaron**. Esto me hizo agregar `cargar_con_prioridad()` como función alternativa para cuando el UX requiera datos progresivos.

*IA preguntó: "¿Qué pasa si necesito mostrar datos progresivamente (conforme llegan)?"*

Mi respuesta: En ese caso `as_completed()` o `wait(FIRST_COMPLETED)` son superiores. Para EcoMarket, el dashboard principal usa `gather()` pero la barra lateral de notificaciones usaría `as_completed()` porque el usuario puede ver la barra poblarse progresivamente sin esperar el endpoint más lento.

**Alternativas consideradas:**

| Alternativa | Trade-off |
|---|---|
| `gather()` sin `return_exceptions` | Error en 1 petición mata todas → **descartada** |
| `wait(FIRST_COMPLETED)` | Mejor UX progresivo, pero requiere estado intermedio más complejo |
| `as_completed()` | Ideal para procesamiento en orden de llegada, no para "mostrar todo junto" |
| `wait(FIRST_EXCEPTION)` | Útil si queremos abortar ante errores, pero no para dashboard resiliente |

**Consecuencias:**
- ✅ La implementación es simple: una sola llamada `gather()` con `return_exceptions=True`
- ✅ El fallo de 1 de 4 fuentes no descarta las demás
- ⚠️ La latencia percibida = la petición más lenta (no la más rápida)
- ⚠️ No hay datos parciales hasta que todas completan o fallan

---

### ADR-002: Sesión HTTP Compartida vs. Sesión por Petición

**Contexto:**  
En el cliente síncrono de Semana 2, cada función hacía `requests.get()` directamente (sin gestión de sesión). Al migrar a `aiohttp`, hay dos opciones: crear una `ClientSession` por petición o una sesión compartida para todo el grupo de operaciones.

**Decisión:**  
Una sola `ClientSession` por bloque de operaciones relacionadas, pasada como parámetro a cada función CRUD.

**Razonamiento detallado (Diálogo socrático con IA):**

*IA preguntó: "¿Qué beneficio da compartir sesión? ¿Hay riesgos?"*

Mi respuesta: El beneficio principal es la **reutilización del pool de conexiones TCP**. Cada `ClientSession` mantiene un pool de conexiones abiertas al mismo host. Si creo una sesión por petición, cada petición hace un TCP three-way handshake (~50ms) que se suma al tiempo total. Con una sesión compartida, el segundo GET reutiliza la conexión ya abierta por el primero.

El riesgo que identifico: si hay un error en la sesión misma (ej. SSL error), afecta a **todas las peticiones** que la usen. Por eso el cierre debe ser explícito con `async with`.

*IA preguntó: "¿Qué pasa si necesito headers diferentes por petición?"*

Mi respuesta: Los headers específicos por petición se pasan directamente en `session.get(url, headers=headers_extra)`. Los headers globales (como `Authorization`) se configuran al crear la sesión. Esta separación es limpia: los headers de autenticación van en la sesión, los headers de contenido van en la petición individual.

**Decisión cambiada después de reflexión:**  
Inicialmente había considerado pasar la sesión como variable global. El diálogo socrático me convenció de **pasarla como parámetro** porque permite:
1. Tests unitarios (se puede pasar una sesión mock)
2. Múltiples sesiones con diferentes configuraciones sin conflicto
3. El scope de vida de la sesión queda explícito en quien la crea

**Alternativas consideradas:**

| Alternativa | Trade-off |
|---|---|
| Sesión por petición | Simple pero ineficiente: un TCP handshake por petición |
| Sesión global (variable de módulo) | Fácil acceso pero dificulta testing y tiene riesgos de estado compartido |
| **Sesión como parámetro** ✓ | Testeable, explícita, permite múltiples sesiones concurrentes |

**Consecuencias:**
- ✅ Reutilización de conexiones TCP (menos latencia)
- ✅ Testeable: se puede pasar una `aioresponses` mock
- ✅ Scope explícito: la sesión vive exactamente lo que el `async with`
- ⚠️ Las funciones CRUD tienen un parámetro extra `session` que no tenían en Semana 2

---

### ADR-003: Timeout Individual vs. Timeout Global

**Contexto:**  
El cliente necesita manejar peticiones lentas. Hay dos enfoques: un timeout global que aplica a toda la operación del dashboard, o timeouts individuales configurables por petición.

**Decisión:**  
Implementar **ambos**: timeout individual por petición (configurable en `aiohttp.ClientTimeout`) más un timeout global opcional que el llamador puede aplicar con `asyncio.wait_for()`.

**Razonamiento detallado (Diálogo socrático con IA):**

*IA preguntó: "¿Qué pasa si el timeout de una petición es 10s pero el usuario espera máximo 3s?"*

Mi respuesta: Este fue el error más grande que identifiqué. Tenía timeouts individuales de 10s, pero el usuario del dashboard espera máximo 3s antes de frustrarse. La solución correcta es tener **dos niveles**:
- Timeout de petición: protege contra un servidor lento en una ruta específica
- Timeout de dashboard: protege la experiencia del usuario final

Si el timeout de dashboard expira a los 3s, se muestra lo que esté disponible y se cancela el resto.

*IA preguntó: "¿Debería haber un timeout 'de dashboard' que cancele todo?"*

Mi respuesta: Sí, y es la decisión que cambiaría. El código original solo tenía timeouts por petición. Después de la reflexión, `cargar_dashboard()` debería estar envuelto en `asyncio.wait_for(cargar_dashboard(), timeout=3.0)` para respetar el SLA del usuario.

**Alternativas consideradas:**

| Alternativa | Trade-off |
|---|---|
| Solo timeout global | Protege al usuario pero puede cancelar peticiones útiles que casi terminaban |
| Solo timeout por petición | Cada petición está protegida pero el dashboard total puede tardar infinito si los timeouts son grandes |
| **Ambos niveles** ✓ | Control fino: timeout individual protege por ruta, timeout global protege la experiencia |

**Consecuencias:**
- ✅ Cada petición puede tener un timeout apropiado a su naturaleza (/notificaciones puede ser más laxo que /perfil)
- ✅ El usuario nunca espera más del SLA del dashboard
- ⚠️ Requiere documentar claramente qué timeout aplica dónde para evitar confusión

---

## Resumen de Fortalezas y Debilidades del Cliente Asíncrono

| Aspecto | Fortaleza | Debilidad |
|---|---|---|
| `gather(return_exceptions=True)` | Resiliente: 1 fallo no cancela todo | Latencia percibida = petición más lenta |
| Sesión como parámetro | Testeable y explícita | Parámetro adicional en todas las funciones |
| Timeout individual | Control fino por endpoint | Requiere conocer la latencia esperada de cada endpoint |
| Sin reintentos | Simple, menos código | Errores transitorios 5xx no se recuperan automáticamente |
| Semáforo de 10 | Protege al servidor de sobrecarga | El número 10 fue arbitrario; debería basarse en benchmarks reales |

**Decisión que cambiaría:** Agregaría timeout global de dashboard envolviendo `cargar_dashboard()` con `asyncio.wait_for()` para respetar el SLA del usuario, que es la métrica más importante desde la perspectiva del producto.
