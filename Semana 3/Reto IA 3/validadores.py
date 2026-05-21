"""
validadores.py - Reutilizado de Semana 2 (sin modificaciones)
Semana 3 confirma que los validadores NO cambian al migrar a asíncrono.
"""

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
        raise ValidationError(f"Se esperaba un diccionario, se recibió: {type(data).__name__}")

    campos_requeridos = {
        'id': int,
        'nombre': str,
        'precio': (int, float),
        'categoria': str,
        'disponible': bool
    }

    for campo, tipo in campos_requeridos.items():
        if campo not in data:
            raise ValidationError(f"Falta el campo requerido: '{campo}'.")
        if tipo == int and isinstance(data[campo], bool):
            raise ValidationError(f"El campo '{campo}' debe ser int, no bool.")
        if not isinstance(data[campo], tipo):
            raise ValidationError(
                f"El campo '{campo}' debe ser {tipo.__name__ if not isinstance(tipo, tuple) else 'numérico'}. "
                f"Se recibió: {type(data[campo]).__name__}."
            )

    if data['precio'] <= 0:
        raise ValidationError(f"'precio' debe ser mayor que 0. Se recibió: {data['precio']}.")

    categorias_validas = ['frutas', 'verduras', 'lacteos', 'miel', 'conservas']
    if data['categoria'] not in categorias_validas:
        raise ValidationError(
            f"'categoria' '{data['categoria']}' no válida. Opciones: {categorias_validas}."
        )

    if 'descripcion' in data and data['descripcion'] is not None:
        if not isinstance(data['descripcion'], str):
            raise ValidationError(f"'descripcion' debe ser str.")

    if 'creado_en' in data and data['creado_en'] is not None:
        if not isinstance(data['creado_en'], str):
            raise ValidationError(f"'creado_en' debe ser str ISO 8601.")
        try:
            datetime.fromisoformat(data['creado_en'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(f"'creado_en' no es ISO 8601 válido: '{data['creado_en']}'.")

    return data


def validar_lista_productos(data: list) -> list:
    """Valida una lista completa de productos."""
    if not isinstance(data, list):
        raise ValidationError(f"Se esperaba una lista, se recibió: {type(data).__name__}")
    for i, producto in enumerate(data):
        try:
            validar_producto(producto)
        except ValidationError as e:
            raise ValidationError(f"Error en producto [{i}]: {e}")
    return data
