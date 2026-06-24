FROM python:3.12-slim

WORKDIR /app

#Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off  \
    PIP_DISABLE_PIP_VERSION_CHECK=on

#Instalar dependencias del sistema necesarias para PyPDF2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalamos uv de forma correcta
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

#Copiar archivos de dependencias
COPY pyproject.toml ./
COPY uv.lock ./

#Sincronizar dependencias con uv
RUN uv pip install --system . uvicorn

#Copiar codigo fuente
COPY . .

#Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

#Puerto expuesto
EXPOSE 8000

#Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \ 
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

#Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]