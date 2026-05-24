# Reto IA 1 - Diagrama de estados

Transcripcion completada:

Estudiante: "El breaker tiene CERRADO, ABIERTO y SEMIABIERTO. CERRADO deja pasar peticiones y cuenta fallos; ABIERTO rechaza sin tocar servidor; SEMIABIERTO permite probar recuperacion."

IA: "Correcto. Agrega que SEMIABIERTO solo debe dejar pasar una peticion de prueba."

Correccion: "SEMIABIERTO usa lock; una peticion prueba, las demas reciben CircuitOpenError."

Diagrama final incluido en `../README.md`.
