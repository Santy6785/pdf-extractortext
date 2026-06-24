from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import uvicorn

from app.api.routes import router
from app.infrastructure.persistence.database import database


# Obtener la ruta absoluta del directorio static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "api", "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    
    - Conecta a MongoDB al iniciar
    - Desconecta al cerrar
    """
    # Startup: Conectar a MongoDB
    await database.connect()
    yield
    # Shutdown: Desconectar de MongoDB
    await database.disconnect()


def create_app() -> FastAPI:
    """
    Factory para crear la aplicación FastAPI.
    Permite configuración flexible y testing.
    """
    app = FastAPI(
        title="Extractor de Documentos PDF",
        description="API para extraer texto y metadatos de archivos PDF con persistencia en MongoDB",
        version="0.2.0",
        lifespan=lifespan
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
    
    # Health check a nivel de aplicación (sin prefijo de versión API)
    @app.get("/health", status_code=status.HTTP_200_OK)
    async def health_check():
        """Endpoint de health check para verificar el estado del sistema."""
        try:
            is_db_connected = database.is_connected()
            status_info = {
                "status": "healthy" if is_db_connected else "unhealthy",
                "database": "connected" if is_db_connected else "disconnected",
                "version": "0.2.0"
            }
            if is_db_connected:
                return status_info
            return JSONResponse(status_code=503, content=status_info)
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": str(e), "version": "0.2.0"}
            )
    
    return app


# Crear instancia de la app para uvicorn
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)