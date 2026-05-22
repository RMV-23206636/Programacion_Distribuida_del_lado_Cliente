# Reto 5: Extensión Avanzada - Retry con Jitter y el Thundering Herd

**Problema del Thundering Herd en el cliente:**
Si el servidor cae repentinamente a t=0, y tenemos 500 instancias de nuestro cliente consultando con un intervalo de 5s, todos al mismo tiempo fallarán. Al usar un backoff estándar (`intervalo * 2`), todos los 500 clientes intentarán reconectarse exactamente al mismo tiempo (a los 10s, luego a los 20s, a los 40s...). Esto causa picos masivos de tráfico que podrían tumbar el servidor de nuevo tan pronto se recupere. El cliente experimentará esto como rechazos repetidos, timeouts persistentes y lentitud, a pesar del backoff.

**Solución en código:**
Añadiendo Jitter decorrelacionamos a todos esos clientes, haciendo que despierten en un rango de tiempos distribuidos y dándole al servidor oportunidad de recuperarse limpiamente.

```python
import random

# Reemplazar el backoff tradicional:
# self.intervalo_actual = min(self.intervalo_actual * 2, INTERVALO_MAX)

# Por una versión con Jitter (Decorrelacionado)
base_backoff = min(self.intervalo_actual * 2, INTERVALO_MAX)
self.intervalo_actual = random.uniform(base_backoff / 2, base_backoff)
```

**Justificación:**
*Desde la perspectiva del cliente:* Al agregar jitter, nuestro cliente espera un tiempo un poco distinto e impredecible (por ejemplo, 14.3s en lugar de 20s exactos). Así evita colisionar de frente con las miles de otras instancias de clientes, aumentando radicalmente la probabilidad de que su solicitud pase exitosamente cuando el servidor despierte.
