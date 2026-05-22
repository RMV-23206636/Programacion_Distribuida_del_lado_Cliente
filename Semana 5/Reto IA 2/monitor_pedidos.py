import asyncio
import random

class Observable:
    def __init__(self):
        self._observadores = []

    def suscribir(self, observador):
        if observador not in self._observadores:
            self._observadores.append(observador)

    def desuscribir(self, observador):
        if observador in self._observadores:
            self._observadores.remove(observador)

    def _notificar(self, datos):
        for obs in self._observadores:
            try:
                obs.actualizar(datos)
            except Exception as e:
                print(f"Error en observador: {e}")

class Observador:
    def actualizar(self, datos):
        pass

class ObservadorPedidosUI(Observador):
    def actualizar(self, pedidos):
        print("\n[UI] --- Lista de Pedidos ---")
        for p in pedidos:
            print(f"  > Pedido {p['id']}: {p['cliente']} | Status: {p['status']}")

class ObservadorPedidosCriticos(Observador):
    def actualizar(self, pedidos):
        for p in pedidos:
            if p.get('status') == 'RETRASADO':
                print(f"[ALERTA] ⚠️ El pedido {p['id']} está RETRASADO.")

class MonitorPedidos(Observable):
    def __init__(self, base_url, sesion_http):
        super().__init__()
        self.base_url = base_url
        self.sesion = sesion_http
        self.ejecutando = False
        self.intervalo_actual = 5
        self.intervalo_base = 5
        self.intervalo_max = 60
        self.ultimo_estado = None

    async def _consultar_pedidos(self):
        try:
            # Asumiendo aiohttp en el entorno real
            import aiohttp
            # GET a /pedidos con timeout
            async with self.sesion.get(f"{self.base_url}/pedidos", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    # Manejo seguro si "pedidos" es null
                    if "pedidos" in data and data["pedidos"] is not None:
                        return data["pedidos"]
                    return None
                elif response.status == 304:
                    return "NOT_MODIFIED"
                elif response.status >= 500:
                    print(f"[Monitor] Error 5xx del servidor. Intentaremos de nuevo.")
                    return "SERVER_ERROR"
                elif response.status >= 400:
                    print(f"[Monitor] Error 4xx del cliente: {response.status}. No se reintentará directamente la misma petición defectuosa si fuera un post, pero es un GET.")
                    return None
        except asyncio.TimeoutError:
            print("[Monitor] Timeout: El servidor tardó demasiado en responder.")
            return "NETWORK_ERROR"
        except Exception as e:
            # Captura cualquier error de conexión para no crashear
            print(f"[Monitor] Error de red inesperado: {e}")
            return "NETWORK_ERROR"

    async def iniciar(self):
        self.ejecutando = True
        print("Monitor de pedidos iniciado...")
        
        while self.ejecutando:
            datos_nuevos = await self._consultar_pedidos()
            
            if datos_nuevos == "NOT_MODIFIED":
                # Backoff adaptativo
                self.intervalo_actual = min(self.intervalo_actual * 2, self.intervalo_max)
            elif datos_nuevos in ("SERVER_ERROR", "NETWORK_ERROR"):
                # Backoff ante error (con jitter para resiliencia avanzada)
                base = min(self.intervalo_actual * 2, self.intervalo_max)
                self.intervalo_actual = random.uniform(base/2, base)
            elif datos_nuevos is not None:
                # Éxito y hay respuesta 200
                self.intervalo_actual = self.intervalo_base
                # Comparamos si cambió
                if datos_nuevos != self.ultimo_estado:
                    self._notificar(datos_nuevos)
                    self.ultimo_estado = datos_nuevos
            
            # Sleep NO bloqueante (asyncio.sleep)
            await asyncio.sleep(self.intervalo_actual)

    def detener(self):
        self.ejecutando = False
        print("Monitor de pedidos detenido suavemente.")

# --- Simulación de uso para validación local ---
async def main():
    class DummySession:
        class DummyResponse:
            def __init__(self, status):
                self.status = status
            async def json(self):
                return {
                    "pedidos": [
                        {"id": "P001", "cliente": "Ana", "total": 450.00, "status": "PENDIENTE"},
                        {"id": "P002", "cliente": "Carlos", "total": 120.50, "status": "RETRASADO"}
                    ]
                }
            async def __aenter__(self): return self
            async def __aexit__(self, exc_type, exc, tb): pass

        def get(self, url, timeout):
            return self.DummyResponse(200)

    monitor = MonitorPedidos("http://api.ecomarket.local", DummySession())
    ui = ObservadorPedidosUI()
    alertas = ObservadorPedidosCriticos()
    
    monitor.suscribir(ui)
    monitor.suscribir(alertas)
    
    task = asyncio.create_task(monitor.iniciar())
    await asyncio.sleep(2)  # Dejar que el ciclo procese
    monitor.detener()
    await task

if __name__ == "__main__":
    asyncio.run(main())
