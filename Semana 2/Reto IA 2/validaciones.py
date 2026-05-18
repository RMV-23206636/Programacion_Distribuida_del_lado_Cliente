import json
from datetime import datetime

def validar_producto_ecomarket(data):
    """
    Motor de validación optimizado para EcoMarket.
    Separa la estructura, la lógica de negocio y los tipos complejos.
    """
    CATEGORIAS_VALIDAS = {"frutas", "verduras", "lacteos", "miel", "conservas"}
    
    # 1. Definición de tipos esperados para campos raíz
    campos_requeridos = {
        "id": int, 
        "nombre": str, 
        "precio": (int, float), 
        "categoria": str,
        "disponible": bool,
        "creado_en": str,
        "productor": dict
    }

    try:
        # A. Validación de existencia y tipos básicos
        for campo, tipo in campos_requeridos.items():
            if campo not in data:
                return False, f"Falta campo obligatorio: '{campo}'"
            if not isinstance(data[campo], tipo):
                return False, f"Tipo incorrecto en '{campo}': se esperaba {tipo}"

        # B. Validación de lógica de negocio (Reglas específicas)
        if data["precio"] <= 0:
            return False, "El precio debe ser un valor positivo"

        if data["categoria"] not in CATEGORIAS_VALIDAS:
            return False, f"Categoría '{data['categoria']}' no permitida"

        # C. Validación robusta de objeto anidado (Productor)
        productor = data["productor"]
        # Verificamos campos internos del dict
        if "id" not in productor or "nombre" not in productor:
            return False, "Estructura de 'productor' incompleta (faltan id o nombre)"
        if not isinstance(productor["id"], int) or not isinstance(productor["nombre"], str):
            return False, "Tipos incorrectos dentro de 'productor'"

        # D. Validación de fecha ISO 8601
        try:
            datetime.strptime(data["creado_en"], "%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            return False, "Formato de fecha inválido (YYYY-MM-DDTHH:MM:SSZ)"

        return True, "✅ Validación exitosa"

    except Exception as e:
        return False, f"❌ Error crítico: {str(e)}"

# --- BANCO DE PRUEBAS (Tus 6 casos) ---

casos_prueba = [
    {
        "nombre": "Caso 1: El Intruso de Tipos (ID como string)",
        "json": {"id": "42", "nombre": "Miel", "precio": 10.0, "categoria": "miel", "disponible": True, "creado_en": "2024-01-15T10:30:00Z", "productor": {"id": 1, "nombre": "Test"}}
    },
    {
        "nombre": "Caso 2: El Regalo Envenenado (Precio negativo)",
        "json": {"id": 42, "nombre": "Miel", "precio": -5.0, "categoria": "miel", "disponible": True, "creado_en": "2024-01-15T10:30:00Z", "productor": {"id": 1, "nombre": "Test"}}
    },
    {
        "nombre": "Caso 3: La Categoría Fantasma (No permitida)",
        "json": {"id": 42, "nombre": "Miel", "precio": 150.0, "categoria": "electronica", "disponible": True, "creado_en": "2024-01-15T10:30:00Z", "productor": {"id": 1, "nombre": "Test"}}
    },
    {
        "nombre": "Caso 4: El Productor Anónimo (Faltan campos internos)",
        "json": {"id": 42, "nombre": "Miel", "precio": 150.0, "categoria": "miel", "disponible": True, "creado_en": "2024-01-15T10:30:00Z", "productor": {"nombre": "Solo Nombre"}}
    },
    {
        "nombre": "Caso 5: El Viajero del Tiempo (Fecha mal formateada)",
        "json": {"id": 42, "nombre": "Miel", "precio": 150.0, "categoria": "miel", "disponible": True, "creado_en": "15/01/2024", "productor": {"id": 1, "nombre": "Test"}}
    },
    {
        "nombre": "Caso 6: El Productor Camaleón (String en vez de Dict)",
        "json": {"id": 106, "nombre": "Miel Premium", "precio": 18.5, "categoria": "miel", "disponible": True, "creado_en": "2026-03-31T19:00:00Z", "productor": "Granja El Sol"}
    }
]

print(f"{'CASO':<55} | {'RESULTADO'}")
print("-" * 85)

for prueba in casos_prueba:
    valido, mensaje = validar_producto_ecomarket(prueba["json"])
    status = "RECHAZADO 🛡️" if not valido else "PASÓ ✅"
    print(f"{prueba['nombre']:<55} | {status}: {mensaje}")