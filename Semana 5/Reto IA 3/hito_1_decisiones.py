"""
DECISIONES DE DISEÑO — Cliente EcoMarket / Hito 1
==================================================
TIMEOUT_HTTP = 10s
  → Trade-off: Un timeout muy corto puede cancelar peticiones legítimas que solo tardan un poco por latencia de red, mostrando falsos errores al usuario. Un timeout muy largo (ej. 60s) bloquea los recursos del cliente, acumulando esperas infinitas si el servidor está caído.
    Decisión: 10s es un balance adecuado para operaciones de lectura como consultar inventario/pedidos, lo suficientemente rápido para fallar a tiempo y permitir al ciclo reintentar.

INTERVALO_POLLING_BASE = 5s
  → Trade-off: Un intervalo más corto daría datos en "tiempo real" pero saturaría la CPU, la red del cliente y mantendría muchas conexiones abiertas. Un intervalo más largo causaría que la UI muestre datos obsoletos durante mucho tiempo.
    Decisión: 5s es razonable para dar una sensación de inmediatez sin sobrecargar, más aún porque se combina con backoff si el sistema no presenta cambios.

REINTENTOS_MAX = 3 (En caso de errores 5xx)
  → Trade-off: Menos reintentos resultan en menor resiliencia (el cliente se rinde muy rápido ante un error transitorio). Más reintentos mantienen conexiones persistentes retrasando el reporte de error y agotando la memoria con callbacks en espera.
    Decisión: 3 reintentos son el estándar de la industria. Permite soportar fallas menores y notificar fallas graves a la UI sin demora excesiva.

Corrección al resumen de la IA:
  Resumen de la IA validado sin correcciones. Refleja fielmente los compromisos adquiridos en la arquitectura del cliente base.
"""
