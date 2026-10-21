# ==============================================================================
# Script de Build y Verificacion para el Microservicio Front-End (PowerShell)
# Ejecuta linting + todas las pruebas y SOLO si pasan construye la imagen Docker.
# ==============================================================================

$ErrorActionPreference = "Stop"

$ImageName = "pdf-frontend"
$ImageTag = "0.2.0"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " [1/4] Ejecutando analisis estatico y linter" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
npm run lint
if ($LASTEXITCODE -ne 0) { throw "Fallo en linting" }

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " [2/4] Ejecutando tests unitarios y de integracion FRONT" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
npm test
if ($LASTEXITCODE -ne 0) { throw "Fallo en tests de frontend" }

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " [3/4] Ejecutando suite completa de tests BACKEND / E2E " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run pytest
} elseif (Test-Path ".venv\Scripts\pytest.exe") {
    & .venv\Scripts\pytest.exe
} else {
    python -m pytest
}
if ($LASTEXITCODE -ne 0) { throw "Fallo en tests de backend" }

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " [4/4] Pruebas aprobadas. Construyendo imagen Docker... " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
try {
    $dockerCheck = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker build -f Dockerfile.frontend -t "${ImageName}:${ImageTag}" -t "${ImageName}:latest" .
        Write-Host "`n========================================================" -ForegroundColor Green
        Write-Host " Build exitoso: ${ImageName}:${ImageTag}" -ForegroundColor Green
        Write-Host "========================================================" -ForegroundColor Green
    } else {
        Write-Host "Docker CLI disponible pero el demonio Docker no esta en ejecucion localmente." -ForegroundColor Yellow
        Write-Host "El codigo paso todos los linters y pruebas unitarias/integracion exitosamente." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Docker CLI disponible pero el demonio Docker no esta en ejecucion localmente." -ForegroundColor Yellow
    Write-Host "El codigo paso todos los linters y pruebas unitarias/integracion exitosamente." -ForegroundColor Yellow
}
