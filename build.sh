#!/usr/bin/env bash
# ==============================================================================
# Script de Build y Verificación para el Microservicio Front-End
# Ejecuta linting + todas las pruebas y SOLO si pasan construye la imagen Docker.
# ==============================================================================

set -euo pipefail

IMAGE_NAME="pdf-frontend"
IMAGE_TAG="0.2.0"

echo "========================================================"
echo " [1/4] Ejecutando análisis estático y linter (JS/Python)"
echo "========================================================"
npm run lint

echo "========================================================"
echo " [2/4] Ejecutando tests unitarios y de integración FRONT"
echo "========================================================"
npm test

echo "========================================================"
echo " [3/4] Ejecutando suite completa de tests BACKEND / E2E "
echo "========================================================"
if command -v uv >/dev/null 2>&1; then
    uv run pytest
elif [ -f ".venv/bin/pytest" ]; then
    .venv/bin/pytest
elif [ -f ".venv/Scripts/pytest.exe" ]; then
    .venv/Scripts/pytest.exe
else
    python3 -m pytest
fi

echo "========================================================"
echo " [4/4] Pruebas aprobadas. Construyendo imagen Docker... "
echo "========================================================"
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        docker build -f Dockerfile.frontend -t "${IMAGE_NAME}:${IMAGE_TAG}" -t "${IMAGE_NAME}:latest" .
        echo "========================================================"
        echo " ✔ Build exitoso: ${IMAGE_NAME}:${IMAGE_TAG}"
        echo "========================================================"
    else
        echo "⚠ Docker CLI disponible pero el demonio Docker no está en ejecución."
        echo "  La verificación de código y tests pasó al 100%."
    fi
else
    echo "⚠ Docker no disponible en este entorno. Tests aprobados al 100%."
fi
