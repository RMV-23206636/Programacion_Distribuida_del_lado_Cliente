# Reto IA 5 - Profundiza

## Decisión Técnica: ¿Herencia o Composición?

Elegí **Composición** (ReceptorAlertas tiene una instancia de Observable en `self.eventos`) sobre Herencia por el principio de "Single Responsibility" (Responsabilidad Única) y cohesión. 

`ReceptorAlertas` ya tiene responsabilidades complejas (manejo de socket asíncrono HTTP, parseo de SSE, timeouts y reconexión Last-Event-ID). Si heredara de `Observable`, expondríamos métodos de publicación (`notificar()`) a los consumidores externos, cuando en realidad el cliente externo solo debería poder suscribirse a eventos (`suscribir()`). La composición nos permite ocultar y desacoplar estas funciones, o instanciar el observable explícitamente (`receptor.eventos.suscribir()`), manteniendo claro que el "Despachador de Eventos" es una entidad lógica separada, manejando la propagación de eventos y aislando excepciones en los callbacks de la capa de red.
