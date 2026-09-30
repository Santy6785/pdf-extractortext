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
    async def insert(self, document: Document) -> str:
        """Inserta un documento nuevo en el almacenamiento persistente.

        Args:
            document: Entidad Document que contiene checksum, texto extraído
                y fecha de creación.

        Returns:
            str: Identificador único generado por el motor de persistencia (ObjectId en string).

        Raises:
            DomainError: Si ocurre un error de persistencia o violación de unicidad de checksum.
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
    async def find_all(self, limit: int, skip: int = 0) -> List[Document]:
        """
        Obtiene todos los documentos almacenados con paginación.

        Args:
            skip: Número de documentos a saltar (offset)
            limit: Número máximo de documentos a retornar

        Returns:
            Lista de documentos
        """
        pass

    @abstractmethod
    async def update(self, document_id: str, document: Document) -> bool:
        """Actualiza un documento existente identificado por su document_id.

        Args:
            document_id: Identificador único en formato string del documento a modificar.
            document: Entidad Document con los datos actualizados a persistir.

        Returns:
            bool: True si el documento existía y fue modificado exitosamente; False si no se encontró.

        Raises:
            DomainError: Si el identificador no tiene formato válido o la operación de base de datos falla.
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
