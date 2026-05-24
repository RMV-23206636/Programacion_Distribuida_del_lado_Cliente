# Reporte de validacion - Semana 9

| Caso | Objetivo | Esperado | Observado | Estado |
| --- | --- | --- | --- | --- |
| 1 | Exito en CERRADO | Sigue CERRADO | CERRADO | PASA |
| 2 | Tres errores 503 | Abre circuito | ABIERTO | PASA |
| 3 | ABIERTO protege servidor | Rechazo local sin aumentar contador | 4->4 | PASA |
| 4 | Recuperacion | SEMIABIERTO cierra con exito | CERRADO y fallos 0 | PASA |
| 5 | 401 Unauthorized | No cuenta como fallo | CERRADO/0 | PASA |
| 6 | Timeout | Cuenta como fallo y abre | ABIERTO | PASA |
| 7 | Concurrencia SEMIABIERTO | Una prueba pasa; otras fallan rapido | exitos=1, rechazadas=2 | PASA |

## Bugs auditados y fixes

- Timer fantasma: se evita con `time.monotonic()` en lugar de `time.time()`.
- Contador que no resetea: `_registrar_exito()` pone fallos en `0`.
- 401 contado como fallo: `_es_fallo_servidor()` ignora 4xx.
- Avalancha en SEMIABIERTO: se usa `asyncio.Lock` y las peticiones extra reciben `CircuitOpenError`.

## Evidencia de proteccion al servidor

`demo_resiliencia.log` muestra que al abrir el circuito el contador no aumenta:

```text
servidor_antes=6 servidor_despues=6
```
