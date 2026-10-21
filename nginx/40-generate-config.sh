#!/bin/sh
set -e

# Asignar valores por defecto a variables de entorno si no existen
export API_BASE_PATH="${API_BASE_PATH:-}"
export MAX_UPLOAD_MB="${MAX_UPLOAD_MB:-10}"
export REQUEST_TIMEOUT_MS="${REQUEST_TIMEOUT_MS:-30000}"

# Generar config.js desde config.template.js reemplazando únicamente las variables de configuración
if [ -f /usr/share/nginx/html/config.template.js ]; then
    envsubst '$API_BASE_PATH $MAX_UPLOAD_MB $REQUEST_TIMEOUT_MS' < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js
    echo "[Entrypoint] Generado config.js con API_BASE_PATH='${API_BASE_PATH}', MAX_UPLOAD_MB=${MAX_UPLOAD_MB}, REQUEST_TIMEOUT_MS=${REQUEST_TIMEOUT_MS}"
fi
