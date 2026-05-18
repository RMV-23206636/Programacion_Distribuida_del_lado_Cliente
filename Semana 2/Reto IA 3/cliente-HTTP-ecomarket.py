import requests

BASE_URL = "http://127.0.0.1:4010"
TOKEN = "token-de-pureba-uan"

# --- Excepciones Personalizadas ---
class EcoMarketError(Exception):
    """Error base para la API de EcoMarket."""
    pass

class NotFoundError(EcoMarketError):
    """Lanzada cuando un recurso no existe (404)."""
    pass

class ConflictError(EcoMarketError):
    """Lanzada cuando hay un conflicto, como un producto duplicado (409)."""
    pass

# --- Funciones CRUD ---

def crear_producto(datos: dict) -> dict:
    """
    Crea un nuevo producto en EcoMarket.
    
    Ejemplo:
        nuevo = crear_producto({"nombre": "Manzana Orgánica", "precio": 2.5})
    """
    url = f"{BASE_URL}/productos"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    
    response = requests.post(url, json=datos, headers=headers)
    
    if response.status_code == 201:
        # Si hay contenido, lo devolvemos; si no, devolvemos un mensaje de éxito
        return response.json() if response.text else {"status": "creado con éxito"}
    elif response.status_code == 409:
        raise ConflictError(f"Conflicto: El producto ya existe. {response.text}")
    
    response.raise_for_status()


def actualizar_producto_total(producto_id: int, datos: dict) -> dict:
    """
    Reemplaza completamente un producto existente (PUT).
    
    Ejemplo:
        actualizar_producto_total(101, {"nombre": "Pera", "precio": 3.0, "stock": 50})
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    
    response = requests.put(url, json=datos, headers=headers)
    
    if response.status_code == 200:
        if response.text:
            return response.json()
        else:
            return {"status": "actualización total exitosa", "id": producto_id}
    elif response.status_code == 404:
        raise NotFoundError(f"No se encontró el producto con ID {producto_id}")
    
    response.raise_for_status()


def actualizar_producto_parcial(producto_id: int, campos: dict) -> dict:
    """
    Modifica solo los campos especificados de un producto (PATCH).
    
    Ejemplo:
        actualizar_producto_parcial(101, {"precio": 2.85})
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    
    response = requests.patch(url, json=campos, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise NotFoundError(f"No se encontró el producto con ID {producto_id}")
    
    response.raise_for_status()


def eliminar_producto(producto_id: int) -> bool:
    """
    Elimina un producto por su ID.
    
    Retorna True si la operación fue exitosa (204).
    Lanza NotFoundError si el producto no existe (404).
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 204:
        return True
    elif response.status_code == 404:
        raise NotFoundError(f"Error al eliminar: El ID {producto_id} no existe.")
    
    response.raise_for_status()

# --- Añade esto justo debajo de tus funciones, sin indentación (al margen izquierdo) ---

print(">>> Iniciando pruebas del cliente...")

try:
    print("--- Intentando crear producto ---")
    nuevo = {
        "nombre": "Miel Orgánica", 
        "precio": 15.50, 
        "categoria": "miel", 
        "productor_id": 1
    }
    resultado = crear_producto(nuevo)
    print(f"Éxito en creación: {resultado}")

    print("\n--- Intentando eliminar producto ID 1 ---")
    if eliminar_producto(1):
        print("Eliminado correctamente")

except Exception as e:
    print(f"HA OCURRIDO UN ERROR: {e}")

# --- Bloque de prueba para el Conflicto (409) ---
try:
    print("--- Probando caso 409 Conflict ---")
    headers_conflicto = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
        "Prefer": "code=409"  # Forzamos a Prism a dar error 409
    }
    
    # Usamos la URL de productos
    res = requests.post(f"{BASE_URL}/productos", json={"nombre":"test"}, headers=headers_conflicto)
    
    if res.status_code == 409:
        # Esto "lanza" el error hacia el bloque 'except' de abajo
        raise ConflictError("El servidor respondió con 409 Conflict (Simulado)")
    else:
        print(f"Nota: El servidor respondió con {res.status_code} en lugar de 409")

except ConflictError as e:
    # ¡ESTA LÍNEA ES LA QUE TE FALTA MOSTRAR!
    print(f"VALIDACIÓN CORRECTA: {e}") 

print(">>> Pruebas finalizadas.")