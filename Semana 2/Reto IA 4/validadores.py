import re
from datetime import datetime

class ValidationError(Exception):
    """Excepción personalizada para errores de validación en el cliente EcoMarket."""
    pass

def validar_producto(data: dict) -> dict:
    """
    Valida un diccionario de producto según las reglas de negocio de EcoMarket.
    Retorna el diccionario si es válido o lanza ValidationError con el motivo exacto.
    """
    if not isinstance(data, dict):
        raise ValidationError(f"Se esperaba un diccionario para el producto, pero se recibió: {type(data).__name__}")

    # 1. Verificar campos requeridos y sus tipos básicos
    # Nota: Incluimos 'disponible' aquí ya que se especifica su tipo en los requerimientos.
    campos_requeridos = {
        'id': int,
        'nombre': str,
        'precio': (int, float),  # Permitimos int o float para ser robustos con JSON numéricos
        'categoria': str,
        'disponible': bool
    }

    for campo, tipo in campos_requeridos.items():
        if campo not in data:
            raise ValidationError(f"Falta el campo requerido obligatorio: '{campo}'.")
        
        # Validación estricta de tipo (evitando que bool sea confundido con int)
        if tipo == int and isinstance(data[campo], bool):
            raise ValidationError(f"El campo '{campo}' debe ser int, pero se recibió un bool.")
        if tipo == (int, float) and isinstance(data[campo], bool):
            raise ValidationError(f"El campo '{campo}' debe ser numérico, pero se recibió un bool.")
            
        if not isinstance(data[campo], tipo):
            raise ValidationError(
                f"El campo '{campo}' debe ser de tipo {tipo if isinstance(tipo, tuple) else tipo.__name__}. "
                f"Se recibió: {type(data[campo])}__name__."
            )

    # 2. Validaciones de reglas de negocio específicas
    if data['precio'] <= 0:
        raise ValidationError(f"El campo 'precio' debe ser un número positivo mayor que 0. Se recibió: {data['precio']}.")

    categorias_validas = ['frutas', 'verduras', 'lacteos', 'miel', 'conservas']
    if data['categoria'] not in categorias_validas:
        raise ValidationError(
            f"La 'categoria' '{data['categoria']}' no es válida. "
            f"Debe ser una de las siguientes: {categorias_validas}."
        )

    # 3. Manejo de campos opcionales
    if 'descripcion' in data and data['descripcion'] is not None:
        if not isinstance(data['descripcion'], str):
            raise ValidationError(f"El campo opcional 'descripcion' debe ser str. Se recibió: {type(data['descripcion']).__name__}.")

    if 'productor' in data and data['productor'] is not None:
        if not isinstance(data['productor'], dict):
            raise ValidationError(f"El campo opcional 'productor' debe ser un dict. Se recibió: {type(data['productor']).__name__}.")
        
        productor = data['productor']
        if 'id' not in productor or 'nombre' not in productor:
            raise ValidationError("El campo opcional 'productor' debe contener internamente las llaves 'id' y 'nombre'.")
        if not isinstance(productor['id'], int) or isinstance(productor['id'], bool):
            raise ValidationError(f"El 'id' del productor debe ser int. Se recibió: {type(productor['id']).__name__}.")
        if not isinstance(productor['nombre'], str):
            raise ValidationError(f"El 'nombre' del productor debe ser str. Se recibió: {type(productor['nombre']).__name__}.")

    if 'creado_en' in data and data['creado_en'] is not None:
        if not isinstance(data['creado_en'], str):
            raise ValidationError(f"El campo opcional 'creado_en' debe ser un str en formato ISO 8601. Se recibió: {type(data['creado_en']).__name__}.")
        try:
            # Reemplazo de 'Z' por una zona horaria válida para compatibilidad nativa en Python
            fecha_str = data['creado_en'].replace('Z', '+00:00')
            datetime.fromisoformat(fecha_str)
        except ValueError:
            raise ValidationError(f"El campo 'creado_en' no cumple con un formato ISO 8601 válido. Se recibió: '{data['creado_en']}'.")

    return data

def validar_lista_productos(data: list) -> list:
    """
    Valida una lista completa de productos.
    """
    if not isinstance(data, list):
        raise ValidationError(f"Se esperaba una lista (list), pero se recibió: {type(data).__name__}")
    
    for indice, producto in enumerate(data):
        try:
            validar_producto(producto)
        except ValidationError as e:
            raise ValidationError(f"Error de validación en el producto del índice [{indice}]: {str(e)}")
            
    return data