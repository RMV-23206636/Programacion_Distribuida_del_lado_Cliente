# Reto IA 6 - Separacion de responsabilidades

`CircuitBreaker` decide salud/transiciones. `TokenManagerDummy` maneja tokens. `ClienteRobusto` orquesta ambos.

Decision critica: auth no debe depender del mismo breaker de inventario. Para evitar deadlock Auth-Breaker, refresh debe usar breaker separado o canal propio.
