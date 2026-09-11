"""
Capa de servicio de configuración que abstrae el acceso a la configuración de la aplicación.
Implementa el principio Dependency Inversion: la capa API depende de una abstracción,
no de un módulo concreto de configuración.
"""

from typing import Protocol
from app.config.settings import Settings, get_settings as original_get_settings


class ConfigService(Protocol):
    """Protocolo para el servicio de configuración."""

    def get_max_pdf_size_mb(self) -> int: ...
    def get_app_name(self) -> str: ...
    def get_app_version(self) -> str: ...
    def is_debug(self) -> bool: ...


def get_config_service() -> ConfigService:
    """
    Factory que proporciona una instancia configurada de ConfigService.
    
    Returns:
        Implementación concreta que envuelve get_settings()
    """
    
    class ConcreteConfigService:
        def __init__(self) -> None:
            self._settings = original_get_settings()
        
        def get_max_pdf_size_mb(self) -> int:
            return self._settings.max_pdf_size_mb
        
        def get_app_name(self) -> str:
            return self._settings.app_name
        
        def get_app_version(self) -> str:
            return self._settings.app_version
        
        def is_debug(self) -> bool:
            return self._settings.debug
    
    return ConcreteConfigService()