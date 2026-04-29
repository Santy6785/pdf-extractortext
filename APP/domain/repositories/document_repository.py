"""
Interfaz del patrón Repository para Document.
Define el contrato que cualquier implementación debe cumplir.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.document import Document


class DocumentRepository(ABC):
    """
    Interfaz abstracta para el repositorio de documentos.
    
    Esta interfaz define el contrato que cualquier implementación
    de persistencia debe cumplir (MongoDB, PostgreSQL, etc.).
    """
    
    @abstractmethod
    async def save(self, document: Document) -> str:
        """
        Guarda un documento en la base de datos.
        
        Args:
            document: Documento a guardar
            
        Returns:
            ID del documento guardado
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """
        Busca un documento por su ID.
        
        Args:
            document_id: ID del documento
            
        Returns:
            Documento encontrado o None
        """
        pass
    
    @abstractmethod
    async def find_by_checksum(self, checksum: str) -> Optional[Document]:
        """
        Busca un documento por su checksum.
        Útil para verificar unicidad.
        
        Args:
            checksum: Hash SHA-256 del archivo
            
        Returns:
            Documento encontrado o None
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Document]:
        """
        Obtiene todos los documentos almacenados.
        
        Returns:
            Lista de documentos
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """
        Elimina un documento por su ID.
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        pass
