// Plantilla para inyección de variables de entorno mediante envsubst al arrancar el contenedor
window.__CONFIG__ = {
  API_BASE_PATH: "${API_BASE_PATH}",
  MAX_UPLOAD_MB: Number("${MAX_UPLOAD_MB}") || 10,
  REQUEST_TIMEOUT_MS: Number("${REQUEST_TIMEOUT_MS}") || 30000
};
