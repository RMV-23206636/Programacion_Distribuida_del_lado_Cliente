"""
smart_session.py - Semana 3, Reto IA 10
Diseñador de Pool de Conexiones Inteligente.

Alumno: Ricardo Matos Vizcarra
Materia: Programación Distribuida del Lado del Cliente
"""

import asyncio
import aiohttp
import time
import socket

class SmartSession:
    """
    Wrapper inteligente sobre aiohttp.ClientSession que maneja un pool
    de conexiones optimizado (TCPConnector) y expone métricas de uso.
    """
    
    def __init__(self, limit=100, limit_per_host=20, keepalive_timeout=30.0):
        # Configuramos el TCPConnector para optimizar el pool
        self.connector = aiohttp.TCPConnector(
            limit=limit,                 # Maximas conexiones concurrentes totales
            limit_per_host=limit_per_host, # Maximas conexiones al mismo host (DNS)
            keepalive_timeout=keepalive_timeout, # Tiempo para reusar conexion TCP (evita slow-start)
            enable_cleanup_closed=True,  # Libera memoria de conexiones forzosamente cerradas
            family=socket.AF_INET        # Forzar IPv4 si sabemos que el host no tiene IPv6 bien configurado
        )
        
        self.session = None
        self._total_requests = 0
        self._failed_requests = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(connector=self.connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get(self, url, **kwargs):
        self._total_requests += 1
        try:
            async with self.session.get(url, **kwargs) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            self._failed_requests += 1
            raise e
            
    def get_metrics(self):
        """Monitorea el estado de la sesión y el pool."""
        return {
            "total_requests_made": self._total_requests,
            "failed_requests": self._failed_requests,
            "connector_limit": self.connector.limit,
            "connector_limit_per_host": self.connector.limit_per_host,
            "closed": self.session.closed if self.session else True
        }

# --- Benchmark para probar la eficacia del Pool ---

async def test_smart_pool():
    print("Iniciando test del SmartSession Pool...")
    url = "https://httpbin.org/get"
    num_requests = 30
    
    # Usando nuestro SmartSession
    t0 = time.time()
    async with SmartSession(limit=50, limit_per_host=10) as smart_client:
        tareas = [smart_client.get(url) for _ in range(num_requests)]
        await asyncio.gather(*tareas, return_exceptions=True)
        
        metrics = smart_client.get_metrics()
        
    t_smart = time.time() - t0
    print(f"[SmartSession] Tiempo: {t_smart:.3f}s. Métricas: {metrics}")
    
    # Usando session cruda (sin optimizar explícitamente, default settings)
    t0 = time.time()
    async with aiohttp.ClientSession() as normal_client:
        async def fetch(c, u):
            async with c.get(u) as r:
                return await r.text()
                
        tareas = [fetch(normal_client, url) for _ in range(num_requests)]
        await asyncio.gather(*tareas, return_exceptions=True)
        
    t_normal = time.time() - t0
    print(f"[Aiohttp Default] Tiempo: {t_normal:.3f}s.")
    print("Nota: Para payloads pequeños las optimizaciones del pool son visibles principalmente bajo altas cargas y conexiones TLS lentas.")

if __name__ == "__main__":
    asyncio.run(test_smart_pool())
