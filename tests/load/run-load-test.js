/**
 * Ejecutor autónomo de pruebas de carga en Node.js (alternativa ligera a k6).
 * Mide latencia (p50, p95, p99), requests por segundo (RPS) y tasa de errores.
 * 
 * Uso:
 *   node tests/load/run-load-test.js [targetUrl] [totalRequests] [concurrency]
 */

import http from 'node:http';
import https from 'node:https';

const targetUrl = process.argv[2] || 'http://127.0.0.1:8000';
const totalRequests = Number(process.argv[3]) || 500;
const concurrency = Number(process.argv[4]) || 20;

console.log(`[Load Test] Iniciando prueba de carga contra ${targetUrl}`);
console.log(`[Load Test] Peticiones totales: ${totalRequests}, Concurrencia: ${concurrency}`);

function makeRequest(url) {
  const parsed = new URL(url);
  const client = parsed.protocol === 'https:' ? https : http;
  const start = performance.now();

  return new Promise((resolve) => {
    const req = client.get(url, (res) => {
      res.resume(); // Consumir respuesta
      res.on('end', () => {
        const duration = performance.now() - start;
        resolve({ ok: res.statusCode >= 200 && res.statusCode < 400, status: res.statusCode, duration });
      });
    });

    req.on('error', (err) => {
      const duration = performance.now() - start;
      resolve({ ok: false, status: 0, duration, error: err.message });
    });

    req.setTimeout(5000, () => {
      req.destroy();
      const duration = performance.now() - start;
      resolve({ ok: false, status: 408, duration, error: 'Timeout' });
    });
  });
}

async function runWorker(queue, results) {
  while (queue.length > 0) {
    const url = queue.pop();
    if (!url) break;
    const res = await makeRequest(url);
    results.push(res);
  }
}

async function main() {
  const endpoints = ['/', '/health', '/config.js'];
  const queue = [];
  for (let i = 0; i < totalRequests; i++) {
    const endpoint = endpoints[i % endpoints.length];
    queue.push(`${targetUrl.replace(/\/$/, '')}${endpoint}`);
  }

  const results = [];
  const startTime = performance.now();

  const workers = [];
  for (let i = 0; i < concurrency; i++) {
    workers.push(runWorker(queue, results));
  }

  await Promise.all(workers);

  const totalTimeSec = (performance.now() - startTime) / 1000;
  const successful = results.filter((r) => r.ok).length;
  const failed = results.filter((r) => !r.ok).length;
  const durations = results.map((r) => r.duration).sort((a, b) => a - b);

  const p50 = durations[Math.floor(durations.length * 0.50)]?.toFixed(2) || 0;
  const p95 = durations[Math.floor(durations.length * 0.95)]?.toFixed(2) || 0;
  const p99 = durations[Math.floor(durations.length * 0.99)]?.toFixed(2) || 0;
  const rps = (results.length / totalTimeSec).toFixed(2);

  console.log('\n================ RESULTADOS DE CARGA ================');
  console.log(`Tiempo total:       ${totalTimeSec.toFixed(2)}s`);
  console.log(`Peticiones totales: ${results.length}`);
  console.log(`Exitosas:           ${successful}`);
  console.log(`Fallidas:           ${failed}`);
  console.log(`RPS (Req/seg):      ${rps}`);
  console.log(`Latencia p50:       ${p50}ms`);
  console.log(`Latencia p95:       ${p95}ms`);
  console.log(`Latencia p99:       ${p99}ms`);
  console.log('====================================================\n');
}

main().catch(console.error);
