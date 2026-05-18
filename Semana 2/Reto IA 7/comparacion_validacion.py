"""
Módulo: comparacion_validacion.py
Descripción: Evaluación de rendimiento y legibilidad de 3 estrategias de validación
             para el modelo Producto de EcoMarket.
Requisitos: pip install pydantic jsonschema
"""

import time
from typing import List, Optional
from pydantic import BaseModel, Field, PositiveFloat, NonNegativeInt
from jsonschema import validate, ValidationError

# ==========================================
# 0. CONFIGURACIÓN DE DATOS DE PRUEBA
# ==========================================

# Estructura base de un producto válido
producto_base = {
    "id": 101,
    "nombre": "Manzanas Orgánicas",
    "precio": 45.50,
    "stock": 120,
    "detalles": {"origen": "Granja Norte", "organico": True},
    "etiquetas": ["fruta", "fresco"]
}

# Generamos una lista de 1000 productos para el benchmark
# Mezclamos un 95% de productos válidos y un 5% de inválidos para simular un escenario real
datos_benchmark = []
for i in range(1000):
    p = producto_base.copy()
    p["id"] = i
    if i % 20 == 0:  # Cada 20 productos, metemos uno con error de tipo
        p["precio"] = -10.0  # Precio inválido
    datos_benchmark.append(p)


# ==========================================
# 1. ESTRATEGIA: VALIDACIÓN MANUAL
# ==========================================
def validar_manual(data) -> bool:
    if not isinstance(data, dict):
        return False
    
    requeridos = ["id", "nombre", "precio", "stock", "detalles"]
    for campo in requeridos:
        if campo not in data:
            return False
            
    if not isinstance(data["id"], int):
        return False
    if not isinstance(data["nombre"], str) or len(data["nombre"].strip()) == 0:
        return False
    if not isinstance(data["precio"], (int, float)) or data["precio"] <= 0:
        return False
    if not isinstance(data["stock"], int) or data["stock"] < 0:
        return False
        
    detalles = data["detalles"]
    if not isinstance(detalles, dict):
        return False
    if "origen" not in detalles or not isinstance(detalles["origen"], str):
        return False
    if "organico" not in detalles or not isinstance(detalles["organico"], bool):
        return False
        
    if "etiquetas" in data and data["etiquetas"] is not None:
        if not isinstance(data["etiquetas"], list) or not all(isinstance(t, str) for t in data["etiquetas"]):
            return False
            
    return True

def ejecutar_validacion_manual(lista_datos):
    correctos = 0
    for item in lista_datos:
        if validar_manual(item):
            correctos += 1
    return correctos


# ==========================================
# 2. ESTRATEGIA: PYDANTIC V2
# ==========================================
class DetallesProducto(BaseModel):
    origen: str
    organico: bool

class ProductoModel(BaseModel):
    id: int
    nombre: str = Field(..., min_length=1)
    precio: PositiveFloat
    stock: NonNegativeInt
    detalles: DetallesProducto
    etiquetas: Optional[List[str]] = None

def ejecutar_validacion_pydantic(lista_datos):
    correctos = 0
    for item in lista_datos:
        try:
            # model_validate es el método óptimo en Pydantic v2
            ProductoModel.model_validate(item, strict=True)
            correctos += 1
        except Exception:
            pass
    return correctos


# ==========================================
# 3. ESTRATEGIA: JSON SCHEMA
# ==========================================
schema_producto = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "nombre": {"type": "string", "minLength": 1},
        "precio": {"type": "number", "minimum": 0.01},
        "stock": {"type": "integer", "minimum": 0},
        "detalles": {
            "type": "object",
            "properties": {
                "origen": {"type": "string"},
                "organico": {"type": "boolean"}
            },
            "required": ["origen", "organico"]
        },
        "etiquetas": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["id", "nombre", "precio", "stock", "detalles"]
}

def ejecutar_validacion_jsonschema(lista_datos):
    correctos = 0
    for item in lista_datos:
        try:
            validate(instance=item, schema=schema_producto)
            correctos += 1
        except ValidationError:
            pass
    return correctos


# ==========================================
# 4. BENCHMARK / MÁS DE 1000 PRODUCTOS
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO BENCHMARK DE VALIDACIÓN (1000 Productos) ---")
    
    # Calentamiento y verificación de que todos validan lo mismo
    res_manual = ejecutar_validacion_manual(datos_benchmark)
    res_pydantic = ejecutar_validacion_pydantic(datos_benchmark)
    res_schema = ejecutar_validacion_jsonschema(datos_benchmark)
    
    print(f"Productos identificados como válidos (de 1000):")
    print(f"  - Manual: {res_manual}/1000")
    print(f"  - Pydantic v2: {res_pydantic}/1000")
    print(f"  - JSON Schema: {res_schema}/1000\n")

    # Ejecución y toma de tiempos
    # 1. Manual
    start = time.perf_counter()
    ejecutar_validacion_manual(datos_benchmark)
    t_manual = (time.perf_counter() - start) * 1000 # Convertir a milisegundos

    # 2. Pydantic
    start = time.perf_counter()
    ejecutar_validacion_pydantic(datos_benchmark)
    t_pydantic = (time.perf_counter() - start) * 1000

    # 3. JSON Schema
    start = time.perf_counter()
    ejecutar_validacion_jsonschema(datos_benchmark)
    t_schema = (time.perf_counter() - start) * 1000

    # Mostrar Resultados
    print("RESULTADOS DE RENDIMIENTO (Tiempo total para 1000 elementos):")
    print(f"1. Validación Manual:  {t_manual:.2f} ms  (Línea base nativa)")
    print(f"2. Pydantic v2:         {t_pydantic:.2f} ms  (Compilado en Rust)")
    print(f"3. JSON Schema:         {t_schema:.2f} ms  (Librería pure-Python)")
    print("-" * 57)