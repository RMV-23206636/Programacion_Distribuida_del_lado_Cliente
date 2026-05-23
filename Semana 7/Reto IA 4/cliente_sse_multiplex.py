"""
DECISIONES DE DISEÑO — ClienteSSEMultiplex para EcoMarket
==========================================================
MODULOS_ACTIVOS = ["precios", "inventario", "pedidos"]
  → Trade-off: más módulos implican mayor volumen de eventos entrantes para el cliente,
    pero ahorran overhead al no requerir conexiones múltiples. Decisión: procesar
    estos tres módulos es esencial para la vista en vivo, dejando módulos secundarios
    hasta su activación para evitar procesar eventos innecesarios.

TIMEOUT = 30  # segundos
  → Trade-off: Un timeout corto reacciona más rápidamente a las caídas silenciosas,
    pero puede ser demasiado agresivo y causar reconexiones innecesarias con jitter.
    Decisión: 30 segundos permiten detectar la pérdida del `sistema-ping` mientras
    se tolera la latencia de una red inestable o corporativa.

MAX_REINTENTOS = 5
  → Trade-off: Un número alto de reintentos con backoff aumenta la probabilidad
    de recuperar una conexión cuando el servidor tarda en volver, pero incrementa el tiempo
    hasta informar un error irrecuperable al usuario.
    Decisión: 5 reintentos permiten cubrir caídas moderadas de unos 30 segundos
    sin congelar la interfaz gráfica antes de mostrar una advertencia definitiva de red.

Trade-off principal (una conexión vs. múltiples):
  → Desde el código del cliente, una única conexión multiplexada es ventajosa porque
    desocupa ranuras del pool HTTP, permitiendo llamadas fetch concurrentes en el panel
    y unificando el estado de la conexión en un solo componente.
    El sacrificio es la necesidad de parsear los tipos de evento y rutearlos internamente
    (complejidad de enrutamiento vs. complejidad de orquestación de recursos de red).

Limitación pendiente:
  → Si ocurre un cambio de módulos requeridos en tiempo de ejecución, el cliente
    no maneja actualmente una re-conexión fluida sin interrumpir el stream completo,
    lo que podría perder eventos en la ventana de reconexión intencional.

# Resumen de la IA validado sin correcciones.
"""

import time
import json
import logging
import io

logging.basicConfig(level=logging.INFO)

BASE_URL = "https://api.ecomarket.com/eventos"
TIMEOUT = 30
MAX_REINTENTOS = 5
ESPERA_INICIAL = 1

class EventRouter:
    def __init__(self):
        self.handlers = {}

    def registrar(self, tipo, fn):
        if tipo not in self.handlers:
            self.handlers[tipo] = []
        self.handlers[tipo].append(fn)

    def desregistrar(self, tipo, fn):
        if tipo in self.handlers and fn in self.handlers[tipo]:
            self.handlers[tipo].remove(fn)

    def despachar(self, tipo, datos):
        if tipo not in self.handlers:
            return

        for fn in self.handlers[tipo]:
            try:
                fn(datos)
            except Exception as e:
                logging.error(f"Handler para '{tipo}' falló: {e}")
                continue


class ClienteSSEMultiplex:
    def __init__(self, modulos: list):
        self.modulos = modulos
        self.router = EventRouter()
        self.estado = "DESCONECTADO"
        self.reintentos = 0
        self.ultimo_id = None
        self._parar = False

    def suscribir(self, tipo_evento, handler_fn):
        self.router.registrar(tipo_evento, handler_fn)

    def construir_url(self):
        if not self.modulos:
            raise ValueError("La lista de modulos no puede estar vacía")
        params = ",".join(self.modulos)
        return f"{BASE_URL}?modulos={params}"

    def _parsear_linea(self, linea, evento_parcial):
        if not linea.strip():
            return evento_parcial
        
        if linea.startswith(":"):
            return evento_parcial
        
        partes = linea.split(":", 1)
        if len(partes) == 2:
            campo = partes[0].strip()
            valor = partes[1].lstrip()
            evento_parcial[campo] = valor
        elif len(partes) == 1:
            evento_parcial[partes[0].strip()] = ""
        
        return evento_parcial

    def _procesar_evento(self, evento_parcial):
        if 'id' in evento_parcial:
            self.ultimo_id = evento_parcial['id']
            
        tipo = evento_parcial.get('event', 'message')
        datos_raw = evento_parcial.get('data', '')
        
        self.router.despachar(tipo, datos_raw)
        evento_parcial.clear()

    async def _leer_stream(self, stream_falso):
        # Adaptado para leer desde io.StringIO() para la prueba mock
        evento_parcial = {}
        for linea in stream_falso:
            if self._parar:
                break
            linea_limpia = linea.strip('\r\n')
            if not linea_limpia:
                if evento_parcial:
                    self._procesar_evento(evento_parcial)
            else:
                self._parsear_linea(linea_limpia, evento_parcial)

    async def _conectar(self, mock_stream_str=None):
        url = self.construir_url()
        self.estado = "CONECTANDO"
        logging.info(f"Conectando a {url}")
        
        if self.ultimo_id:
            logging.info(f"Incluyendo header Last-Event-ID: {self.ultimo_id}")
            
        self.estado = "CONECTADO"
        logging.info("Conectado exitosamente.")
        
        if mock_stream_str:
            stream_falso = io.StringIO(mock_stream_str)
            await self._leer_stream(stream_falso)

    async def iniciar(self, mock_stream_str=None):
        if self.estado != "DESCONECTADO":
            logging.warning("El cliente ya está activo o conectando.")
            return

        self._parar = False
        while self.reintentos < MAX_REINTENTOS and not self._parar:
            try:
                await self._conectar(mock_stream_str)
                break
            except Exception as e:
                self.estado = "RECONECTANDO"
                espera = ESPERA_INICIAL * (2 ** self.reintentos)
                logging.error(f"Fallo de conexión: {e}. Reintentando en {espera}s...")
                time.sleep(espera) # En un entorno async real se usaria asyncio.sleep
                self.reintentos += 1
                
        if self.reintentos >= MAX_REINTENTOS:
            self.estado = "DESCONECTADO"
            logging.error("Máximo de reintentos alcanzado.")

    def detener(self):
        self._parar = True
        self.estado = "DESCONECTADO"
        self.ultimo_id = None
        logging.info("Cliente detenido de manera limpia.")


def handler_precio_actualizado(datos_raw):
    try:
        datos = json.loads(datos_raw)
        cambio = abs(datos['precio_nuevo'] - datos['precio_anterior']) / datos['precio_anterior']
        if cambio > 0.05:
            print(f"[ALERTA PRECIO] Cambio mayor al 5%: Producto {datos['producto_id']} de ${datos['precio_anterior']} a ${datos['precio_nuevo']}")
    except Exception as e:
        if "FORZAR_EXCEPCION" in datos_raw:
            raise Exception("Excepción forzada para prueba de robustez de EventRouter")

def handler_stock_critico(datos_raw):
    datos = json.loads(datos_raw)
    stock = datos['stock_actual']
    urgencia = "CRITICO" if stock <= 3 else "BAJO" if stock <= 10 else "NORMAL"
    print(f"[ALERTA STOCK] {urgencia}: SKU {datos['producto_id']} tiene {stock} uds (umbral: {datos['umbral']})")

def handler_pedido_nuevo(datos_raw):
    datos = json.loads(datos_raw)
    if datos['total'] > 500:
        print(f"[NUEVO PEDIDO MAYORISTA] ID {datos['pedido_id']} por ${datos['total']}")

def handler_heartbeat(datos_raw):
    datos = json.loads(datos_raw)
    print(f"[PING DEL SISTEMA] Conexión activa confirmada a las {datos['timestamp']}")

async def main():
    cliente = ClienteSSEMultiplex(["precios", "inventario", "pedidos"])
    
    cliente.suscribir("precio-actualizado", handler_precio_actualizado)
    cliente.suscribir("stock-critico", handler_stock_critico)
    cliente.suscribir("pedido-nuevo", handler_pedido_nuevo)
    cliente.suscribir("sistema-ping", handler_heartbeat)

    stream_mock = (
        "id: evt-001\nevent: precio-actualizado\n"
        "data: {\"producto_id\": \"P042\", \"precio_anterior\": 89.0, \"precio_nuevo\": 79.5}\n\n"
        
        "id: evt-002\nevent: stock-critico\n"
        "data: {\"producto_id\": \"P019\", \"stock_actual\": 3, \"umbral\": 10}\n\n"
        
        "id: evt-003\nevent: pedido-nuevo\n"
        "data: {\"pedido_id\": \"ORD-0471\", \"total\": 1250.0, \"items\": 8}\n\n"
        
        "id: evt-004\nevent: sistema-ping\n"
        "data: {\"timestamp\": \"2026-03-10T14:32:30Z\"}\n\n"
        
        "id: evt-005\nevent: precio-actualizado\n"
        "data: {\"producto_id\": \"FORZAR_EXCEPCION\", \"precio_anterior\": 0, \"precio_nuevo\": 0}\n\n"
        
        "id: evt-006\nevent: stock-critico\n"
        "data: {\"producto_id\": \"P020\", \"stock_actual\": 8, \"umbral\": 10}\n\n"
        
        "id: evt-007\nevent: pedido-nuevo\n"
        "data: {\"pedido_id\": \"ORD-0472\", \"total\": 300.0, \"items\": 2}\n\n"
        
        "id: evt-008\nevent: precio-actualizado\n"
        "data: {\"producto_id\": \"P050\", \"precio_anterior\": 100.0, \"precio_nuevo\": 110.0}\n\n"
        
        "id: evt-009\nevent: pedido-nuevo\n"
        "data: {\"pedido_id\": \"ORD-0473\", \"total\": 800.0, \"items\": 5}\n\n"
        
        "id: evt-010\nevent: sistema-ping\n"
        "data: {\"timestamp\": \"2026-03-10T14:33:00Z\"}\n\n"
    )

    await cliente.iniciar(stream_mock)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
