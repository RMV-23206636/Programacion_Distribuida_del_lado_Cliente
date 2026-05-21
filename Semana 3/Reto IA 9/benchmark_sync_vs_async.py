"""
benchmark_sync_vs_async.py - Semana 3, Reto IA 9
Benchmark Comparativo: Cliente Síncrono (requests) vs Asíncrono (aiohttp).

Alumno: Ricardo Matos Vizcarra
Materia: Programación Distribuida del Lado del Cliente
"""

import time
import requests
import asyncio
import aiohttp
import urllib.request
import threading

# Definimos una API publica rápida de testing para no requerir un servidor mock local en el benchmark real
URL_PRUEBA = "https://jsonplaceholder.typicode.com/posts/{}"
TOTAL_PETICIONES = 50

# =======================================================
# IMPLEMENTACION SINCRONA (Librería requests)
# =======================================================
def benchmark_sincrono():
    print(f"\n--- Iniciando Benchmark Síncrono (requests) - {TOTAL_PETICIONES} peticiones ---")
    t0 = time.time()
    
    # Creamos un session para requests para aprovechar connection pooling como minimo
    session = requests.Session()
    
    for i in range(1, TOTAL_PETICIONES + 1):
        url = URL_PRUEBA.format(i)
        response = session.get(url)
        # response.json()  # simular parseo
        
    tiempo_total = time.time() - t0
    print(f"[Requests Síncrono] Tiempo total: {tiempo_total:.3f} segundos")
    return tiempo_total


# =======================================================
# IMPLEMENTACION ASINCRONA (Librería aiohttp)
# =======================================================
async def peticion_async(session, url):
    async with session.get(url) as response:
        await response.read() # Forzar lectura

async def rutina_asincrona():
    t0 = time.time()
    async with aiohttp.ClientSession() as session:
        tareas = []
        for i in range(1, TOTAL_PETICIONES + 1):
            url = URL_PRUEBA.format(i)
            tareas.append(asyncio.create_task(peticion_async(session, url)))
            
        await asyncio.gather(*tareas)
        
    return time.time() - t0

def benchmark_asincrono():
    print(f"\n--- Iniciando Benchmark Asíncrono (aiohttp) - {TOTAL_PETICIONES} peticiones ---")
    tiempo_total = asyncio.run(rutina_asincrona())
    print(f"[Aiohttp Asíncrono] Tiempo total: {tiempo_total:.3f} segundos")
    return tiempo_total


# =======================================================
# EJECUCION Y CONCLUSIONES
# =======================================================
if __name__ == "__main__":
    print("Iniciando Benchmarks...")
    
    # Calentamiento (ignorar primeros tiempos por DNS/TLS handshake cache)
    print("Calentando DNS...")
    requests.get("https://jsonplaceholder.typicode.com/")
    
    t_sync = benchmark_sincrono()
    t_async = benchmark_asincrono()
    
    mejora_porcentual = ((t_sync - t_async) / t_sync) * 100
    mejora_multiplicador = t_sync / t_async
    
    print("\n================ RESULTADOS ==================")
    print(f"| Enfoque     | Tiempo Total | Peticiones/seg |")
    print(f"|-------------|--------------|----------------|")
    print(f"| Síncrono    | {t_sync:.3f} s    | {TOTAL_PETICIONES/t_sync:.1f} req/s     |")
    print(f"| Asíncrono   | {t_async:.3f} s    | {TOTAL_PETICIONES/t_async:.1f} req/s     |")
    print("==============================================")
    
    print(f"\nEl cliente asíncrono fue {mejora_multiplicador:.1f}x veces más rápido.")
    print(f"Ahorro de tiempo: {mejora_porcentual:.1f}%")
    
    print("\nCONCLUSIÓN SOBRE CUÁNDO MIGRAR:")
    print("Se debe migrar a un enfoque asíncrono cuando la aplicación es intensiva en I/O (Input/Output bound), "
          "como es el caso de un cliente HTTP que realiza múltiples peticiones simultáneas, un web scraper, o un "
          "API gateway. Como demuestra el benchmark, al no bloquear el hilo de ejecución esperando las respuestas "
          "de red (Network Latency), el Event Loop de asyncio permite lanzar docenas de peticiones virtualmente al "
          "mismo tiempo. Sin embargo, para scripts lineales o tareas intensivas de CPU (CPU bound), migrar a "
          "asíncrono añade complejidad innecesaria sin mejorar el rendimiento.")
