from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.api.routes import router
from app.api.dependencies import get_database
from app.config.settings import get_settings


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
    settings = get_settings()
    app = FastAPI(
        title="Extractor de Documentos PDF",
        description="API para extraer texto y metadatos de archivos PDF con persistencia en MongoDB",
        version=settings.app_version,
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
    
    # Incluir rutas de la API (incluye el health check en /api/v1/health)
    app.include_router(router)

    return app


# Crear instancia de la app para uvicorn
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)