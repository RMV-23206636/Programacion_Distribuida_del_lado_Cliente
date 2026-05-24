"""
CircuitBreaker del lado del cliente para EcoMarket.

Decisiones de diseno:
- Estados: CERRADO, ABIERTO y SEMIABIERTO.
- Umbral: 3 fallos consecutivos.
- Timeout de apertura: 2 segundos en demo, mayor con jitter en produccion.
- Cuentan como fallo: 5xx, timeouts y errores de red.
- No cuentan como fallo: 4xx, CircuitOpenError ni errores locales del cliente.
- Se usa time.monotonic() para evitar el bug de reloj del sistema.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from enum import Enum
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class EstadoCircuito(str, Enum):
    CERRADO = "CERRADO"
    ABIERTO = "ABIERTO"
    SEMIABIERTO = "SEMIABIERTO"


class CircuitOpenError(Exception):
    pass


class HttpError(Exception):
    def __init__(self, status: int, message: str = "") -> None:
        super().__init__(message or f"HTTP {status}")
        self.status = status


class NetworkError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, umbral_fallos: int = 3, timeout_apertura: float = 2.0) -> None:
        self._umbral_fallos = umbral_fallos
        self._timeout_apertura = timeout_apertura
        self._estado = EstadoCircuito.CERRADO
        self._fallos_consecutivos = 0
        self._abierto_desde: float | None = None
        self._lock_semiabierto = asyncio.Lock()

    @property
    def estado(self) -> EstadoCircuito:
        self._revisar_timeout()
        return self._estado

    @property
    def fallos_consecutivos(self) -> int:
        return self._fallos_consecutivos

    def _revisar_timeout(self) -> None:
        if self._estado == EstadoCircuito.ABIERTO and self._abierto_desde is not None:
            if time.monotonic() - self._abierto_desde >= self._timeout_apertura:
                self._estado = EstadoCircuito.SEMIABIERTO

    def _es_fallo_servidor(self, error: Exception) -> bool:
        if isinstance(error, CircuitOpenError):
            return False
        if isinstance(error, (TimeoutError, asyncio.TimeoutError, NetworkError, ConnectionError)):
            return True
        status = getattr(error, "status", None)
        return status is not None and 500 <= int(status) <= 599

    def _registrar_exito(self) -> None:
        self._fallos_consecutivos = 0
        self._estado = EstadoCircuito.CERRADO
        self._abierto_desde = None

    def _registrar_fallo(self) -> None:
        if self._estado == EstadoCircuito.SEMIABIERTO:
            self._abrir()
            return
        self._fallos_consecutivos += 1
        if self._fallos_consecutivos >= self._umbral_fallos:
            self._abrir()

    def _abrir(self) -> None:
        self._estado = EstadoCircuito.ABIERTO
        self._abierto_desde = time.monotonic()

    async def ejecutar(self, fn: Callable[[], T | Awaitable[T]]) -> T:
        estado = self.estado
        if estado == EstadoCircuito.ABIERTO:
            raise CircuitOpenError("Circuito abierto: peticion rechazada sin contactar al servidor")
        if estado == EstadoCircuito.SEMIABIERTO:
            if self._lock_semiabierto.locked():
                raise CircuitOpenError("Circuito semiabierto: ya existe una peticion de prueba")
            async with self._lock_semiabierto:
                return await self._ejecutar_y_registrar(fn)
        return await self._ejecutar_y_registrar(fn)

    async def _ejecutar_y_registrar(self, fn: Callable[[], T | Awaitable[T]]) -> T:
        try:
            resultado = fn()
            if inspect.isawaitable(resultado):
                resultado = await resultado
        except Exception as error:
            if self._es_fallo_servidor(error):
                self._registrar_fallo()
            raise
        self._registrar_exito()
        return resultado
