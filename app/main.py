from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.api.routes import router
from app.api.dependencies import get_database, get_document_service, create_app_with_deps


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    
    - Conecta a MongoDB al iniciar
    - Desconecta al cerrar
    """
    # Startup: Conectar a MongoDB
    database = get_database()
    await database.connect()
    # Almacenar en app.state para que esté disponible en los endpoints
    app.state.database = database
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
    
    # Configurar CORS para permitir peticiones desde el frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, restringir a los dominios específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Incluir rutas de la API (sin montar archivos estáticos)
    app.include_router(router)
    
    # Health check a nivel de aplicación (sin prefijo de versión API)
    @app.get("/health", status_code=status.HTTP_200_OK)
    async def health_check():
        """
        Endpoint de health check para verificar el estado del sistema.
        
        Returns:
            Estado saludable o no saludable con información de la base de datos
        """
        is_db_connected = app.state.database.is_connected()
        status_info = {
            "status": "healthy" if is_db_connected else "unhealthy",
            "database": "connected" if is_db_connected else "disconnected",
            "version": "0.2.0"
        }
        if is_db_connected:
            return status_info
        return JSONResponse(status_code=503, content=status_info)
    
    return app


# Crear instancia de la app para uvicorn
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)