"""
Dependencias de FastAPI para inyección de dependencias.
Proporciona acceso a servicios y repositorios configurados.
Es el composition root único para todas las dependencias de infraestructura.
"""

from fastapi import Request

from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
from app.infrastructure.persistence.database import Database, get_documents_collection
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


def get_database_instance() -> Database:
    """
    Factory que proporciona la instancia de base de datos configurada.
    
    Returns:
        Instancia de Database conectada a MongoDB
    """
    from app.infrastructure.persistence.database import database as _db
    return _db

# Alias for FastAPI dependency injection compatibility
get_database = get_database_instance
