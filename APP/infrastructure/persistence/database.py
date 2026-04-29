"""
Gestor de conexión a MongoDB usando motor.
Implementa el patrón Singleton para la conexión.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.settings import get_settings


class Database:
    """
    Gestor de conexión a MongoDB.
    
    Responsabilidades:
    - Mantener una única instancia de conexión (Singleton)
    - Proveer acceso a la base de datos y colecciones
    - Manejar conexión y desconexión
    """
    
    _instance = None
    _client: AsyncIOMotorClient = None
    _db: AsyncIOMotorDatabase = None
    
    def __new__(cls):
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """
        Establece la conexión a MongoDB.
        Carga configuración desde variables de entorno (12-Factor App).
        """
        settings = get_settings()
        
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.mongodb_url)
            self._db = self._client[settings.mongodb_db_name]
    
    async def disconnect(self):
        """Cierra la conexión a MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """Retorna el cliente de MongoDB."""
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Retorna la base de datos."""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db
    
    def get_collection(self, name: str):
        """
        Obtiene una colección de MongoDB.
        
        Args:
            name: Nombre de la colección
            
        Returns:
            Colección de MongoDB
        """
        return self.database[name]


# Instancia global del gestor de base de datos
database = Database()


def get_database() -> Database:
    """Retorna la instancia global del gestor de base de datos."""
    return database


def get_documents_collection():
    """
    Retorna la colección de documentos.
    
    Returns:
        Colección 'documents' de MongoDB
    """
    return database.get_collection("documents")
