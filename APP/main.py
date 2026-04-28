"""
Punto de entrada de la aplicación FastAPI.
Configura y crea la aplicación con sus rutas.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router


# Obtener la ruta absoluta del directorio static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "api", "static")


def create_app() -> FastAPI:
    """
    Factory para crear la aplicación FastAPI.
    Permite configuración flexible y testing.
    """
    app = FastAPI(
        title="Extractor de Documentos PDF",
        description="API para extraer texto y metadatos de archivos PDF",
        version="0.1.0",
    )

    # Montar archivos estáticos
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Incluir rutas de la API
    app.include_router(router)

    # Ruta raíz que sirve el index.html
    @app.get("/")
    async def root():
        """Sirve la interfaz web principal."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    return app


# Crear instancia de la app para uvicorn
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
