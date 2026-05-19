import pytest
import requests
import responses
from json.decoder import JSONDecodeError

# ==============================================================================
# IMPLEMENTACIÓN DEL CLIENTE (Para asegurar la ejecución inmediata de la suite)
# ==============================================================================
class EcoMarketClient:
    def __init__(self, base_url="https://api.ecomarket.com", token=None):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def listar_productos(self, categoria=None, orden=None):
        params = {}
        if categoria: params['categoria'] = categoria
        if orden: params['orden'] = orden
        
        response = requests.get(f"{self.base_url}/productos", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def obtener_producto(self, producto_id):
        response = requests.get(f"{self.base_url}/productos/{producto_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def crear_producto(self, datos):
        # Validación local de tipo para el caso de borde (Edge Case)
        if "precio" in datos and isinstance(datos["precio"], str):
            raise TypeError("El campo 'precio' debe ser un número, no un string.")
            
        response = requests.post(f"{self.base_url}/productos", json=datos, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def actualizar_producto_total(self, producto_id, datos):
        response = requests.put(f"{self.base_url}/productos/{producto_id}", json=datos, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def actualizar_producto_parcial(self, producto_id, campos):
        response = requests.patch(f"{self.base_url}/productos/{producto_id}", json=campos, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def eliminar_producto(self, producto_id):
        response = requests.delete(f"{self.base_url}/productos/{producto_id}", headers=self.headers)
        response.raise_for_status()
        return response.status_code in [200, 204]


# ==============================================================================
# CONFIGURACIÓN DE FIXTURES DE PYTEST
# ==============================================================================
@pytest.fixture
def cliente_valido():
    """Retorna una instancia del cliente HTTP con un token válido."""
    return EcoMarketClient(base_url="https://api.ecomarket.com", token="token_secreto_123")

@pytest.fixture
def cliente_sin_token():
    """Retorna una instancia del cliente sin token de autenticación."""
    return EcoMarketClient(base_url="https://api.ecomarket.com", token=None)


# ==============================================================================
# 1. HAPPY PATH (6 TESTS)
# ==============================================================================

@responses.activate
def test_listar_productos_exitoso(cliente_valido):
    """Prueba el listado exitoso de productos filtrados por categoría y orden."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos?categoria=organicos&orden=asc",
        json=[{"id": 1, "nombre": "Manzana Orgánica", "precio": 2.5}],
        status=200
    )
    
    resultado = cliente_valido.listar_productos(categoria="organicos", orden="asc")
    assert len(resultado) == 1
    assert resultado[0]["nombre"] == "Manzana Orgánica"

@responses.activate
def test_obtener_producto_exitoso(cliente_valido):
    """Prueba la obtención exitosa de un producto específico mediante su ID."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos/1",
        json={"id": 1, "nombre": "Manzana Orgánica", "precio": 2.5},
        status=200
    )
    
    resultado = cliente_valido.obtener_producto(1)
    assert resultado["id"] == 1
    assert resultado["precio"] == 2.5

@responses.activate
def test_crear_producto_exitoso(cliente_valido):
    """Prueba la creación exitosa de un nuevo producto enviando datos válidos."""
    datos_nuevo = {"nombre": "Palta Bio", "precio": 4.5}
    responses.add(
        method=responses.POST,
        url="https://api.ecomarket.com/productos",
        json={"id": 2, "nombre": "Palta Bio", "precio": 4.5},
        status=201
    )
    
    resultado = cliente_valido.crear_producto(datos_nuevo)
    assert resultado["id"] == 2
    assert resultado["nombre"] == "Palta Bio"

@responses.activate
def test_actualizar_producto_total_exitoso(cliente_valido):
    """Prueba la actualización completa (PUT) de un producto existente."""
    datos_actualizados = {"nombre": "Palta Hass Bio", "precio": 5.0}
    responses.add(
        method=responses.PUT,
        url="https://api.ecomarket.com/productos/2",
        json={"id": 2, "nombre": "Palta Hass Bio", "precio": 5.0},
        status=200
    )
    
    resultado = cliente_valido.actualizar_producto_total(2, datos_actualizados)
    assert resultado["precio"] == 5.0
    assert resultado["nombre"] == "Palta Hass Bio"

@responses.activate
def test_actualizar_producto_parcial_exitoso(cliente_valido):
    """Prueba la actualización parcial (PATCH) de un solo campo del producto."""
    campos_parciales = {"precio": 5.5}
    responses.add(
        method=responses.PATCH,
        url="https://api.ecomarket.com/productos/2",
        json={"id": 2, "nombre": "Palta Hass Bio", "precio": 5.5},
        status=200
    )
    
    resultado = cliente_valido.actualizar_producto_parcial(2, campos_parciales)
    assert resultado["precio"] == 5.5

@responses.activate
def test_eliminar_producto_exitoso(cliente_valido):
    """Prueba la eliminación exitosa (DELETE) de un producto existente."""
    responses.add(
        method=responses.DELETE,
        url="https://api.ecomarket.com/productos/2",
        status=204
    )
    
    resultado = cliente_valido.eliminar_producto(2)
    assert resultado is True


# ==============================================================================
# 2. ERRORES HTTP (8 TESTS)
# ==============================================================================

@responses.activate
def test_crear_producto_datos_invalidos_retorna_400_bad_request(cliente_valido):
    """Prueba el comportamiento cuando se envían datos inválidos en la creación."""
    responses.add(
        method=responses.POST,
        url="https://api.ecomarket.com/productos",
        status=400
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.crear_producto({"nombre": ""})
    assert exc_info.value.response.status_code == 400

@responses.activate
def test_listar_productos_sin_token_retorna_401_unauthorized(cliente_sin_token):
    """Prueba que el cliente lance un error de autorización si falta el token."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos",
        status=401
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_sin_token.listar_productos()
    assert exc_info.value.response.status_code == 401

@responses.activate
def test_obtener_producto_inexistente_retorna_404_not_found(cliente_valido):
    """Prueba el intento de consultar un ID que no existe en el sistema."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos/999",
        status=404
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.obtener_producto(999)
    assert exc_info.value.response.status_code == 404

@responses.activate
def test_actualizar_producto_inexistente_retorna_404_not_found(cliente_valido):
    """Prueba la actualización total de un recurso que no existe en el backend."""
    responses.add(
        method=responses.PUT,
        url="https://api.ecomarket.com/productos/999",
        status=404
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.actualizar_producto_total(999, {"nombre": "Test", "precio": 1.0})
    assert exc_info.value.response.status_code == 404

@responses.activate
def test_eliminar_producto_inexistente_retorna_404_not_found(cliente_valido):
    """Prueba el intento de eliminar un ID de producto que ya no existe o es inválido."""
    responses.add(
        method=responses.DELETE,
        url="https://api.ecomarket.com/productos/999",
        status=404
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.eliminar_producto(999)
    assert exc_info.value.response.status_code == 404

@responses.activate
def test_crear_producto_duplicado_retorna_409_conflict(cliente_valido):
    """Prueba el envío de una petición de creación que rompe restricciones de unicidad."""
    responses.add(
        method=responses.POST,
        url="https://api.ecomarket.com/productos",
        status=409
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.crear_producto({"nombre": "Producto Repetido", "precio": 10.0})
    assert exc_info.value.response.status_code == 409

@responses.activate
def test_listar_productos_error_interno_retorna_500_internal_server_error(cliente_valido):
    """Prueba la tolerancia a fallos del cliente ante una caída general del backend."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos",
        status=500
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.listar_productos()
    assert exc_info.value.response.status_code == 500

@responses.activate
def test_listar_productos_servicio_no_disponible_retorna_503_service_unavailable(cliente_valido):
    """Prueba la respuesta cuando el servidor está en mantenimiento o saturado."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos",
        status=503
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        cliente_valido.listar_productos()
    assert exc_info.value.response.status_code == 503


# ==============================================================================
# 3. EDGE CASES (6 TESTS)
# ==============================================================================

@responses.activate
def test_listar_productos_respuesta_vacia_con_200_ok(cliente_valido):
    """Prueba cuando el servidor responde HTTP 200 pero el body está vacío, rompiendo JSON."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos",
        body="",
        status=200,
        content_type="application/json"
    )
    
    with pytest.raises(JSONDecodeError):
        cliente_valido.listar_productos()

@responses.activate
def test_obtener_producto_content_type_incorrecto_text_html(cliente_valido):
    """Prueba si el backend retorna por error una estructura HTML en lugar del JSON esperado."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos/1",
        body="<html><body>Error Crítico de Proxy</body></html>",
        status=200,
        content_type="text/html"
    )
    
    with pytest.raises(JSONDecodeError):
        cliente_valido.obtener_producto(1)

@responses.activate
def test_obtener_producto_json_valido_pero_estructura_incorrecta(cliente_valido):
    """Prueba la aserción defensiva si el JSON recibido es válido pero carece de la estructura esperada."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos/1",
        json={"mensaje_raro": "estructura_desconocida"},
        status=200
    )
    
    resultado = cliente_valido.obtener_producto(1)
    # Validamos que, aunque la petición no lance HTTPError, falten los campos críticos mapeados
    assert "id" not in resultado
    assert "nombre" not in resultado

@responses.activate
def test_listar_productos_timeout_del_servidor(cliente_valido):
    """Prueba la capacidad del cliente de lanzar una excepción de timeout ante un cuelgue de red."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos",
        body=requests.exceptions.Timeout("Connection timed out")
    )
    
    with pytest.raises(requests.exceptions.Timeout):
        cliente_valido.listar_productos()

@responses.activate
def test_crear_producto_campo_precio_como_string_lanza_error(cliente_valido):
    """Prueba la validación local o del servidor para evitar guardar tipos de datos incorrectos."""
    datos_erroneos = {"nombre": "Zanahoria Súper", "precio": "diez_pesos"}
    
    with pytest.raises(TypeError) as exc_info:
        cliente_valido.crear_producto(datos_erroneos)
    assert "debe ser un número" in str(exc_info.value)

@responses.activate
def test_listar_productos_lista_vacia(cliente_valido):
    """Prueba un caso de borde común y válido: la consulta no tiene elementos en la base de datos."""
    responses.add(
        method=responses.GET,
        url="https://api.ecomarket.com/productos",
        json=[],
        status=200
    )
    
    resultado = cliente_valido.listar_productos()
    assert isinstance(resultado, list)
    assert len(resultado) == 0