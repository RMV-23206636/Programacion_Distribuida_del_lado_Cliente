# Configuración Óptima del Pool de Conexiones

**Alumno:** Ricardo Matos Vizcarra 
**Materia:** Programación Distribuida del Lado del Cliente  
**Semana 3 – Reto IA 10**

---

## El Problema del Agotamiento de Conexiones

Cuando se desarrollan clientes asíncronos que manejan picos altos de tráfico (como scripts de scraping, crawlers o testeadores de carga), instanciar indiscriminadamente múltiples peticiones HTTP puede llevar a dos cuellos de botella graves:

1.  **Agotamiento de sockets (File Descriptors limit):** El sistema operativo tiene un límite de archivos/sockets abiertos por proceso. Si `aiohttp` abre una conexión TCP nueva por cada corrutina disparada y no las cierra o limita, el OS lanzará errores como `Too many open files`.
2.  **Sobrecarga del servidor remoto:** Si se realizan cientos de peticiones concurrentes, podemos tumbar un servidor web frágil (ataque DoS no intencionado) o hacer que su firewall/WAF nos bloquee la IP (rate limiting HTTP 429).

## Configuración Óptima Recomendada para EcoMarket

Para el proyecto de EcoMarket, donde consultamos una API REST en un entorno predecible, la configuración del pool de conexiones se maneja inyectando una instancia de `aiohttp.TCPConnector` en la `ClientSession`.

```python
connector = aiohttp.TCPConnector(
    limit=100,
    limit_per_host=30,
    keepalive_timeout=60.0
)
session = aiohttp.ClientSession(connector=connector)
```

### Explicación de las Métricas y Parámetros

*   **`limit` (100)**: Este parámetro dicta el máximo absoluto de conexiones simultáneas globales que la sesión de `aiohttp` mantendrá vivas al mismo tiempo, sin importar el host destino. Si se encolan 150 peticiones, 50 quedarán esperando internamente en la cola de asyncio hasta que un socket se libere. 100 es un estándar sano para clientes que leen diferentes microservicios.
*   **`limit_per_host` (30)**: Extremadamente vital. Limita cuántas de esas 100 conexiones pueden apuntar a *un mismo servidor/dominio* a la vez (ej. `api.ecomarket.com`). Configurar esto protege al servidor de ráfagas destructivas y evita baneos.
*   **`keepalive_timeout` (60.0s)**: Los handshakes de TCP y TLS/SSL consumen tiempo (alta latencia). `keepalive_timeout` le dice a `aiohttp` que no cierre la conexión TCP inmediatamente después de recibir la respuesta, sino que la mantenga abierta por 60 segundos por si llega otra petición al mismo host, re-utilizando el canal y mejorando dramáticamente la velocidad.

Implementando esta capa inteligente mediante la clase **`SmartSession`**, nos aseguramos de escalar el cliente asíncrono responsablemente, monitoreando la contención de red antes de que se convierta en un error en tiempo de ejecución.
