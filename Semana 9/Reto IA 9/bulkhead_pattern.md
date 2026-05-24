# Reto IA 9 - Bulkhead Pattern

Bulkhead limita recursos concurrentes por dependencia.

```text
inventario_pool: max 3
precios_pool: max 5
auth_pool: max 2

request(endpoint):
  bulkhead = seleccionar_bulkhead(endpoint)
  breaker = seleccionar_breaker(endpoint)
  con permiso del bulkhead:
    breaker.ejecutar(lambda: http.request(endpoint))
```

Beneficio: si inventario tarda 45 segundos, no consume recursos de precios ni auth.
