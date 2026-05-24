# Reto IA 5 - Umbrales

Se eligio umbral 3 y timeout 2 segundos para demo.

| Escenario | Analisis | Decision |
| --- | --- | --- |
| Falla aislada | Abrir con 1 seria falso positivo | umbral mayor que 1 |
| Polling de operadores | Puede saturar servidor en falla real | abrir tras 3 fallos |
| Recuperacion | Probar demasiado pronto causa avalancha | timeout + SEMIABIERTO |

Limite: el breaker no recupera el servidor ni reemplaza cache/degradacion elegante.

## Escenario 2: respuestas lentas

Si el servidor tarda 45 segundos en responder, el cliente debe aplicar timeout y convertir esa espera excesiva en `TimeoutError`. Esa excepcion cuenta como fallo de servidor porque, desde la experiencia del cliente, el servicio no esta disponible en tiempo util. La implementacion lo refleja en `_es_fallo_servidor()` y el Caso 6 del validador.
