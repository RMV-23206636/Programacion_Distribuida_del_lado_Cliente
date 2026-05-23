import asyncio
import httpx
import json
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReceptorAlertas:
    def __init__(self, url: str):
        self.url = url
        self.last_event_id: Optional[str] = None
        self.retry_ms: int = 3000
        self.activo: bool = False
        self.timeout = httpx.Timeout(30.0)
        self._task: Optional[asyncio.Task] = None

    async def conectar(self):
        self.activo = True
        intentos = 0
        max_intentos = 5

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while self.activo and intentos < max_intentos:
                headers = {"Accept": "text/event-stream"}
                if self.last_event_id:
                    headers["Last-Event-ID"] = self.last_event_id

                logging.info(f"Conectando a {self.url} (Intento {intentos + 1})")
                
                try:
                    async with client.stream('GET', self.url, headers=headers) as response:
                        if response.status_code == 204:
                            logging.info("El servidor respondió 204 No Content. Deteniendo reconexión.")
                            self.activo = False
                            break
                            
                        if response.status_code != 200:
                            logging.warning(f"Error HTTP {response.status_code}. Reintentando en {self.retry_ms} ms...")
                            intentos += 1
                            await asyncio.sleep(self.retry_ms / 1000.0)
                            continue

                        intentos = 0  # Reset de intentos al conectar con éxito
                        logging.info("Conexión SSE establecida con éxito.")
                        
                        buffer = {"id": None, "event": "message", "data": ""}
                        
                        async for line in response.aiter_lines():
                            if not self.activo:
                                break
                            
                            # Parsear línea
                            line = line.strip()
                            
                            if not line:
                                # Línea en blanco -> Fin de mensaje
                                if buffer["data"]:
                                    self._procesar_evento(buffer)
                                # Resetear buffer
                                buffer = {"id": None, "event": "message", "data": ""}
                                continue
                                
                            if line.startswith(":"):
                                # Comentario / Keep-alive
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

                except httpx.RequestError as exc:
                    logging.error(f"Error de red: {exc}")
                    intentos += 1
                except httpx.TimeoutException:
                    logging.warning("Timeout de conexión alcanzado (30s).")
                    intentos += 1
                except Exception as exc:
                    logging.error(f"Excepción inesperada: {exc}")
                    intentos += 1
                
                if self.activo and intentos < max_intentos:
                    logging.info(f"Reconectando en {self.retry_ms} ms...")
                    # Backoff exponencial básico (por simplicidad, limitamos el backoff y usamos retry_ms)
                    await asyncio.sleep(self.retry_ms / 1000.0)

            if intentos >= max_intentos:
                logging.error("Límite máximo de intentos de reconexión alcanzado. Deteniendo cliente.")
                self.activo = False

    def _procesar_evento(self, evento: dict):
        # Eliminar el último salto de línea en data
        data = evento["data"].strip()
        tipo = evento["event"]
        
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            parsed_data = data
            
        logging.info(f"Evento Recibido [ID: {evento['id']}] | Tipo: {tipo}")
        
        try:
            if tipo == "precio-actualizado":
                logging.info(f"-> Actualizar tabla de precios: {parsed_data}")
            elif tipo == "stock-critico":
                logging.warning(f"-> ⚠️ ALERTA: Stock crítico detectado: {parsed_data}")
            else:
                logging.info(f"-> (Evento no manejado: {tipo}) Datos: {parsed_data}")
        except Exception as e:
            logging.error(f"Error al procesar evento: {e}")

    def iniciar(self):
        self._task = asyncio.create_task(self.conectar())

    async def detener(self):
        logging.info("Deteniendo Receptor de Alertas...")
        self.activo = False
        if self._task:
            await self._task
        logging.info("Cliente detenido de forma limpia.")

async def main():
    receptor = ReceptorAlertas("https://sse.dev/test")
    receptor.iniciar()
    
    # Simular la escucha durante 15 segundos antes de detener limpiamente
    await asyncio.sleep(15)
    await receptor.detener()

if __name__ == "__main__":
    asyncio.run(main())
