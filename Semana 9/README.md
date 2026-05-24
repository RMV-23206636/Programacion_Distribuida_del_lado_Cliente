# Semana 9 - Resiliencia del Cliente

Proyecto integrado de Circuit Breaker y tolerancia a fallos para el cliente de EcoMarket.

## Entregable unico

- `circuit_breaker.py`: CircuitBreaker completo con decisiones de diseno en docstring.
- `cliente_robusto.py`: ClienteRobusto integrado con CircuitBreaker + TokenManagerDummy + demo ejecutable.
- `demo_resiliencia.log`: salida del script con normal, fallo, apertura y recuperacion.
- `reporte_validacion.md`: tabla de 7 casos, bugs encontrados y fix aplicado.
- `validar_resiliencia.py`: verificacion automatizada de los 7 casos.

## Diagrama de estados

```text
CERRADO --fallos >= umbral--> ABIERTO
ABIERTO --timeout_apertura--> SEMIABIERTO
SEMIABIERTO --exito---------> CERRADO
SEMIABIERTO --fallo---------> ABIERTO
ABIERTO --peticion normal---> CircuitOpenError sin contactar servidor
```

## Decisiones de resiliencia

Umbral: 3 fallos consecutivos. Evita abrir por un incidente aislado, pero corta antes de que el polling de varios operadores amplifique la falla.

Timeout: 2 segundos para la demo. En produccion conviene 30-60 segundos con jitter.

| Escenario | Decision | Razon |
| --- | --- | --- |
| 503 | FALLO | El servidor declara indisponibilidad. |
| Timeout | FALLO | No hay respuesta util. |
| Error de red | FALLO | No se alcanzo el servicio. |
| 500 | FALLO | Error interno del servidor. |
| 401 | IGNORAR | Problema de token/autenticacion. |
| 404 | IGNORAR | Ruta o recurso inexistente. |
| 400 | IGNORAR | Peticion invalida del cliente. |
| CircuitOpenError | IGNORAR | Es proteccion local, no falla nueva del servidor. |

## Auth y breaker

Las peticiones de auth no deben quedar bloqueadas por el mismo breaker global de inventario. Si inventario abre el circuito y tambien bloquea `refresh_access_token()`, el cliente queda en deadlock Auth-Breaker. La solucion es breaker separado para auth o canal de refresh independiente.

## Limites

El mock no usa red real; simula los casos necesarios. El timeout es pedagogico. La arquitectura multi-breaker y bulkhead se documenta en los Retos 8 y 9.

## Escenario 2: respuestas lentas

Las respuestas lentas deben activar el breaker cuando exceden el timeout operativo del cliente. En esta implementacion se modelan con `TimeoutError`, y `_es_fallo_servidor()` las clasifica como FALLO. Si el servidor responde en 45 segundos, el cliente no debe esperar indefinidamente ni multiplicar reintentos; debe cortar por timeout, registrar fallo y abrir el circuito al llegar al umbral.
