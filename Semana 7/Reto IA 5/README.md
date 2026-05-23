# Por qué elegí herencia/decorador para EventRouterPrioritizado

Para `EventRouterPrioritizado`, decidí crear un componente basado en el patrón Wrapper/Decorador o una reimplementación adaptada que mantiene la misma interfaz pública en lugar de herencia directa. 

**Razonamiento:**
1. **Composición sobre Herencia:** Extender directamente la clase `EventRouter` implicaría sobrescribir múltiples métodos y depender de su estructura de datos interna, rompiendo el principio de encapsulación. Al usar un Decorador (o reimplementar manteniendo la interfaz `registrar(tipo, fn)` con un valor de prioridad predeterminado de 5), garantizamos compatibilidad hacia atrás.
2. **Priorización Transparente:** El `ClienteSSEMultiplex` original no tiene que conocer ni alterar la lógica de despacho. Simplemente llamará a `despachar()` y el `EventRouterPrioritizado` ordenará automáticamente los *handlers* de acuerdo con las prioridades de mayor a menor sin modificar el flujo de eventos.
3. **Escalabilidad:** Al implementarlo de esta manera, los *handlers* urgentes (como el de stock-crítico) podrán ser registrados con prioridad 10, de modo que durante un *burst* de eventos siempre serán los primeros evaluados y atendidos antes que los de tipo precio-actualizado o sistema-ping.
