"""
DTOs (Data Transfer Objects) para la capa de aplicación.
Separan la representación externa de las entidades de dominio.
"""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime


@dataclass
class DocumentCreateDTO:
    """DTO para crear un nuevo documento."""
    file_bytes: bytes
    extracted_text: str


@dataclass
class DocumentResponseDTO:
    """DTO para responder con un documento completo."""
    id: str
    checksum: str
    extracted_text: str
    created_at: datetime
    
    @classmethod
    def from_entity(cls, entity) -> "DocumentResponseDTO":
        """Crea un DTO desde una entidad de dominio."""
        return cls(
            id=entity.id,
            checksum=entity.checksum,
            extracted_text=entity.extracted_text,
            created_at=entity.created_at
        )


@dataclass
class DocumentListDTO:
    """DTO para listar documentos (versión resumida)."""
    id: str
    checksum: str
    created_at: datetime
    
    @classmethod
    def from_entity(cls, entity) -> "DocumentListDTO":
        """Crea un DTO desde una entidad de dominio."""
        return cls(
            id=entity.id,
            checksum=entity.checksum,
            created_at=entity.created_at
        )


@dataclass
class ChecksumValidationResult:
    """Resultado de la validación de checksum."""
    is_valid: bool
    document: Optional[Any]
    error_message: Optional[str]
