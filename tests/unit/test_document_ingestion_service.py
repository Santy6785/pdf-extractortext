"""
Tests unitarios para el servicio de aplicación DocumentIngestionService.
Responsable del pipeline de ingesta de PDFs: procesar, validar unicidad y persistir.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_ingestion_service_process_and_save_success():
    """Test que procesa y guarda un documento nuevo exitosamente."""
    from app.application.services.document_ingestion_service import DocumentIngestionService
    from app.application.pdf.pdf_extractor import PdfProcessingResult

    # Mocks
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    mock_repo.insert = AsyncMock(return_value="new-doc-id")

    mock_pdf_extractor = MagicMock()
    mock_pdf_extractor.process_pdf = MagicMock(return_value=PdfProcessingResult(
        checksum="abc123",
        extracted_text="texto extraido"
    ))

    service = DocumentIngestionService(
        repository=mock_repo,
        pdf_extractor=mock_pdf_extractor
    )

    file_bytes = b"test pdf content"
    result = await service.process_and_save(file_bytes, "test.pdf")

    assert result.is_valid is True
    assert result.document is not None
    assert result.document.id == "new-doc-id"
    assert result.document.checksum == "abc123"
    assert result.document.extracted_text == "texto extraido"

    # Verify process_pdf was called once with the file bytes
    mock_pdf_extractor.process_pdf.assert_called_once_with(file_bytes)


@pytest.mark.asyncio
async def test_ingestion_service_process_duplicate_checksum():
    """Test que rechaza documento con checksum duplicado."""
    from app.application.services.document_ingestion_service import DocumentIngestionService
    from app.domain.models.document import Document
    from app.application.pdf.pdf_extractor import PdfProcessingResult

    # Documento existente (solo campos requeridos)
    existing_doc = Document(
        checksum="duplicate-checksum",
        extracted_text="old text",
        created_at=datetime.now(),
        id="existing-id"
    )

    # Mocks
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=existing_doc)

    mock_pdf_extractor = MagicMock()
    mock_pdf_extractor.process_pdf = MagicMock(return_value=PdfProcessingResult(
        checksum="duplicate-checksum",
        extracted_text="new text"
    ))

    service = DocumentIngestionService(
        repository=mock_repo,
        pdf_extractor=mock_pdf_extractor
    )

    file_bytes = b"content"
    result = await service.process_and_save(file_bytes, "new.pdf")

    assert result.is_valid is False
    assert result.document is None
    assert "409 Conflict" in result.error_message or "already exists" in result.error_message

    # Verify process_pdf was called
    mock_pdf_extractor.process_pdf.assert_called_once_with(file_bytes)


@pytest.mark.asyncio
async def test_ingestion_service_document_has_only_required_fields():
    """Test que el documento creado tiene solo los 4 campos requeridos."""
    from app.application.services.document_ingestion_service import DocumentIngestionService
    from app.application.pdf.pdf_extractor import PdfProcessingResult
    from dataclasses import fields

    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    mock_repo.insert = AsyncMock(return_value="doc-id")

    mock_pdf_extractor = MagicMock()
    mock_pdf_extractor.process_pdf = MagicMock(return_value=PdfProcessingResult(
        checksum="abc123",
        extracted_text="texto extraido"
    ))

    service = DocumentIngestionService(
        repository=mock_repo,
        pdf_extractor=mock_pdf_extractor
    )

    file_bytes = b"content"
    result = await service.process_and_save(file_bytes, "test.pdf")

    assert result.is_valid is True
    document = result.document

    # Verificar que tiene exactamente 4 campos
    document_fields = {f.name for f in fields(document)}
    assert document_fields == {"id", "checksum", "extracted_text", "created_at"}

    # Verificar valores
    assert document.checksum == "abc123"
    assert document.extracted_text == "texto extraido"
    assert isinstance(document.created_at, datetime)
