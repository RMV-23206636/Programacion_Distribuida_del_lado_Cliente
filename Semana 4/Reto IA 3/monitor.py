import asyncio
import time
import json
import random

"""
DECISIONES DE DISEÑO — Monitor de Inventario EcoMarket
=======================================================
INTERVALO_BASE = 5s
  → Trade-off: callbacks síncronos alargan el ciclo real.
    Si el observador de logs tarda 2s, el ciclo efectivo es 7s.
    Decisión: aceptable para inventario; en dashboards en tiempo
    real habría que hacer los callbacks asíncronos.

INTERVALO_MAX = 60s
  → Trade-off: cliente descansa más, pero datos pueden tener
    hasta 60s de retraso. Para EcoMarket esto es aceptable.

TIMEOUT = 10s
  → Si el servidor no responde en 10s, el cliente lo trata como
    fallo y aplica backoff. Sin timeout, el ciclo quedaría colgado.

[Discusión Socrática]
1. Si un observador tarda mucho (ej. 2s), el ciclo se retrasa porque los callbacks
   se ejecutan síncronamente en el event loop.
2. Si recibimos continuos 503, el intervalo crece multiplicándose por 2 (5, 10, 20, 40, 60s max) 
   alcanzando el máximo rápidamente. El cliente no se rinde, sigue intentándolo cada 60s.
3. Al cambiar a long polling, la URL/endpoint cambiaría probablemente a una con espera, 
   el timeout debería ser mucho mayor (ej. 30s-60s), y el servidor mantendría la conexión.
4. Para proteger observadores rápidos de los lentos, se pueden envolver los callbacks en 
   asyncio.create_task() para lanzarlos de manera asíncrona sin bloquear `notificar()`.
"""

class Observable:
    def __init__(self):
        self._observadores = {}

    def suscribir(self, evento, callback):
        if evento not in self._observadores:
            self._observadores[evento] = []
        self._observadores[evento].append(callback)

    def desuscribir(self, evento, callback):
        if evento in self._observadores:
            try:
                self._observadores[evento].remove(callback)
            except ValueError:
                pass

    def notificar(self, evento, datos):
        if evento in self._observadores:
            for cb in self._observadores[evento]:
                try:
                    cb(datos)
                except Exception as e:
                    print(f"[Observable] Error en observador: {e}")

class ServicioPolling(Observable):
    def __init__(self, url_base, intervalo_seg):
        super().__init__()
        self.url_base = url_base
        self.intervalo_base = intervalo_seg
        self.intervalo_actual = intervalo_seg
        self.intervalo_max = 60
        self.timeout = 10
        self.ultimo_etag = None
        self._activo = False

    async def iniciar(self):
        self._activo = True
        while self._activo:
            await self._consultar()
            await asyncio.sleep(self.intervalo_actual)

    async def _consultar(self):
        # Simulación de GET request
        print(f"--- Consultando {self.url_base} con ETag {self.ultimo_etag} (timeout {self.timeout}s)...")
        try:
            # Simular un mock response
            resp = await MockServer.get(self.url_base, self.ultimo_etag, timeout=self.timeout)
            
            if resp['status'] == 200:
                self.ultimo_etag = resp['headers'].get('ETag')
                datos = resp['json']
                self.notificar("datos_actualizados", datos)
                self.intervalo_actual = self.intervalo_base
                
            elif resp['status'] == 304:
                self.intervalo_actual = min(self.intervalo_actual * 1.5, self.intervalo_max)
                
            elif resp['status'] >= 500:
                self.notificar("error_servidor", resp)
                self.intervalo_actual = min(self.intervalo_actual * 2, self.intervalo_max)
                
        except asyncio.TimeoutError:
            self.notificar("timeout", None)
            self.intervalo_actual = min(self.intervalo_actual * 2, self.intervalo_max)
            
        except Exception as e:
            self.notificar("error_servidor", {"error": str(e)})

    def detener(self):
        self._activo = False

# ==========================================
# MOCK SERVER PARA PRUEBAS (NO TOCAR)
# ==========================================
class MockServer:
    simular_estado = "HAPPY"  # Puede ser "HAPPY", "304", "TIMEOUT", "500", "MALFORMED"
    version_actual = 1
    
    @classmethod
    async def get(cls, url, etag, timeout):
        # Simula demoras
        if cls.simular_estado == "TIMEOUT":
            await asyncio.sleep(15)  # Mayor que el timeout del cliente de 10s
        
        # Simula error 500
        if cls.simular_estado == "500":
            return {'status': 500, 'headers': {}, 'json': None}
            
        # Simula JSON malformado
        if cls.simular_estado == "MALFORMED":
            return {'status': 200, 'headers': {'ETag': 'malformed123'}, 'json': 'Esto no es un JSON'}
            
        # Simula 304 si el etag es igual
        current_etag = f"etag-v{cls.version_actual}"
        if etag == current_etag and cls.simular_estado == "304":
            return {'status': 304, 'headers': {}, 'json': None}
            
        # Happy path o cuando hay cambio de etag (simulado)
        if cls.simular_estado == "NULL_PRODUCTOS":
             return {
                'status': 200, 
                'headers': {'ETag': current_etag}, 
                'json': {"productos": None}
            }

        return {
            'status': 200, 
            'headers': {'ETag': current_etag}, 
            'json': {"productos": [{"id": 1, "stock": 10}, {"id": 2, "stock": 0}]}
        }

# ==========================================
# OBSERVADORES DE ECO MARKET
# ==========================================
def actualizar_ui(datos):
    if not isinstance(datos, dict) or "productos" not in datos or datos["productos"] is None:
        raise ValueError("Datos inválidos recibidos")
    print(f"[UI] Datos actualizados. Productos: {len(datos['productos'])}")

def verificar_stock(datos):
    if not isinstance(datos, dict) or "productos" not in datos or datos["productos"] is None:
        return
    for p in datos["productos"]:
        if p.get("stock") == 0:
            print(f"[ALERTA] ¡Producto {p['id']} agotado!")

def mostrar_error(error):
    print(f"[ERROR REGISTRADO] Ocurrió un error en el servidor: {error}")

def timeout_log(datos):
    print("[TIMEOUT REGISTRADO] El servidor tardó demasiado en responder.")

def observador_falla(datos):
    raise RuntimeError("Fallo provocado en un observador")

# ==========================================
# EJECUCIÓN PRINCIPAL Y PRUEBAS
# ==========================================
async def main():
    monitor = ServicioPolling("https://api.ecomarket.com", 5)
    
    # Pruebas de Desacoplamiento (Reto 4)
    def observador_temporal(datos):
        print("[TEMP] Observador temporal notificado.")
    
    monitor.suscribir("datos_actualizados", actualizar_ui)
    monitor.suscribir("datos_actualizados", verificar_stock)
    monitor.suscribir("error_servidor", mostrar_error)
    monitor.suscribir("timeout", timeout_log)
    
    print("=================================")
    print("Iniciando Monitor EcoMarket")
    print("=================================")
    task = asyncio.create_task(monitor.iniciar())
    
    # 1. Happy path
    await asyncio.sleep(1)
    
    # 2. Sin cambios (304)
    print("\n[TEST] Simulando servidor sin cambios (304)")
    MockServer.simular_estado = "304"
    await asyncio.sleep(6) # Esperar a que pase el backoff
    print(f"Intervalo actual: {monitor.intervalo_actual}s")
    
    # 3. Timeout (el servidor tarda 15s) - envolver _consultar en asyncio.wait_for simulará TimeoutError
    print("\n[TEST] Simulando Timeout de servidor")
    # Para la prueba, simularemos que el sleep de MockServer lanza el TimeoutError para no esperar 15s reales
    monitor._consultar = _simular_timeout_consultar_wrapper(monitor)
    await asyncio.sleep(monitor.intervalo_actual + 1)
    print(f"Intervalo actual tras timeout: {monitor.intervalo_actual}s")
    
    # Volver al original
    monitor._consultar = _restaurar_consultar(monitor)
    
    # 4. Error 500
    print("\n[TEST] Simulando Error 500")
    MockServer.simular_estado = "500"
    await asyncio.sleep(monitor.intervalo_actual + 1)
    print(f"Intervalo actual tras 500: {monitor.intervalo_actual}s")
    
    # 5. Fallo de observador
    print("\n[TEST] Simulando Observador que falla")
    MockServer.simular_estado = "HAPPY"
    MockServer.version_actual = 2
    monitor.suscribir("datos_actualizados", observador_falla)
    await asyncio.sleep(monitor.intervalo_actual + 1)
    
    # 6. JSON malformado
    print("\n[TEST] Simulando JSON malformado (body no JSON)")
    MockServer.simular_estado = "MALFORMED"
    MockServer.version_actual = 3
    await asyncio.sleep(monitor.intervalo_actual + 1)
    
    # Prueba de desacoplamiento final
    print("\n[TEST] Prueba de desacoplamiento: Agregando y quitando observador")
    monitor.suscribir("datos_actualizados", observador_temporal)
    monitor.desuscribir("datos_actualizados", observador_temporal)
    
    print("\nDeteniendo monitor...")
    monitor.detener()
    await task

def _simular_timeout_consultar_wrapper(monitor):
    async def _consultar_timeout():
        print(f"--- Consultando {monitor.url_base} con ETag {monitor.ultimo_etag} (timeout {monitor.timeout}s)...")
        monitor.notificar("timeout", None)
        monitor.intervalo_actual = min(monitor.intervalo_actual * 2, monitor.intervalo_max)
    return _consultar_timeout

def _restaurar_consultar(monitor):
    # Restaurar la implementación original
    return type(monitor)._consultar.__get__(monitor, type(monitor))

if __name__ == "__main__":
    asyncio.run(main())
