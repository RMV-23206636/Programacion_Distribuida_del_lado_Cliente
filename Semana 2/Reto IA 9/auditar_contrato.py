import yaml
import inspect
import importlib.util
import sys
from typing import Dict, Any

# Mapeo esperado de Endpoints OpenAPI -> Métodos del Cliente Python
MAPEO_CONTRATO = {
    ("/productos", "get"): {
        "metodo": "listar_productos",
        "params": ["categoria", "nombre", "limit"],
        "respuestas": [200]
    },
    ("/productos", "post"): {
        "metodo": "crear_producto",
        "params": ["datos"],
        "respuestas": [201, 400]
    },
    ("/productos/{id}", "get"): {
        "metodo": "obtener_producto",
        "params": ["producto_id"],
        "respuestas": [200, 404]
    },
    ("/productos/{id}", "patch"): {
        "metodo": "actualizar_producto_parcial",
        "params": ["producto_id", "campos"],
        "respuestas": [200, 404]
    },
    ("/productos/{id}", "delete"): {
        "metodo": "eliminar_producto",
        "params": ["producto_id"],
        "respuestas": [204]
    },
    ("/productores", "get"): {
        "metodo": "listar_productores",
        "params": [],
        "respuestas": [200]
    },
    ("/productores", "post"): {
        "metodo": "registrar_productor",
        "params": ["datos"],
        "respuestas": [201]
    },
    ("/productores/{id}", "delete"): {
        "metodo": "eliminar_productor",
        "params": ["productor_id"],
        "respuestas": [204, 409]
    },
    ("/productores/{id}/productos", "get"): {
        "metodo": "obtener_productos_productor",
        "params": ["productor_id"],
        "respuestas": [200]
    },
    ("/pedidos", "post"): {
        "metodo": "crear_pedido",
        "params": ["datos"],
        "respuestas": [201]
    },
    ("/pedidos/{id}", "patch"): {
        "metodo": "cambiar_estado_pedido",
        "params": ["pedido_id", "campos"],
        "respuestas": [200]
    }
}

def cargar_cliente(ruta_archivo: str, nombre_clase: str):
    try:
        spec = importlib.util.spec_from_file_location("modulo_cliente", ruta_archivo)
        modulo = importlib.util.module_from_spec(spec)
        sys.modules["modulo_cliente"] = modulo
        spec.loader.exec_module(modulo)
        return getattr(modulo, nombre_clase)
    except Exception as e:
        print(f"❌ Error crítico al cargar el archivo cliente: {e}")
        sys.exit(1)

def auditar(ruta_openapi: str, ruta_cliente: str, nombre_clase: str):
    with open(ruta_openapi, 'r', encoding='utf-8') as f:
        contrato = yaml.safe_load(f)
    
    ClaseCliente = cargar_cliente(ruta_cliente, nombre_clase)
    instancia_cliente = ClaseCliente()
    
    print("\n" + "="*60)
    print("📋 REPORTE DE CONFORMIDAD DE CONTRATO - ECOMARKET")
    print("="*60 + "\n")
    
    global_conformidad = True
    
    # Evaluar los endpoints declarados en OpenAPI
    for path, info_path in contrato.get("paths", {}).items():
        for verbo, info_verbo in info_path.items():
            if verbo not in ['get', 'post', 'patch', 'delete', 'put']:
                continue
                
            llave_contrato = (path, verbo)
            print(f"🌐 Endpoint: {verbo.upper()} {path}")
            
            if llave_contrato not in MAPEO_CONTRATO:
                print(f"  ❌ Desconocido: No mapeado en el verificador.\n")
                continue
                
            meta = MAPEO_CONTRATO[llave_contrato]
            nombre_funcion = meta["metodo"]
            
            # 1. Verificar existencia de la función
            if not hasattr(ClaseCliente, nombre_funcion):
                print(f"  ❌ Faltante: No hay función para endpoint (Se esperaba '{nombre_funcion}')\n")
                global_conformidad = False
                continue
                
            funcion = getattr(ClaseCliente, nombre_funcion)
            sig = inspect.signature(funcion)
            params_funcion = list(sig.parameters.keys())
            
            # 2. Verificar Parámetros de la firma
            params_faltantes = [p for p in meta["params"] if p not in params_funcion]
            
            # 3. Verificar códigos de respuesta manejados analizando el código fuente
            codigo_fuente = inspect.getsource(funcion)
            codigos_faltantes = [str(c) for c in meta["respuestas"] if str(c) not in codigo_fuente and c != 200]
            
            # Evaluar si el Token de autenticación (Header) está integrado
            tiene_seguridad = "security" in info_verbo or "security" in contrato
            usa_headers = "headers" in codigo_fuente or "_get_headers" in codigo_fuente
            
            # Determinar estatus
            if params_faltantes or codigos_faltantes or (tiene_seguridad and not usa_headers):
                print(f"  ⚠️ Parcial: la función '{nombre_funcion}' presenta inconsistencias:")
                if params_faltantes:
                    print(f"    - Parámetros faltantes en firma: {params_faltantes}")
                if codigos_faltantes:
                    print(f"    - Códigos HTTP no gestionados explícitamente: {codigos_faltantes}")
                if tiene_seguridad and not usa_headers:
                    print(f"    - Alerta: El endpoint requiere Auth pero no se detecta envío de Headers.")
                global_conformidad = False
            else:
                print(f"  ✅ Conformidad: función '{nombre_funcion}' cumple con el contrato.")
                
            print("-" * 50)
            
    # Detectar métodos obsoletos o fuera de contrato (como PUT en el cliente original)
    metodos_cliente = [func for func in dir(ClaseCliente) if callable(getattr(ClaseCliente, func)) and not func.startswith("_")]
    metodos_esperados = [m["metodo"] for m in MAPEO_CONTRATO.values()]
    
    metodos_extra = [m for m in metodos_cliente if m not in metodos_esperados]
    if metodos_extra:
        print(f"\n⚠️ Métodos detectados en el cliente que NO existen en el contrato OpenAPI: {metodos_extra}")

    print("\n" + "="*60)
    if global_conformidad:
        print("🎉 ¡RESULTADO FINAL: 100% DE CONFORMIDAD CON EL CONTRATO!")
    else:
        print("🚨 RESULTADO FINAL: CONTRATO VIOLADO. CORREGIR ACCIONES PARCIALES/FALTANTES.")
    print("="*60 + "\n")

if __name__ == "__main__":
    # Cambiar 'cliente-HTTP-ecomarket-v2.py' por el nombre del archivo a evaluar
    auditar("openapi.yaml", "cliente-HTTP-ecomarket-v2.py", "EcoMarketClient")