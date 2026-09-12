"""
Servicio de aplicación para operaciones CRUD de documentos.
Integra procesamiento de PDF, validación de checksum y persistencia.
"""

from typing import List, Optional

from app.domain.models.document import Document
from app.domain.repositories.document_repository import DocumentRepository
from app.application.pdf.pdf_extractor import PdfExtractor, PdfProcessingResult
from app.application.services.checksum_service import ChecksumService
from app.application.dto.document_dto import (
    DocumentCreateDTO,
    DocumentResponseDTO,
    DocumentListDTO,
    ChecksumValidationResult
)
from app.infrastructure.pdf.pypdf_extractor import PypdfPdfExtractor


class DocumentServiceError(Exception):
    """Excepción para errores del servicio de documentos."""
    pass


class DocumentService:
    """
    Servicio de aplicación que orquesta el procesamiento y almacenamiento de documentos.
    
    Responsabilidades:
    - Procesar archivos PDF
    - Validar unicidad mediante checksum
    - Persistir documentos
    - Gestionar operaciones CRUD
    """
    
    def __init__(
        self,
        repository: DocumentRepository,
        pdf_extractor: PdfExtractor = None,
        checksum_service: Optional[ChecksumService] = None
    ):
        """
        Inicializa el servicio con sus dependencias.
        
        Args:
            repository: Repositorio de documentos
            pdf_extractor: Extractor de PDFs (opcional)
            checksum_service: Servicio de validación de checksum (opcional)
        """
        self._repository = repository
        self._pdf_extractor = pdf_extractor or PypdfPdfExtractor()
        self._checksum_service = checksum_service or ChecksumService(repository)
    
    async def process_and_save(
        self,
        file_bytes: bytes,
        filename: str
    ) -> ChecksumValidationResult:
        """
        Procesa un archivo PDF y lo guarda si es único.
        
        Args:
            file_bytes: Contenido del archivo
            filename: Nombre del archivo (solo para logging, no se almacena)
            
        Returns:
            Resultado de la validación y persistencia
            
        Raises:
            DocumentServiceError: Si hay error al procesar el PDF
        """
        try:
            # 1. Procesar PDF usando el extractor (extrae texto y calcula checksum en una sola pasada)
            pdf_result = self._pdf_extractor.process_pdf(file_bytes)
            
            # 2. Crear DTO para validación con el checksum ya calculado
            create_dto = DocumentCreateDTO(
                file_bytes=file_bytes,
                extracted_text=pdf_result.extracted_text,
                checksum=pdf_result.checksum
            )
            
            # 3. Validar checksum y crear documento (reutiliza el checksum del DTO)
            validation_result = await self._checksum_service.validate_and_create_document(
                create_dto
            )
            
            if not validation_result.is_valid:
                return validation_result
            
            # 4. Guardar en base de datos
            document = validation_result.document
            document_id = await self._repository.save(document)
            document.id = document_id
            
            return ChecksumValidationResult(
                is_valid=True,
                document=document,
                error_message=None
            )
            
        except Exception as e:
            raise DocumentServiceError(f"Error processing document: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 20) -> List[DocumentListDTO]:
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

    
