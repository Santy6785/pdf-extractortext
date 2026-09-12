"""
Dominio - Capa central de la arquitectura limpia.
Contiene entidades, interfaces de repositorio y excepciones de dominio.
"""

from app.domain.exceptions import DocumentNotFoundError, DomainError
from app.domain.models.document import Document
from app.domain.repositories.document_repository import DocumentRepository

__all__ = [
    "Document",
    "DocumentRepository",
    "DocumentNotFoundError",
    "DomainError",
]