"""
Servicio de aplicación para validación de checksum y unicidad de documentos.
"""

import hashlib
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.application.dto.document_dto import (
    DocumentCreateDTO,
    ChecksumValidationResult
)
from app.domain.models.document import Document
from app.domain.repositories.document_repository import DocumentRepository


class ChecksumService:
    """
    Servicio que encapsula la lógica de negocio para validación de checksum.
    
    Responsabilidades:
    - Calcular checksum SHA-256 de archivos
    - Verificar unicidad de documentos
    - Crear documentos válidos
    """
    
    def __init__(self, repository: Optional[DocumentRepository] = None):
        """
        Inicializa el servicio con un repositorio opcional.
        
        Args:
            repository: Repositorio de documentos para verificar unicidad
        """
        self._repository = repository
    
    def calculate_checksum(self, file_bytes: bytes) -> str:
        """
        Calcula el checksum SHA-256 de los bytes del archivo.
        
        Args:
            file_bytes: Contenido del archivo en bytes
            
        Returns:
            Hash SHA-256 en formato hexadecimal
        """
        return hashlib.sha256(file_bytes).hexdigest()
    
    async def is_checksum_unique(self, checksum: str) -> bool:
        """
        Verifica si un checksum ya existe en la base de datos.
        
        Args:
            checksum: Hash a verificar
            
        Returns:
            True si el checksum es único (no existe), False si ya existe
        """
        if self._repository is None:
            return True
            
        existing = await self._repository.find_by_checksum(checksum)
        return existing is None
    
    async def validate_and_create_document(
        self,
        dto: DocumentCreateDTO
    ) -> ChecksumValidationResult:
        """
        Valida la unicidad del checksum y crea un documento si es válido.
        
        Args:
            dto: DTO con los datos del documento a crear
            
        Returns:
            Resultado de la validación con el documento creado o mensaje de error
        """
        # Calcular checksum del archivo
        checksum = self.calculate_checksum(dto.file_bytes)
        
        # Verificar unicidad
        if not await self.is_checksum_unique(checksum):
            return ChecksumValidationResult(
                is_valid=False,
                document=None,
                error_message=f"Document with checksum {checksum} already exists (409 Conflict)"
            )
        
        # Crear documento de dominio
        document = Document(
            id=str(ObjectId()),
            checksum=checksum,
            extracted_text=dto.extracted_text,
            created_at=datetime.now()
        )
        
        return ChecksumValidationResult(
            is_valid=True,
            document=document,
            error_message=None
        )
