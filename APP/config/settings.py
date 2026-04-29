"""
Configuración de la aplicación siguiendo 12-Factor App.
Todas las configuraciones se cargan desde variables de entorno.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "pdf_extractor"
    
    # App
    app_name: str = "PDF Extractor API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna una instancia cacheada de Settings.
    El cacheo evita recargar las variables de entorno en cada uso.
    """
    return Settings()
