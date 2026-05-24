from __future__ import annotations

import asyncio

from circuit_breaker import CircuitBreaker, CircuitOpenError, HttpError
from cliente_robusto import ClienteRobusto, MockEcoMarketServer, TokenManagerDummy


async def assert_raises(expected, coro):
    try:
        await coro
    except expected:
        return
    raise AssertionError(f"Se esperaba {expected.__name__}")


async def main() -> None:
    resultados: list[tuple[str, str]] = []
    servidor = MockEcoMarketServer()
    cb = CircuitBreaker(umbral_fallos=3, timeout_apertura=0.2)
    cliente = ClienteRobusto(servidor, TokenManagerDummy(), cb)

    await cliente.get("/api/inventario")
    resultados.append(("Caso 1 exito en CERRADO", cb.estado.value))

    servidor.modo = "fallo_503"
    for _ in range(3):
        await assert_raises(HttpError, cliente.get("/api/inventario"))
    resultados.append(("Caso 2 5xx abre circuito", cb.estado.value))

    antes = servidor.peticiones_recibidas
    await assert_raises(CircuitOpenError, cliente.get("/api/inventario"))
    assert servidor.peticiones_recibidas == antes
    resultados.append(("Caso 3 abierto no toca servidor", f"{antes}->{servidor.peticiones_recibidas}"))

    await asyncio.sleep(0.25)
    assert cb.estado.value == "SEMIABIERTO"
    servidor.modo = "normal"
    await cliente.get("/api/inventario")
    assert cb.estado.value == "CERRADO" and cb.fallos_consecutivos == 0
    resultados.append(("Caso 4 semiabierto cierra con exito", cb.estado.value))

    servidor.modo = "unauthorized"
    for _ in range(8):
        await assert_raises(HttpError, cliente.get("/api/inventario"))
    assert cb.estado.value == "CERRADO" and cb.fallos_consecutivos == 0
    resultados.append(("Caso 5 401 no cuenta como fallo", f"{cb.estado.value}/{cb.fallos_consecutivos}"))

    servidor.modo = "timeout"
    for _ in range(3):
        await assert_raises(TimeoutError, cliente.get("/api/inventario"))
    assert cb.estado.value == "ABIERTO"
    resultados.append(("Caso 6 timeout abre circuito", cb.estado.value))

    cb2 = CircuitBreaker(umbral_fallos=1, timeout_apertura=0.2)
    servidor2 = MockEcoMarketServer()
    cliente2 = ClienteRobusto(servidor2, TokenManagerDummy(), cb2)
    servidor2.modo = "fallo_503"
    await assert_raises(HttpError, cliente2.get("/api/inventario"))
    await asyncio.sleep(0.25)
    servidor2.modo = "normal"
    respuestas = await asyncio.gather(*(cliente2.get("/api/inventario") for _ in range(3)), return_exceptions=True)
    exitos = sum(1 for r in respuestas if not isinstance(r, Exception))
    rechazadas = sum(1 for r in respuestas if isinstance(r, CircuitOpenError))
    assert exitos == 1 and rechazadas == 2
    resultados.append(("Caso 7 una prueba en SEMIABIERTO", f"exitos={exitos}, rechazadas={rechazadas}"))

    for nombre, observado in resultados:
        print(f"OK - {nombre}: {observado}")


if __name__ == "__main__":
    asyncio.run(main())
