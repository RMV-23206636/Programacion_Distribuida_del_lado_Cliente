import requests

# --- Excepciones Personalizadas Compatibles con Requests ---
class EcoMarketError(requests.exceptions.HTTPError):
    """Error base para la API de EcoMarket, compatible con la suite de QA."""
    pass

class NotFoundError(EcoMarketError):
    """Lanzada cuando un recurso no existe (404)."""
    pass

class ConflictError(EcoMarketError):
    """Lanzada cuando hay un conflicto, como un producto duplicado (409)."""
    pass


# --- Clase del Cliente HTTP EcoMarket ---
class EcoMarketClient:
    def __init__(self, base_url="http://127.0.0.1:4010", token="token-de-pureba-uan"):
        """
        Inicializa el cliente de EcoMarket permitiendo modularidad y desacoplamiento
        para facilitar las pruebas automatizadas de QA.
        """
        self.base_url = base_url
        self.token = token

    def _get_headers(self) -> dict:
        """Helper privado para estructurar los headers de las peticiones."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def listar_productos(self, categoria: str = None, orden: str = None) -> list:
        """
        Obtiene la lista de productos con soporte para filtros opcionales.
        """
        url = f"{self.base_url}/productos"
        params = {}
        if categoria: params["categoria"] = categoria
        if orden: params["orden"] = orden
            
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def obtener_producto(self, producto_id: int) -> dict:
        """
        Recupera un producto específico mediante su ID único.
        """
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 404:
            raise NotFoundError(f"No se encontró el producto con ID {producto_id}", response=response)
        
        response.raise_for_status()
        return response.json()

    def crear_producto(self, datos: dict) -> dict:
        """
        Crea un nuevo producto en EcoMarket controlando casos de borde de tipado.
        """
        # Edge Case: Validación preventiva del tipo de dato para el precio
        if "precio" in datos and isinstance(datos["precio"], str):
            raise TypeError("El campo 'precio' debe ser un número, no un string.")
            
        url = f"{self.base_url}/productos"
        response = requests.post(url, json=datos, headers=self._get_headers())
        
        if response.status_code == 201:
            return response.json() if response.text else {"status": "creado con éxito"}
        elif response.status_code == 409:
            raise ConflictError(f"Conflicto: El producto ya existe. {response.text}", response=response)
        
        response.raise_for_status()

    def actualizar_producto_total(self, producto_id: int, datos: dict) -> dict:
        """
        Reemplaza completamente un producto existente (PUT).
        """
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.put(url, json=datos, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json() if response.text else {"status": "actualización total exitosa", "id": producto_id}
        elif response.status_code == 404:
            raise NotFoundError(f"No se encontró el producto con ID {producto_id}", response=response)
        
        response.raise_for_status()

    def actualizar_producto_parcial(self, producto_id: int, campos: dict) -> dict:
        """
        Modifica solo los campos especificados de un producto (PATCH).
        """
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.patch(url, json=campos, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFoundError(f"No se encontró el producto con ID {producto_id}", response=response)
        
        response.raise_for_status()

    def eliminar_producto(self, producto_id: int) -> bool:
        """
        Elimina un producto por su ID. Retorna True si la operación fue exitosa (204).
        """
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.delete(url, headers=self._get_headers())
        
        if response.status_code in [200, 204]:
            return True
        elif response.status_code == 404:
            raise NotFoundError(f"Error al eliminar: El ID {producto_id} no existe.", response=response)
        
        response.raise_for_status()

        # --- BLOQUE DE EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    print(">>> Iniciando pruebas con EcoMarketClient (v2)...")
    
    # 1. Instanciamos el cliente
    cliente = EcoMarketClient()
    
    try:
        # 2. Intentamos crear un producto
        print("--- Intentando crear producto ---")
        nuevo_producto = {
            "nombre": "Miel Orgánica v2", 
            "precio": 18.50, 
            "categoria": "miel", 
            "productor_id": 1
        }
        resultado = cliente.crear_producto(nuevo_producto)
        print(f"Éxito en creación: {resultado}")
        
        # 3. Intentamos listar los productos para ver si interactúa
        print("\n--- Listando productos ---")
        productos = cliente.listar_productos()
        print(f"Productos obtenidos: {productos}")

        # 4. Intentamos eliminar el producto ID 1
        print("\n--- Intentando eliminar producto ID 1 ---")
        if cliente.eliminar_producto(1):
            print("Eliminado correctamente")

    except Exception as e:
        print(f"HA OCURRIDO UN ERROR: {e}")

    print(">>> Pruebas finalizadas v2.")