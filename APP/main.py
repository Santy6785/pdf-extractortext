"""
Punto de entrada de la aplicación FastAPI.
Configura y crea la aplicación con sus rutas.
"""

import uvicorn
from fastapi import FastAPI

from APP.api.routes import router


def create_app() -> FastAPI:
    """
    Factory para crear la aplicación FastAPI.
    Permite configuración flexible y testing.
    """
    app = FastAPI(
        title="PDF Extractor API",
        description="API para extraer texto y metadatos de archivos PDF",
        version="0.1.0",
    )
    
    # Incluir rutas de la API
    app.include_router(router)
    
    return app


# Crear instancia de la app para uvicorn
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
