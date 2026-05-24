from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable

from circuit_breaker import CircuitBreaker, CircuitOpenError, HttpError, NetworkError


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {message}")


class TokenManagerDummy:
    def __init__(self) -> None:
        self._access_token = "access-token-demo"
        self.refresh_count = 0

    async def get_access_token(self) -> str:
        return self._access_token

    async def refresh_access_token(self) -> str:
        self.refresh_count += 1
        self._access_token = f"access-token-refresh-{self.refresh_count}"
        return self._access_token


class MockEcoMarketServer:
    def __init__(self) -> None:
        self.modo = "normal"
        self.peticiones_recibidas = 0

    async def request(self, endpoint: str, token: str) -> dict[str, Any]:
        self.peticiones_recibidas += 1
        await asyncio.sleep(0.03)
        if self.modo == "normal":
            return {"endpoint": endpoint, "estado": "ok", "stock": 42}
        if self.modo == "fallo_503":
            raise HttpError(503, "Service Unavailable")
        if self.modo == "unauthorized":
            raise HttpError(401, "Unauthorized")
        if self.modo == "timeout":
            raise TimeoutError("Timeout esperando respuesta del servidor")
        if self.modo == "network":
            raise NetworkError("No se pudo establecer conexion")
        raise ValueError(f"Modo no soportado: {self.modo}")


class ClienteRobusto:
    def __init__(self, servidor: MockEcoMarketServer, token_manager: TokenManagerDummy, circuit_breaker: CircuitBreaker) -> None:
        self.servidor = servidor
        self.token_manager = token_manager
        self.circuit_breaker = circuit_breaker
        self._listeners: list[Callable[[str], None]] = []

    def on_estado_circuito(self, listener: Callable[[str], None]) -> None:
        self._listeners.append(listener)

    def _notificar_estado(self) -> None:
        for listener in self._listeners:
            listener(self.circuit_breaker.estado.value)

    async def get(self, endpoint: str) -> dict[str, Any]:
        token = await self.token_manager.get_access_token()
        estado_antes = self.circuit_breaker.estado

        async def operacion() -> dict[str, Any]:
            return await self.servidor.request(endpoint, token)

        try:
            return await self.circuit_breaker.ejecutar(operacion)
        finally:
            if self.circuit_breaker.estado != estado_antes:
                self._notificar_estado()


async def demo_resiliencia() -> None:
    servidor = MockEcoMarketServer()
    cliente = ClienteRobusto(servidor, TokenManagerDummy(), CircuitBreaker(umbral_fallos=3, timeout_apertura=2.0))
    cliente.on_estado_circuito(lambda estado: log(f"UI notificada: circuito -> {estado}"))

    log("FASE 1 normal: 3 peticiones exitosas")
    for i in range(1, 4):
        respuesta = await cliente.get("/api/inventario")
        log(f"normal #{i}: estado={cliente.circuit_breaker.estado.value} respuesta={respuesta} servidor={servidor.peticiones_recibidas}")

    log("FASE 2 fallo_503: el breaker registra fallos y abre el circuito")
    servidor.modo = "fallo_503"
    for i in range(1, 5):
        try:
            await cliente.get("/api/inventario")
        except Exception as error:
            log(f"fallo #{i}: {type(error).__name__} estado={cliente.circuit_breaker.estado.value} fallos={cliente.circuit_breaker.fallos_consecutivos} servidor={servidor.peticiones_recibidas}")

    log("FASE 3 abierto: peticion rechazada localmente, contador del servidor no aumenta")
    antes = servidor.peticiones_recibidas
    try:
        await cliente.get("/api/inventario")
    except CircuitOpenError as error:
        log(f"fail-fast: {error} servidor_antes={antes} servidor_despues={servidor.peticiones_recibidas}")

    log("FASE 4 recuperacion: espera timeout, pasa a SEMIABIERTO y cierra con exito")
    await asyncio.sleep(2.1)
    log(f"despues del timeout: estado={cliente.circuit_breaker.estado.value}")
    servidor.modo = "normal"
    respuesta = await cliente.get("/api/inventario")
    log(f"prueba semiabierta exitosa: estado={cliente.circuit_breaker.estado.value} fallos={cliente.circuit_breaker.fallos_consecutivos} respuesta={respuesta}")
    log(f"FIN demo: total_peticiones_servidor={servidor.peticiones_recibidas}")


if __name__ == "__main__":
    asyncio.run(demo_resiliencia())
