"""
cliente_async_ecomarket.py - Semana 3, Reto IA 3
Migración del cliente síncrono (requests) al asíncrono (aiohttp).

Alumno: Ricardo Matos Vizcarra
Materia: Programación Distribuida del Lado del Cliente

Cambios respecto a Semana 2:
  - Todas las funciones son async def
  - Se usa aiohttp en lugar de requests
  - La sesión se pasa como parámetro (una sola por bloque de operaciones)
  - Se agrega cargar_dashboard() que lanza 3 peticiones en paralelo
  - Se mide tiempo síncono vs asíncrono
"""

import asyncio
import aiohttp
import time

# Reutilizamos los validadores de Semana 2 sin modificarlos
from validadores import validar_producto, validar_lista_productos

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:3000/api"
TOKEN = "token-de-prueba-uan"
TIMEOUT_POR_PETICION = aiohttp.ClientTimeout(total=10)


# ─── Excepciones personalizadas (iguales a Semana 2) ─────────────────────────
class EcoMarketError(Exception):
    """Error base para la API de EcoMarket."""
    pass

class ValidationError(EcoMarketError):
    """Error de validación en la respuesta del servidor."""
    pass

class ServerError(EcoMarketError):
    """Error 5xx del servidor."""
    pass

class NotFoundError(EcoMarketError):
    """Recurso no encontrado (404)."""
    pass


# ─── Helper: verificar respuesta HTTP ─────────────────────────────────────────
async def _verificar_respuesta(response: aiohttp.ClientResponse) -> aiohttp.ClientResponse:
    """Misma lógica de Semana 2, ahora asíncrona."""
    if response.status >= 500:
        raise ServerError(f"Error del servidor: {response.status}")
    if response.status == 404:
        raise NotFoundError(f"Recurso no encontrado: {response.url}")
    if response.status >= 400:
        raise ValidationError(f"Error de cliente: {response.status}")

    content_type = response.headers.get('Content-Type', '')
    if 'application/json' not in content_type and response.status != 204:
        raise ValidationError(f"Respuesta no es JSON: {content_type}")

    return response


# ─── CRUD asíncrono ───────────────────────────────────────────────────────────

async def listar_productos(session: aiohttp.ClientSession, categoria: str = None) -> list:
    """
    GET /productos - Lista todos los productos.
    Parámetro opcional 'categoria' para filtrar.
    """
    params = {}
    if categoria:
        params['categoria'] = categoria

    async with session.get(f"{BASE_URL}/productos", params=params) as response:
        await _verificar_respuesta(response)
        datos = await response.json()
        return validar_lista_productos(datos)


async def obtener_producto(session: aiohttp.ClientSession, producto_id: int) -> dict:
    """
    GET /productos/{id} - Obtiene un producto específico.
    """
    async with session.get(f"{BASE_URL}/productos/{producto_id}") as response:
        await _verificar_respuesta(response)
        datos = await response.json()
        return validar_producto(datos)


async def crear_producto(session: aiohttp.ClientSession, datos: dict) -> dict:
    """
    POST /productos - Crea un nuevo producto.
    """
    async with session.post(f"{BASE_URL}/productos", json=datos) as response:
        await _verificar_respuesta(response)
        return await response.json()


async def actualizar_producto_total(session: aiohttp.ClientSession, producto_id: int, datos: dict) -> dict:
    """
    PUT /productos/{id} - Reemplaza completamente un producto.
    """
    async with session.put(f"{BASE_URL}/productos/{producto_id}", json=datos) as response:
        await _verificar_respuesta(response)
        return await response.json()


async def actualizar_producto_parcial(session: aiohttp.ClientSession, producto_id: int, campos: dict) -> dict:
    """
    PATCH /productos/{id} - Actualiza campos específicos de un producto.
    """
    async with session.patch(f"{BASE_URL}/productos/{producto_id}", json=campos) as response:
        await _verificar_respuesta(response)
        return await response.json()


async def eliminar_producto(session: aiohttp.ClientSession, producto_id: int) -> bool:
    """
    DELETE /productos/{id} - Elimina un producto.
    Retorna True si se eliminó correctamente (204).
    """
    async with session.delete(f"{BASE_URL}/productos/{producto_id}") as response:
        if response.status == 204:
            return True
        await _verificar_respuesta(response)
        return False


async def obtener_categorias(session: aiohttp.ClientSession) -> list:
    """GET /categorias - Lista todas las categorías disponibles."""
    async with session.get(f"{BASE_URL}/categorias") as response:
        await _verificar_respuesta(response)
        return await response.json()


async def obtener_perfil(session: aiohttp.ClientSession) -> dict:
    """GET /perfil - Obtiene el perfil del usuario autenticado."""
    async with session.get(f"{BASE_URL}/perfil") as response:
        await _verificar_respuesta(response)
        return await response.json()


# ─── Procesador de resultados de gather ───────────────────────────────────────

def _procesar_resultados(nombres: list, resultados: list) -> dict:
    """
    Separa los resultados exitosos de las excepciones de un gather con return_exceptions=True.
    Retorna un dict con 'datos' y 'errores'.
    """
    datos = {}
    errores = {}
    for nombre, resultado in zip(nombres, resultados):
        if isinstance(resultado, Exception):
            errores[nombre] = str(resultado)
            print(f"  ⚠ Error en '{nombre}': {resultado}")
        else:
            datos[nombre] = resultado
            print(f"  ✓ '{nombre}' cargado correctamente")
    return {'datos': datos, 'errores': errores}


# ─── Dashboard: 3 peticiones en paralelo ──────────────────────────────────────

async def cargar_dashboard() -> dict:
    """
    Carga productos, categorías y perfil de usuario en paralelo.
    Usa una sola ClientSession y return_exceptions=True para que
    el fallo de una petición no descarte las demás.
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=TIMEOUT_POR_PETICION
    ) as session:
        print("[Dashboard] Lanzando 3 peticiones en paralelo...")
        t_inicio = time.perf_counter()

        resultados = await asyncio.gather(
            listar_productos(session),
            obtener_categorias(session),
            obtener_perfil(session),
            return_exceptions=True   # CRÍTICO: no perder trabajo si una falla
        )

        t_total = (time.perf_counter() - t_inicio) * 1000
        print(f"[Dashboard] Completado en {t_total:.0f} ms")

        return _procesar_resultados(
            ['productos', 'categorias', 'perfil'],
            resultados
        )


# ─── Creación masiva con semáforo ─────────────────────────────────────────────

async def crear_multiples_productos(lista_productos: list, max_concurrentes: int = 5) -> tuple:
    """
    Crea múltiples productos en paralelo, limitando la concurrencia con un semáforo.
    Retorna: (productos_creados, productos_fallidos)
    """
    semaforo = asyncio.Semaphore(max_concurrentes)
    headers = {"Authorization": f"Bearer {TOKEN}"}

    async def crear_con_limite(session, datos, indice):
        async with semaforo:
            print(f"  [Creando] Producto {indice + 1}/{len(lista_productos)}: {datos.get('nombre', '?')}")
            return await crear_producto(session, datos)

    async with aiohttp.ClientSession(headers=headers, timeout=TIMEOUT_POR_PETICION) as session:
        tareas = [
            crear_con_limite(session, datos, i)
            for i, datos in enumerate(lista_productos)
        ]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

    creados = [r for r in resultados if not isinstance(r, Exception)]
    fallidos = [(lista_productos[i], str(r)) for i, r in enumerate(resultados) if isinstance(r, Exception)]
    return creados, fallidos


# ─── Medición: síncrono vs asíncrono ─────────────────────────────────────────

def simular_sincrono():
    """
    Simula 3 peticiones secuenciales (síncrono) con delay de 500ms cada una.
    Representa el comportamiento del cliente de Semana 2.
    """
    import requests
    tiempos = []
    urls = [
        f"{BASE_URL}/productos",
        f"{BASE_URL}/categorias",
        f"{BASE_URL}/perfil",
    ]
    headers = {"Authorization": f"Bearer {TOKEN}"}
    for url in urls:
        t = time.perf_counter()
        try:
            requests.get(url, headers=headers, timeout=10)
        except Exception:
            pass
        tiempos.append((time.perf_counter() - t) * 1000)
    return sum(tiempos)


async def benchmark():
    """Compara tiempo síncrono vs asíncrono para cargar el dashboard."""
    print("\n=== BENCHMARK: Síncrono vs. Asíncrono ===")

    # Asíncrono
    t_inicio = time.perf_counter()
    resultado = await cargar_dashboard()
    t_async = (time.perf_counter() - t_inicio) * 1000

    print(f"\nResultados del benchmark:")
    print(f"  Asíncrono (gather):  {t_async:.0f} ms")
    print(f"  Datos cargados:      {list(resultado['datos'].keys())}")
    if resultado['errores']:
        print(f"  Errores:             {resultado['errores']}")
    print("\nNota: El síncrono tomaría aprox. 3× el tiempo de una sola petición")
    print("      porque hace las 3 peticiones de forma secuencial.")


# ─── Punto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(benchmark())
