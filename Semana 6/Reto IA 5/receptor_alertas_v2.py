import asyncio
import httpx
import json
import logging
from typing import Callable, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Observable:
    def __init__(self):
        # type -> list of subscribers
        self._suscriptores: Dict[str, List[Callable]] = {}

    def suscribir(self, evento_tipo: str, callback: Callable):
        if evento_tipo not in self._suscriptores:
            self._suscriptores[evento_tipo] = []
        self._suscriptores[evento_tipo].append(callback)

    def notificar(self, evento_tipo: str, datos: dict):
        if evento_tipo in self._suscriptores:
            for callback in self._suscriptores[evento_tipo]:
                try:
                    callback(datos)
                except Exception as e:
                    logging.error(f"Error en suscriptor al procesar '{evento_tipo}': {e}")


# Composición: ReceptorAlertas TIENE un Observable
class ReceptorAlertas:
    def __init__(self, url: str):
        self.url = url
        self.last_event_id: Optional[str] = None
        self.retry_ms: int = 3000
        self.activo: bool = False
        self.timeout = httpx.Timeout(30.0)
        self._task: Optional[asyncio.Task] = None
        
        # Integración con el patrón Observer
        self.eventos = Observable()

    async def conectar(self):
        self.activo = True
        intentos = 0
        max_intentos = 5

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while self.activo and intentos < max_intentos:
                headers = {"Accept": "text/event-stream"}
                if self.last_event_id:
                    headers["Last-Event-ID"] = self.last_event_id
                
                try:
                    async with client.stream('GET', self.url, headers=headers) as response:
                        if response.status_code == 204:
                            self.activo = False
                            break
                            
                        if response.status_code != 200:
                            intentos += 1
                            await asyncio.sleep(self.retry_ms / 1000.0)
                            continue

                        intentos = 0
                        buffer = {"id": None, "event": "message", "data": ""}
                        
                        async for line in response.aiter_lines():
                            if not self.activo:
                                break
                            
                            line = line.strip()
                            if not line:
                                if buffer["data"]:
                                    self._despachar_evento(buffer)
                                buffer = {"id": None, "event": "message", "data": ""}
                                continue
                                
                            if line.startswith(":"):
                                continue
                                
                            if ":" in line:
                                field, value = line.split(":", 1)
                                value = value.strip()
                                
                                if field == "id":
                                    buffer["id"] = value
                                    self.last_event_id = value
                                elif field == "event":
                                    buffer["event"] = value
                                elif field == "data":
                                    buffer["data"] += value + "\n"
                                elif field == "retry":
                                    if value.isdigit():
                                        self.retry_ms = int(value)

                except Exception as exc:
                    intentos += 1
                
                if self.activo and intentos < max_intentos:
                    await asyncio.sleep(self.retry_ms / 1000.0)

            if intentos >= max_intentos:
                self.activo = False

    def _despachar_evento(self, evento: dict):
        data = evento["data"].strip()
        tipo = evento["event"]
        
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            parsed_data = {"raw_text": data}
            
        # En lugar de hardcodear los if/else, delegamos al Observable
        self.eventos.notificar(tipo, parsed_data)

    def iniciar(self):
        self._task = asyncio.create_task(self.conectar())

    async def detener(self):
        self.activo = False
        if self._task:
            await self._task

# --- Suscriptores (Funciones independientes) ---

def actualizador_precios_ui(datos: dict):
    logging.info(f"[UI] Actualizando tabla simulada -> {datos}")

def alerta_stock_critico(datos: dict):
    logging.warning(f"[ALERTA URGENTE] ⚠️ Stock agotado o crítico: {datos}")

def registrador_auditoria(datos: dict):
    logging.info(f"[AUDITORIA] Registrando evento en base de datos: {datos}")


async def main():
    receptor = ReceptorAlertas("https://sse.dev/test")
    
    # Registro de suscripciones
    receptor.eventos.suscribir("precio-actualizado", actualizador_precios_ui)
    receptor.eventos.suscribir("precio-actualizado", registrador_auditoria)
    receptor.eventos.suscribir("stock-critico", alerta_stock_critico)
    receptor.eventos.suscribir("stock-critico", registrador_auditoria)
    
    receptor.iniciar()
    
    await asyncio.sleep(15)
    await receptor.detener()

if __name__ == "__main__":
    asyncio.run(main())
