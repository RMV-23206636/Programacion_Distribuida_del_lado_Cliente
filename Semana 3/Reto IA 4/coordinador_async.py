"""
coordinador_async.py - Semana 3, Reto IA 4
Estrategias de timeout individual, cancelación de tareas, y carga con prioridad.

Alumno: Ricardo Matos Vizcarra
Materia: Programación Distribuida del Lado del Cliente

Implementa:
  1. Timeout individual por petición (asyncio.wait_for / asyncio.timeout)
  2. Cancelación de tareas en grupo cuando falla autenticación (401)
  3. cargar_con_prioridad() usando asyncio.wait(FIRST_COMPLETED)
"""

import asyncio
import aiohttp
import time

BASE_URL = "http://127.0.0.1:4010"
TOKEN = "token-de-prueba-uan"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


# ══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 1: TIMEOUT INDIVIDUAL POR PETICIÓN
# ══════════════════════════════════════════════════════════════════════════════

async def peticion_con_timeout(
    session: aiohttp.ClientSession,
    url: str,
    nombre: str,
    timeout_seg: float
) -> dict:
    """
    Envuelve una petición GET con un timeout individual.
    Si esta petición excede SU propio timeout, lanza asyncio.TimeoutError
    SOLO para esta tarea; las demás peticiones lanzadas en paralelo continúan.

    Uso en gather():
        await asyncio.gather(
            peticion_con_timeout(session, url1, "productos", 5.0),
            peticion_con_timeout(session, url2, "categorias", 3.0),  # ← puede fallar sola
            peticion_con_timeout(session, url3, "perfil", 2.0),
            return_exceptions=True
        )
    """
    try:
        async with asyncio.timeout(timeout_seg):  # Python 3.11+
            async with session.get(url) as response:
                response.raise_for_status()
                datos = await response.json()
                print(f"  ✓ [{nombre}] OK (timeout configurado: {timeout_seg}s)")
                return {"fuente": nombre, "datos": datos}

    except asyncio.TimeoutError:
        print(f"  ✗ [{nombre}] TIMEOUT: superó {timeout_seg}s → las demás continúan")
        raise
    except aiohttp.ClientConnectorError:
        print(f"  ✗ [{nombre}] ERROR DE CONEXIÓN: servidor inalcanzable")
        raise
    except aiohttp.ClientResponseError as e:
        print(f"  ✗ [{nombre}] HTTP {e.status}")
        raise


async def demo_timeout_individual():
    """
    Escenario: /categorias tarda más de su timeout (3 s).
    Resultado esperado:
      - /productos y /perfil completan normalmente
      - /categorias lanza TimeoutError
      - gather(return_exceptions=True) devuelve 2 éxitos + 1 excepción
    """
    print("\n══════ ESTRATEGIA 1: TIMEOUT INDIVIDUAL ══════")
    print("  /productos  → timeout 5 s")
    print("  /categorias → timeout 3 s  (simular delay de 8 s en el servidor)")
    print("  /perfil     → timeout 2 s")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        resultados = await asyncio.gather(
            peticion_con_timeout(session, f"{BASE_URL}/productos",  "productos",  5.0),
            peticion_con_timeout(session, f"{BASE_URL}/categorias", "categorias", 3.0),
            peticion_con_timeout(session, f"{BASE_URL}/perfil",     "perfil",     2.0),
            return_exceptions=True   # ← CRÍTICO
        )

    exitos  = [r for r in resultados if not isinstance(r, Exception)]
    fallos  = [r for r in resultados if isinstance(r, Exception)]
    print(f"\n  Resultado final: {len(exitos)} éxitos, {len(fallos)} fallos")
    print("  → El trabajo útil de las peticiones exitosas NO se perdió.")


# ══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 2: CANCELACIÓN DE TAREAS EN GRUPO
# ══════════════════════════════════════════════════════════════════════════════

async def _cancelar_tareas(tareas: list, razon: str):
    """
    Cancela todas las asyncio.Task pendientes.
    Espera a que procesen la cancelación para evitar resource leaks.
    """
    print(f"\n  ↩ Cancelando tareas pendientes. Razón: {razon}")
    canceladas = 0
    for t in tareas:
        if not t.done():
            t.cancel()
            canceladas += 1
    # Recoger cancelaciones — return_exceptions=True evita que CancelledError
    # se propague y permite que el cleanup ocurra limpiamente.
    await asyncio.gather(*tareas, return_exceptions=True)
    print(f"  ↩ {canceladas} tarea(s) cancelada(s) limpiamente.")


async def demo_cancelacion_en_grupo():
    """
    Escenario: si /perfil responde con 401 (no autorizado),
    cancelar TODAS las demás tareas porque sin autenticación los datos
    obtenidos no son útiles ni seguros de usar.

    Patrón:
        - Crear Tasks explícitas (no usar gather directamente)
        - Iterar con as_completed() para detectar el 401 en cuanto llega
        - Al detectar 401, llamar _cancelar_tareas() sobre las pendientes
    """
    print("\n══════ ESTRATEGIA 2: CANCELACIÓN EN GRUPO ══════")
    print("  Escenario: /perfil devuelve 401 → cancelar todo")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Crear Tasks explícitas para poder cancelarlas por referencia
        tarea_productos  = asyncio.create_task(
            peticion_con_timeout(session, f"{BASE_URL}/productos",  "productos",  10.0)
        )
        tarea_categorias = asyncio.create_task(
            peticion_con_timeout(session, f"{BASE_URL}/categorias", "categorias", 10.0)
        )
        tarea_perfil     = asyncio.create_task(
            peticion_con_timeout(session, f"{BASE_URL}/perfil",     "perfil",     10.0)
        )

        todas = [tarea_productos, tarea_categorias, tarea_perfil]

        # Procesar conforme llegan — detectar 401 lo antes posible
        for tarea_completa in asyncio.as_completed(todas):
            try:
                resultado = await tarea_completa
                print(f"  ✓ Recibido: {resultado.get('fuente', '?')}")

            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    print(f"  ✗ 401 No Autorizado en '{e.request_info.url}'")
                    await _cancelar_tareas(todas, "401 → sesión inválida")
                    break  # No continuar procesando
                else:
                    print(f"  ✗ HTTP {e.status} — continuando con las demás")

            except asyncio.CancelledError:
                # Tarea cancelada por _cancelar_tareas — limpiar sin re-lanzar
                print("  ↩ Tarea cancelada (cleanup OK)")

            except Exception as e:
                print(f"  ✗ Error inesperado: {type(e).__name__}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 3: CARGA CON PRIORIDAD (asyncio.wait)
# ══════════════════════════════════════════════════════════════════════════════

async def cargar_con_prioridad():
    """
    Lanza 4 peticiones simultáneas y procesa resultados conforme llegan.

    Peticiones CRÍTICAS   → productos, perfil
    Peticiones SECUNDARIAS → categorias, notificaciones

    En cuanto ambas críticas completan, se muestra el dashboard parcial
    sin esperar a las secundarias (que se procesan cuando lleguen).

    Esto mejora la latencia percibida: el usuario ve datos útiles más rápido.
    """
    print("\n══════ ESTRATEGIA 3: CARGA CON PRIORIDAD (asyncio.wait) ══════")
    print("  Críticas:    /productos, /perfil")
    print("  Secundarias: /categorias, /notificaciones")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Crear un set de Tasks para asyncio.wait
        tareas = {
            asyncio.create_task(
                peticion_con_timeout(session, f"{BASE_URL}/productos",      "productos",      10.0)
            ),
            asyncio.create_task(
                peticion_con_timeout(session, f"{BASE_URL}/categorias",     "categorias",     10.0)
            ),
            asyncio.create_task(
                peticion_con_timeout(session, f"{BASE_URL}/perfil",         "perfil",         10.0)
            ),
            asyncio.create_task(
                peticion_con_timeout(session, f"{BASE_URL}/notificaciones", "notificaciones", 10.0)
            ),
        }

        datos_obtenidos    = {}
        dashboard_mostrado = False
        pendientes         = tareas

        while pendientes:
            # FIRST_COMPLETED: retorna cuando cualquier tarea termine
            completadas, pendientes = await asyncio.wait(
                pendientes,
                return_when=asyncio.FIRST_COMPLETED
            )

            for t in completadas:
                try:
                    resultado = t.result()
                    nombre = resultado.get("fuente", "?")
                    datos_obtenidos[nombre] = resultado["datos"]
                    print(f"  ✓ Llegó: {nombre}")
                except Exception as e:
                    print(f"  ✗ Error en tarea: {type(e).__name__}: {e}")

            # ¿Ya tenemos los datos críticos?
            criticos_listos = "productos" in datos_obtenidos and "perfil" in datos_obtenidos
            if not dashboard_mostrado and criticos_listos:
                print("\n  ★ DASHBOARD PARCIAL DISPONIBLE")
                print(f"    Productos cargados: ✓")
                print(f"    Perfil cargado:     ✓")
                n_pendientes = len(pendientes)
                print(f"    Aún esperando {n_pendientes} fuente(s) secundaria(s)...")
                dashboard_mostrado = True

    print(f"\n  Dashboard completo. Fuentes cargadas: {list(datos_obtenidos.keys())}")


# ══════════════════════════════════════════════════════════════════════════════
# LOG DE COMPORTAMIENTO (generado durante las pruebas)
# ══════════════════════════════════════════════════════════════════════════════

"""
SALIDA ESPERADA AL EJECUTAR (servidor mock con delays configurados):

=== RETO IA 4: TIMEOUTS Y CANCELACIÓN ===

══════ ESTRATEGIA 1: TIMEOUT INDIVIDUAL ══════
  /productos  → timeout 5 s
  /categorias → timeout 3 s  (simular delay de 8 s en el servidor)
  /perfil     → timeout 2 s
  ✓ [productos] OK (timeout configurado: 5.0s)
  ✗ [categorias] HTTP 404
  ✗ [perfil] HTTP 404

  Resultado final: 1 éxitos, 2 fallos
  → El trabajo útil de las peticiones exitosas NO se perdió.

══════ ESTRATEGIA 2: CANCELACIÓN EN GRUPO ══════
  Escenario: /perfil devuelve 401 → cancelar todo
  ✓ [productos] OK (timeout configurado: 10.0s)
  ✓ Recibido: productos
  ✗ [categorias] HTTP 404
  ✗ HTTP 404 — continuando con las demás
  ✗ [perfil] HTTP 404
  ✗ HTTP 404 — continuando con las demás

══════ ESTRATEGIA 3: CARGA CON PRIORIDAD (asyncio.wait) ══════
  Críticas:    /productos, /perfil
  Secundarias: /categorias, /notificaciones
  ✓ [productos] OK (timeout configurado: 10.0s)
  ✓ Llegó: productos
  ✗ [categorias] HTTP 404
  ✗ Error en tarea: ClientResponseError: 404, message='Not Found', url='http://127.0.0.1:4010/categorias'
  ✗ [perfil] HTTP 404
  ✗ Error en tarea: ClientResponseError: 404, message='Not Found', url='http://127.0.0.1:4010/perfil'
  ✗ [notificaciones] HTTP 404
  ✗ Error en tarea: ClientResponseError: 404, message='Not Found', url='http://127.0.0.1:4010/notificaciones'

  Dashboard completo. Fuentes cargadas: ['productos']

=== FIN DE DEMOSTRACIÓN ===
"""


# ══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n=== RETO IA 4: TIMEOUTS Y CANCELACIÓN ===")
    asyncio.run(demo_timeout_individual())
    asyncio.run(demo_cancelacion_en_grupo())
    asyncio.run(cargar_con_prioridad())
    print("\n=== FIN DE DEMOSTRACIÓN ===")
