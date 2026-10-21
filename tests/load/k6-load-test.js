/**
 * Script de Pruebas de Carga con k6 para el Front-End y /health
 * 
 * Uso:
 *   k6 run tests/load/k6-load-test.js
 *   k6 run -e TARGET_URL=http://localhost:80 tests/load/k6-load-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 20 },  // Rampa de subida a 20 usuarios virtuales
    { duration: '30s', target: 50 },  // Carga sostenida de 50 VUs
    { duration: '10s', target: 100 }, // Pico para probar límites
    { duration: '10s', target: 0 },   // Enfriamiento
  ],
  thresholds: {
    // 95% de las peticiones deben responder en menos de 200ms
    http_req_duration: ['p(95)<200'],
    // Tasa de fallos menor al 1% en condiciones normales
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://127.0.0.1:80';

export default function () {
  // 1. Probar carga de la UI principal (index.html)
  const homeRes = http.get(`${BASE_URL}/`);
  check(homeRes, {
    'GET / status is 200': (r) => r.status === 200,
    'GET / contains title': (r) => r.body && r.body.includes('Extractor de Documentos PDF'),
  });

  // 2. Probar endpoint de health check estático de Nginx
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'GET /health status is 200': (r) => r.status === 200,
    'GET /health content-type is json': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
    'GET /health status is ok': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'ok' && body.service === 'frontend';
      } catch {
        return false;
      }
    },
  });

  // 3. Probar carga de archivo de configuración en runtime
  const configRes = http.get(`${BASE_URL}/config.js`);
  check(configRes, {
    'GET /config.js status is 200': (r) => r.status === 200,
    'GET /config.js has no-cache header': (r) => {
      const cacheControl = r.headers['Cache-Control'] || '';
      return cacheControl.includes('no-cache');
    },
  });

  sleep(0.5);
}
