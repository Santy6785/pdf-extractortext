"""
Servicio de aplicación para la gestión del ciclo de vida de documentos.
Operaciones CRUD (consulta, actualización, eliminación) sobre documentos existentes.
La ingesta de nuevos PDFs es responsabilidad de DocumentIngestionService.
"""

from typing import List, Optional

from app.domain.repositories.document_repository import DocumentRepository
from app.application.dto.document_dto import (
    DocumentResponseDTO,
    DocumentListDTO
)


class DocumentService:
    """
    Servicio de aplicación para gestionar documentos existentes.

    Responsabilidad única: operaciones CRUD sobre documentos ya almacenados.
    """

    def __init__(self, repository: DocumentRepository):
        """
        Inicializa el servicio con sus dependencias.

        Args:
            repository: Repositorio de documentos
        """
        self._repository = repository

    async def get_all(self, limit: int, skip: int = 0) -> List[DocumentListDTO]:
        """
        Obtiene todos los documentos en formato resumido con paginación.

        Args:
            skip: Número de documentos a saltar (offset)
            limit: Número máximo de documentos a retornar

        Returns:
            Lista de documentos resumidos
        """
        documents = await self._repository.find_all(skip=skip, limit=limit)
        return [DocumentListDTO.from_entity(doc) for doc in documents]

    async def get_by_id(self, document_id: str) -> Optional[DocumentResponseDTO]:
        """
        Obtiene un documento por su ID completo.

        Args:
            document_id: ID del documento

        Returns:
            Documento completo o None
        """
        document = await self._repository.find_by_id(document_id)
        if document:
            return DocumentResponseDTO.from_entity(document)
        return None

    async def update(self, document_id: str, extracted_text: str) -> Optional[DocumentResponseDTO]:
        """
        Actualiza el texto extraído de un documento por su ID.

        Args:
            document_id: ID del documento a actualizar
            extracted_text: Nuevo texto extraído

        Returns:
            Documento actualizado o None si no existía
        """
        # Obtener documento existente
        existing = await self._repository.find_by_id(document_id)
        if existing is None:
            return None

        # Actualizar solo el texto extraído
        existing.extracted_text = extracted_text

        # Guardar cambios
        updated = await self._repository.update(document_id, existing)
        if not updated:
            return None

        return DocumentResponseDTO.from_entity(existing)

    async def delete(self, document_id: str) -> bool:
        """
        Elimina un documento por su ID.

        Args:
            document_id: ID del documento a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self._repository.delete(document_id)
