import urllib.parse
import uuid
from typing import Union, Type, Optional

class URLBuilder:
    def __init__(self, base_url: str):
        # Asegura que la URL base no termine en / para evitar dobles slashes
        self.base_url = base_url.rstrip('/')
        self.path_segments = []
        self.query_params = {}

    def add_path_segment(self, segment: any, expected_type: Optional[Type] = None) -> 'URLBuilder':
        """
        Agrega un segmento al path de forma segura.
        Valida tipos y escapa caracteres especiales.
        """
        # 1. Validación estricta de tipos si se solicita
        if expected_type == int:
            try:
                # Forzar la conversión a int para validar
                int(str(segment))
            except (ValueError, TypeError):
                raise ValueError(f"Validación fallida: Se esperaba un entero, se recibió '{segment}'")
        
        elif expected_type == uuid.UUID:
            try:
                if not isinstance(segment, uuid.UUID):
                    uuid.UUID(str(segment))
            except (ValueError, TypeError):
                raise ValueError(f"Validación fallida: Se esperaba un UUID válido, se recibió '{segment}'")

        # 2. Convertir a string y escapar de forma segura
        # safe='' asegura que incluso los slashes '/' se escapen como %2F
        safe_segment = urllib.parse.quote(str(segment), safe='')
        self.path_segments.append(safe_segment)
        return self

    def add_query_params(self, params: dict) -> 'URLBuilder':
        """Agrega parámetros de consulta (Query Strings) de forma segura."""
        if params:
            self.query_params.update(params)
        return self

    def build(self) -> str:
        """Construye y retorna la URL final."""
        url = self.base_url
        
        if self.path_segments:
            url += "/" + "/".join(self.path_segments)
            
        if self.query_params:
            # urlencode se encarga de escapar llaves y valores de la query string
            url += "?" + urllib.parse.urlencode(self.query_params)
            
        return url
    
# =====================================================================
# SECCIÓN DE PRUEBAS / CASOS MALICIOSOS
# =====================================================================
if __name__ == "__main__":
    base_url = "https://api.mi-tienda.com"
    
    print("=== 1. PRUEBA: PATH TRAVERSAL ===")
    ataque_1 = "../../../etc/passwd"
    try:
        URLBuilder(base_url).add_path_segment(ataque_1, expected_type=int).build()
    except ValueError as e:
        print(f"[PROTEGIDO - Tipo Estricto]: {e}")
        
    url_segura = URLBuilder(base_url).add_path_segment(ataque_1).build()
    print(f"[PROTEGIDO - Escapado]: {url_segura}\n")

    print("=== 2. PRUEBA: INYECCIÓN DE QUERY PARAMS ===")
    ataque_2 = "123?promo=gratis&admin=true"
    url_segura = URLBuilder(base_url).add_path_segment(ataque_2).build()
    print(f"[PROTEGIDO]: {url_segura}\n")

    print("=== 3. PRUEBA: UNICODE HOMÓGLIFO ===")
    ataque_3 = "123\u2044admin"
    url_segura = URLBuilder(base_url).add_path_segment(ataque_3).build()
    print(f"[PROTEGIDO]: {url_segura}\n")