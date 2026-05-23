# Reto IA 2 - Aplica (Ruta A)

## Instrucciones de ejecución

1. Instalar dependencias si no las tienes (requiere Python 3.7+):
```bash
pip install httpx
```

2. Ejecutar el script:
```bash
python receptor_alertas.py
```

## Traza del Reto 1

Ver la carpeta `Reto IA 1` para la explicación conceptual. En resumen:
El cliente asíncrono inicia una petición HTTP con el encabezado `Accept: text/event-stream`. El servidor devuelve una respuesta 200 OK y la conexión TCP permanece abierta (keep-alive). A partir de ese momento, el servidor envía fragmentos de texto (chunks) que representan eventos SSE, los cuales el cliente parsea línea por línea sin cerrar la conexión, lo cual ahorra ancho de banda y conexiones comparado al polling clásico.
