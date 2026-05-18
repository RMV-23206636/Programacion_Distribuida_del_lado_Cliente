import pytest
from validadores import validar_producto, validar_lista_productos, ValidationError

# Base de un producto completamente válido para usar de plantilla limpia
@pytest.fixture
def producto_valido():
    return {
        "id": 101,
        "nombre": "Manzanas Orgánicas",
        "precio": 4.50,
        "categoria": "frutas",
        "disponible": True,
        "descripcion": "Manzanas frescas locales",
        "productor": {"id": 1, "nombre": "Finca Sol"},
        "creado_en": "2026-05-18T10:00:00Z"
    }

def test_error_falta_campo_requerido(producto_valido):
    """Caso 1: Falla si falta un campo estructural indispensable (ej: nombre)."""
    del producto_valido['nombre']
    with pytest.raises(ValidationError) as exc_info:
        validar_producto(producto_valido)
    assert "Falta el campo requerido obligatorio: 'nombre'" in str(exc_info.value)

def test_error_tipo_incorrecto_en_campo_requerido(producto_valido):
    """Caso 2: Falla si el tipo de dato no coincide con el esquema técnico (ej: id como string)."""
    producto_valido['id'] = "ciento-uno"
    with pytest.raises(ValidationError) as exc_info:
        validar_producto(producto_valido)
    assert "El campo 'id' debe ser de tipo int" in str(exc_info.value)

def test_error_precio_negativo_o_cero(producto_valido):
    """Caso 3: Falla si el precio rompe la regla de negocio (Configuración Mock Server de precio negativo)."""
    producto_valido['precio'] = -1.50
    with pytest.raises(ValidationError) as exc_info:
        validar_producto(producto_valido)
    assert "El campo 'precio' debe ser un número positivo mayor que 0" in str(exc_info.value)

def test_error_categoria_invalida(producto_valido):
    """Caso 4: Falla si la categoría no pertenece a la lista blanca permitida."""
    producto_valido['categoria'] = 'carnes'  # Categoría no soportada
    with pytest.raises(ValidationError) as exc_info:
        validar_producto(producto_valido)
    assert "La 'categoria' 'carnes' no es válida" in str(exc_info.value)

def test_error_campo_opcional_productor_mal_formado(producto_valido):
    """Caso 5: Falla si un subcampo opcional está presente pero le faltan llaves requeridas."""
    producto_valido['productor'] = {"nombre": "SoloNombreSinID"}
    with pytest.raises(ValidationError) as exc_info:
        validar_producto(producto_valido)
    assert "El campo opcional 'productor' debe contener internamente las llaves 'id' y 'nombre'" in str(exc_info.value)

def test_error_lista_con_elemento_corrupto(producto_valido):
    """Caso 6: Falla al procesar colecciones si un elemento rompe las reglas, indicando el índice exacto."""
    producto_corrupto = producto_valido.copy()
    producto_corrupto['disponible'] = "NoEsUnBooleano"
    
    lista_productos = [producto_valido, producto_corrupto]
    
    with pytest.raises(ValidationError) as exc_info:
        validar_lista_productos(lista_productos)
    assert "Error de validación en el producto del índice [1]" in str(exc_info.value)