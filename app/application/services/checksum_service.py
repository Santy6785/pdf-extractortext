"""
Servicio de aplicación para cálculo de checksum y validación de unicidad.
No crea entidades de dominio; esa responsabilidad pertenece a DocumentIngestionService.
"""

import hashlib
from typing import Optional

from app.application.dto.document_dto import (
    DocumentCreateDTO,
    ChecksumValidationResult
)
from app.domain.repositories.document_repository import DocumentRepository


class ChecksumService:
    """
    Servicio que encapsula la lógica de negocio para validación de checksum.

    Responsabilidades:
    - Calcular checksum SHA-256 de archivos
    - Verificar unicidad de documentos
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
    
    async def validate(
        self,
        dto: DocumentCreateDTO
    ) -> ChecksumValidationResult:
        """
        Valida la unicidad del checksum de un documento a crear.

        Args:
            dto: DTO con los datos del documento. Si incluye checksum,
                 se usa ese valor; si no, se calcula desde file_bytes.

        Returns:
            Resultado de la validación con el checksum validado
            o mensaje de error si es duplicado
        """
        # Usar checksum pre-calculado si está disponible, sino calcularlo
        checksum = dto.checksum if dto.checksum is not None else self.calculate_checksum(dto.file_bytes)

        # Verificar unicidad
        if not await self.is_checksum_unique(checksum):
            return ChecksumValidationResult(
                is_valid=False,
                checksum=None,
                error_message=f"Document with checksum {checksum} already exists (409 Conflict)"
            )

        return ChecksumValidationResult(
            is_valid=True,
            checksum=checksum,
            error_message=None
        )
