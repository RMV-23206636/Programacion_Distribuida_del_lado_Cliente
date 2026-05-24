# Reto IA 2 - Clasificacion de errores

| Error | Decision | Justificacion |
| --- | --- | --- |
| 503 | FALLO | Servidor indisponible. |
| Timeout | FALLO | No responde en tiempo util. |
| ConnectionError | FALLO | Falla de red. |
| 500 | FALLO | Falla interna del servidor. |
| 401 | IGNORAR | Lo maneja TokenManager. |
| 404 | IGNORAR | Recurso/ruta incorrecta. |
| 400 | IGNORAR | Peticion invalida. |
| CircuitOpenError | IGNORAR | Proteccion local. |

Implementado en `../circuit_breaker.py`, metodo `_es_fallo_servidor()`.
