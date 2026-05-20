import requests

# --- Excepciones Personalizadas Organizadas por Código HTTP ---
class EcoMarketError(requests.exceptions.HTTPError):
    """Error base para la API de EcoMarket."""
    pass

class BadRequestError(EcoMarketError):
    """Lanzada cuando hay errores de validación de datos (400)."""
    pass

class NotFoundError(EcoMarketError):
    """Lanzada cuando un recurso no existe (404)."""
    pass

class ConflictError(EcoMarketError):
    """Lanzada cuando ocurre una colisión de dependencias en el servidor (409)."""
    pass


class EcoMarketClient:
    def __init__(self, base_url="https://api.ecomarket.com/v1", token="token-de-prueba-uan"):
        """
        Inicializa el cliente alineado a los servidores y seguridad de OpenAPI.
        """
        self.base_url = base_url
        self.token = token

    def _get_headers(self) -> dict:
        """Helper para inyectar Content-Type y Bearer JWT de forma centralizada."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _manejar_error(self, response: requests.Response):
        """Procesa respuestas de error estándar mapeadas en el componente Error de OpenAPI."""
        if response.status_code == 400:
            raise BadRequestError(f"400 Bad Request: {response.text}", response=response)
        elif response.status_code == 404:
            raise NotFoundError(f"404 Not Found: {response.text}", response=response)
        elif response.status_code == 409:
            raise ConflictError(f"409 Conflict: {response.text}", response=response)
        response.raise_for_status()

    # --- ENDPOINTS: /productos ---

    def listar_productos(self, categoria: str = None, nombre: str = None, limit: int = 20) -> dict:
        """GET /productos - Lista productos paginados filtrando por categoría y nombre."""
        url = f"{self.base_url}/productos"
        params = {"limit": limit}
        if categoria: params["categoria"] = categoria
        if nombre: params["nombre"] = nombre
            
        response = requests.get(url, params=params, headers=self._get_headers())
        self._manejar_error(response)
        return response.json()

    def crear_producto(self, datos: dict) -> dict:
        """POST /productos - Crea un producto. Requiere autenticación."""
        url = f"{self.base_url}/productos"
        response = requests.post(url, json=datos, headers=self._get_headers())
        if response.status_code == 201:
            return response.json() if response.text else {"status": "creado"}
        self._manejar_error(response)

    # --- ENDPOINTS: /productos/{id} ---

    def obtener_producto(self, producto_id: int) -> dict:
        """GET /productos/{id} - Obtiene el detalle de un producto por ID."""
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        self._manejar_error(response)

    def actualizar_producto_parcial(self, producto_id: int, campos: dict) -> dict:
        """PATCH /productos/{id} - Actualización parcial (precio/disponible)."""
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.patch(url, json=campos, headers=self._get_headers())
        if response.status_code == 200:
            return response.json() if response.text else {"status": "actualizado"}
        self._manejar_error(response)

    def eliminar_producto(self, producto_id: int) -> bool:
        """DELETE /productos/{id} - Elimina un producto. Retorna True si es exitoso (204)."""
        url = f"{self.base_url}/productos/{producto_id}"
        response = requests.delete(url, headers=self._get_headers())
        if response.status_code == 204:
            return True
        self._manejar_error(response)

    # --- ENDPOINTS: /productores ---

    def listar_productores(self) -> list:
        """GET /productores - Retorna la lista de productores registrados."""
        url = f"{self.base_url}/productores"
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        self._manejar_error(response)

    def registrar_productor(self, datos: dict) -> dict:
        """POST /productores - Registra un nuevo productor."""
        url = f"{self.base_url}/productores"
        response = requests.post(url, json=datos, headers=self._get_headers())
        if response.status_code == 201:
            return response.json() if response.text else {"status": "registrado"}
        self._manejar_error(response)

    # --- ENDPOINTS: /productores/{id} ---

    def eliminar_productor(self, productor_id: int) -> bool:
        """DELETE /productores/{id} - Elimina un productor si no tiene dependencias activas (409)."""
        url = f"{self.base_url}/productores/{productor_id}"
        response = requests.delete(url, headers=self._get_headers())
        if response.status_code == 204:
            return True
        self._manejar_error(response)

    def obtener_productos_productor(self, productor_id: int) -> list:
        """GET /productores/{id}/productos - Obtiene el catálogo de un productor."""
        url = f"{self.base_url}/productores/{productor_id}/productos"
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        self._manejar_error(response)

    # --- ENDPOINTS: /pedidos ---

    def crear_pedido(self, datos: dict) -> dict:
        """POST /pedidos - Genera una orden de compra en la plataforma."""
        url = f"{self.base_url}/pedidos"
        response = requests.post(url, json=datos, headers=self._get_headers())
        if response.status_code == 201:
            return response.json() if response.text else {"status": "pedido creado"}
        self._manejar_error(response)

    def cambiar_estado_pedido(self, pedido_id: int, campos: dict) -> dict:
        """PATCH /pedidos/{id} - Modifica el estado del flujo del pedido."""
        url = f"{self.base_url}/pedidos/{pedido_id}"
        response = requests.patch(url, json=campos, headers=self._get_headers())
        if response.status_code == 200:
            return response.json() if response.text else {"status": "estado actualizado"}
        self._manejar_error(response)


if __name__ == "__main__":
    print(">>> Pruebas locales de inicialización del Cliente Corregido...")
    cliente = EcoMarketClient(base_url="http://127.0.0.1:4010") # Puerto por defecto de Prism Mock
    print(f"Instancia generada de forma conforme con URL: {cliente.base_url}")