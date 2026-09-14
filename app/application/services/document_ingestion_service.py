"""
Servicio de aplicación para la ingesta de documentos PDF.
Orquesta el procesamiento de PDF, la validación de checksum/unicidad
y la persistencia de documentos nuevos.
"""

from typing import Optional

from app.domain.models.document import Document
from app.domain.repositories.document_repository import DocumentRepository
from app.application.pdf.pdf_extractor import PdfExtractor, PdfProcessingResult
from app.application.services.checksum_service import ChecksumService
from app.application.dto.document_dto import (
    DocumentCreateDTO,
    ChecksumValidationResult
)


class DocumentIngestionService:
    """
    Servicio de aplicación que orquesta la ingesta de documentos PDF.

    Responsabilidad única: recibir bytes de un PDF, extraer su contenido,
    validar unicidad por checksum y persistir el documento resultante.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        pdf_extractor: PdfExtractor,
        checksum_service: Optional[ChecksumService] = None
    ):
        """
        Inicializa el servicio con sus dependencias.

        Args:
            repository: Repositorio de documentos
            pdf_extractor: Extractor de PDFs (abstracción)
            checksum_service: Servicio de validación de checksum (opcional)
        """
        self._repository = repository
        self._pdf_extractor = pdf_extractor
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

            # 2. Construir DTO de creación con el checksum ya calculado
            create_dto = self._build_create_dto(file_bytes, pdf_result)

            # 3. Validar checksum y crear documento (reutiliza el checksum del DTO)
            validation_result = await self._checksum_service.validate_and_create_document(
                create_dto
            )

            if not validation_result.is_valid:
                return validation_result

            # 4. Persistir el documento
            document = await self._save_document(validation_result.document)

            return ChecksumValidationResult(
                is_valid=True,
                document=document,
                error_message=None
            )

        except Exception as e:
            raise DocumentServiceError(f"Error processing document: {str(e)}")

    @staticmethod
    def _build_create_dto(file_bytes: bytes, pdf_result: PdfProcessingResult) -> DocumentCreateDTO:
        """
        Construye el DTO de creación a partir del resultado del procesamiento del PDF.

        Args:
            file_bytes: Contenido del archivo original
            pdf_result: Resultado del extractor (texto y checksum)

        Returns:
            DTO listo para validación de checksum
        """
        return DocumentCreateDTO(
            file_bytes=file_bytes,
            extracted_text=pdf_result.extracted_text,
            checksum=pdf_result.checksum
        )

    async def _save_document(self, document: Document) -> Document:
        """
        Persiste un documento en el repositorio y le asigna el ID generado.

        Args:
            document: Documento a persistir

        Returns:
            El mismo documento con su ID asignado
        """
        document.id = await self._repository.insert(document)
        return document


class DocumentServiceError(Exception):
    """Excepción para errores del servicio de ingesta de documentos."""
    pass
