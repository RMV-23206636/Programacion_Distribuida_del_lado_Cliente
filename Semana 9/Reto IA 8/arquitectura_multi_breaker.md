# Reto IA 8 - Circuit Breaker por endpoint

Problema: si `/api/inventario` falla y se usa breaker global, tambien bloquea `/api/precios` aunque precios este sano.

```text
breakers = {
  "inventario": CircuitBreaker(3, 30),
  "precios": CircuitBreaker(3, 20),
  "auth": CircuitBreaker(5, 10)
}

seleccionar_breaker(endpoint):
  /api/inventario -> inventario
  /api/precios -> precios
  /auth -> auth
```

Auth tiene breaker propio para evitar deadlock Auth-Breaker.
