"""
Dependencias de FastAPI para inyección de dependencias.
Proporciona acceso a servicios y repositorios configurados.
"""

from fastapi import Request

from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
from app.infrastructure.persistence.database import get_documents_collection
from app.application.services.document_service import DocumentService


def get_document_repository() -> DocumentRepository:
    """
    Factory que proporciona un repositorio de documentos configurado.
    
    Returns:
        Implementación de DocumentRepository con MongoDB
    """
    collection = get_documents_collection()
    return MongoDocumentRepository(collection)


def get_document_service() -> DocumentService:
    """
    Factory que proporciona un servicio de documentos configurado.
    
    Returns:
        DocumentService con todas sus dependencias inyectadas
    """
    repository = get_document_repository()
    return DocumentService(repository)
