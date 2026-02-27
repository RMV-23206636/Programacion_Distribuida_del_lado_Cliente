const express = require('express');
const app = express();
let requestCounter = 0;

// Middleware para simular JSON body parsing
app.use(express.json());

// Escenario 1: Latencia
app.get('/slow', (req, res) => {
    setTimeout(() => res.json({ status: 'ok', data: 'EcoMarket Data' }), 5000);
});

// Escenario 2: Intermitencia
app.get('/flaky', (req, res) => {
    requestCounter++;
    if (requestCounter % 3 === 0) {
        return res.status(503).json({ error: 'Service Unavailable' });
    }
    res.json({ status: 'ok', attempt: requestCounter });
});

// Escenario 3: Truncado
app.get('/cut', (req, res) => {
    res.write('{"status": "partial"'); // Escribir parte de la respuesta
    setTimeout(() => {
        req.destroy(); // Matar el socket abruptamente
    }, 100);
});

// Escenario 4: Formato Inesperado
app.get('/html', (req, res) => {
    // Envía HTML con header 200 OK, común cuando un proxy intermedio falla
    res.set('Content-Type', 'text/html');
    res.send('<html><body><h1>502 Bad Gateway</h1></body></html>');
});

// Escenario 5: Timeout
app.get('/timeout', (req, res) => {
    // No responde nunca (o después de un tiempo absurdo)
    setTimeout(() => res.json({ status: 'too late' }), 65000);
});

app.listen(3000, () => console.log('👹 Chaos Server corriendo en puerto 3000'));