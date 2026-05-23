class EventRouterPrioritizado:
    def __init__(self):
        # handlers estructurado como { tipo: [(prioridad, fn), ...] }
        self.handlers = {}

    def registrar(self, tipo, fn, prioridad=5):
        if tipo not in self.handlers:
            self.handlers[tipo] = []
        # Registramos como tupla para conservar la prioridad
        self.handlers[tipo].append((prioridad, fn))

    def desregistrar(self, tipo, fn):
        if tipo in self.handlers:
            # Filtramos para eliminar la tupla con esa función
            self.handlers[tipo] = [h for h in self.handlers[tipo] if h[1] != fn]

    def despachar(self, tipo, datos):
        if tipo not in self.handlers:
            return

        # Ordenar handlers: primero las prioridades mayores, luego preservar orden de llegada 
        # (al ser list sort en Python es estable por defecto)
        # Ordenamos descendente por prioridad
        handlers_ordenados = sorted(self.handlers[tipo], key=lambda x: x[0], reverse=True)
        
        for prioridad, fn in handlers_ordenados:
            try:
                fn(datos)
            except Exception as e:
                import logging
                logging.error(f"Handler para '{tipo}' falló: {e}")
                continue
