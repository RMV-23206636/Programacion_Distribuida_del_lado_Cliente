"""
comparacion_coordinacion.py - Semana 3, Reto IA 7
Comparador de Estrategias de Coordinación en asyncio.

Alumno: Ricardo Matos Vizcarra
Materia: Programación Distribuida del Lado del Cliente

Implementa y mide 4 estrategias de coordinación:
1. asyncio.gather()
2. asyncio.wait(return_when=FIRST_COMPLETED)
3. asyncio.as_completed()
4. asyncio.wait(return_when=FIRST_EXCEPTION)
"""

import asyncio
import time
import random

# Simulación de llamadas a API
async def fetch_data(name: str, delay: float, fail: bool = False) -> str:
    print(f"[{name}] Iniciando peticion (delay simulado: {delay:.1f}s)...")
    await asyncio.sleep(delay)
    if fail:
        print(f"[{name}] ERROR!")
        raise ValueError(f"Error simulado en {name}")
    print(f"[{name}] Completado.")
    return f"Datos de {name}"

async def estrategia_1_gather(tareas_config):
    print("\n--- Estrategia 1: asyncio.gather() ---")
    t0 = time.time()
    
    tareas = [fetch_data(name, delay, fail) for name, delay, fail in tareas_config]
    
    try:
        # return_exceptions=False por defecto. Si una falla, lanza la excepción y aborta el await
        resultados = await asyncio.gather(*tareas)
        print(f"Resultados: {resultados}")
    except Exception as e:
        print(f"Excepcion capturada en gather: {e}")
        
    print(f"Tiempo total gather: {time.time() - t0:.2f}s")

async def estrategia_2_wait_first_completed(tareas_config):
    print("\n--- Estrategia 2: asyncio.wait(FIRST_COMPLETED) ---")
    t0 = time.time()
    
    tareas = [asyncio.create_task(fetch_data(name, delay, fail)) for name, delay, fail in tareas_config]
    pendientes = set(tareas)
    
    while pendientes:
        hechas, pendientes = await asyncio.wait(pendientes, return_when=asyncio.FIRST_COMPLETED)
        for tarea in hechas:
            try:
                res = tarea.result()
                print(f"Recibido parcial: {res}")
            except Exception as e:
                print(f"Recibido parcial con error: {e}")
                
    print(f"Tiempo total wait(FIRST_COMPLETED): {time.time() - t0:.2f}s")

async def estrategia_3_as_completed(tareas_config):
    print("\n--- Estrategia 3: asyncio.as_completed() ---")
    t0 = time.time()
    
    tareas = [fetch_data(name, delay, fail) for name, delay, fail in tareas_config]
    
    for coroutine in asyncio.as_completed(tareas):
        try:
            res = await coroutine
            print(f"Recibido al instante: {res}")
        except Exception as e:
            print(f"Recibido error al instante: {e}")
            
    print(f"Tiempo total as_completed(): {time.time() - t0:.2f}s")

async def estrategia_4_wait_first_exception(tareas_config):
    print("\n--- Estrategia 4: asyncio.wait(FIRST_EXCEPTION) ---")
    t0 = time.time()
    
    tareas = [asyncio.create_task(fetch_data(name, delay, fail)) for name, delay, fail in tareas_config]
    pendientes = set(tareas)
    
    try:
        hechas, pendientes = await asyncio.wait(pendientes, return_when=asyncio.FIRST_EXCEPTION)
        
        # Revisamos si alguna fallo
        for tarea in hechas:
            if tarea.exception():
                print(f"Se detuvo por excepcion: {tarea.exception()}")
                # Cancelar las pendientes si hay un error
                for p in pendientes:
                    p.cancel()
                print("Tareas pendientes canceladas.")
                break
        else:
            print("Todas completaron sin excepciones.")
            
    except Exception as e:
         print(f"Excepcion: {e}")
            
    print(f"Tiempo total wait(FIRST_EXCEPTION): {time.time() - t0:.2f}s")

async def main():
    # Configuracion: nombre, delay, falla
    tareas_exitosas = [
        ("productos", 1.0, False),
        ("categorias", 0.5, False),
        ("perfil", 1.5, False)
    ]
    
    tareas_con_fallo = [
        ("productos", 1.0, False),
        ("categorias", 0.5, True), # Falla rapido
        ("perfil", 1.5, False)
    ]

    print("================== ESCENARIO: SIN ERRORES ==================")
    await estrategia_1_gather(tareas_exitosas)
    await estrategia_2_wait_first_completed(tareas_exitosas)
    await estrategia_3_as_completed(tareas_exitosas)
    await estrategia_4_wait_first_exception(tareas_exitosas)
    
    print("\n\n================== ESCENARIO: CON UN ERROR ==================")
    await estrategia_1_gather(tareas_con_fallo)
    await estrategia_2_wait_first_completed(tareas_con_fallo)
    await estrategia_3_as_completed(tareas_con_fallo)
    await estrategia_4_wait_first_exception(tareas_con_fallo)

if __name__ == "__main__":
    asyncio.run(main())
