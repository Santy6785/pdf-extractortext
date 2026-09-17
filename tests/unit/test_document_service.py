"""
Tests unitarios para el servicio de aplicación DocumentService.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_document_service_get_all():
    """Test que obtiene todos los documentos."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document

    documents = [
        Document(
            checksum="cs1",
            extracted_text="text1",
            created_at=datetime.now(),
            id="doc-1"
        ),
        Document(
            checksum="cs2",
            extracted_text="text2",
            created_at=datetime.now(),
            id="doc-2"
        )
    ]

    mock_repo = MagicMock()
    mock_repo.find_all = AsyncMock(return_value=documents)

    service = DocumentService(repository=mock_repo)
    result = await service.get_all(limit=20)

    assert len(result) == 2
    assert result[0].checksum == "cs1"
    assert result[1].checksum == "cs2"
    # Verify pagination parameters were passed
    mock_repo.find_all.assert_called_once_with(skip=0, limit=20)


@pytest.mark.asyncio
async def test_document_service_get_all_with_pagination():
    """Test que obtiene documentos con paginación."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document

    documents = [
        Document(
            checksum="cs3",
            extracted_text="text3",
            created_at=datetime.now(),
            id="doc-3"
        )
    ]

    mock_repo = MagicMock()
    mock_repo.find_all = AsyncMock(return_value=documents)

    service = DocumentService(repository=mock_repo)
    result = await service.get_all(skip=10, limit=5)

    assert len(result) == 1
    mock_repo.find_all.assert_called_once_with(skip=10, limit=5)


@pytest.mark.asyncio
async def test_document_service_get_by_id_success():
    """Test que obtiene un documento por ID."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document
    
    doc = Document(
        checksum="cs123",
        extracted_text="texto",
        created_at=datetime.now(),
        id="doc-123"
    )
    
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=doc)
    
    service = DocumentService(repository=mock_repo)
    result = await service.get_by_id("doc-123")
    
    assert result is not None
    assert result.id == "doc-123"
    assert result.checksum == "cs123"
    assert result.extracted_text == "texto"


@pytest.mark.asyncio
async def test_document_service_get_by_id_not_found():
    """Test que retorna None cuando el documento no existe."""
    from app.application.services.document_service import DocumentService
    
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=None)
    
    service = DocumentService(repository=mock_repo)
    result = await service.get_by_id("non-existent")
    
    assert result is None


@pytest.mark.asyncio
async def test_document_service_delete_success():
    """Test que elimina un documento exitosamente."""
    from app.application.services.document_service import DocumentService
    
    mock_repo = MagicMock()
    mock_repo.delete = AsyncMock(return_value=True)
    
    service = DocumentService(repository=mock_repo)
    result = await service.delete("doc-to-delete")
    
    assert result is True


@pytest.mark.asyncio
async def test_document_service_delete_not_found():
    """Test que retorna False al eliminar documento inexistente."""
    from app.application.services.document_service import DocumentService
    
    mock_repo = MagicMock()
    mock_repo.delete = AsyncMock(return_value=False)
    
    service = DocumentService(repository=mock_repo)
    result = await service.delete("non-existent")

    assert result is False


@pytest.mark.asyncio
async def test_document_service_update_success():
    """Test que actualiza el texto extraido de un documento exitosamente."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document

    doc = Document(
        checksum="cs-upd",
        extracted_text="texto viejo",
        created_at=datetime.now(),
        id="doc-upd"
    )

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=doc)
    mock_repo.update = AsyncMock(return_value=True)

    service = DocumentService(repository=mock_repo)
    result = await service.update("doc-upd", "texto nuevo")

    assert result is not None
    assert result.id == "doc-upd"
    assert result.checksum == "cs-upd"
    assert result.extracted_text == "texto nuevo"
    mock_repo.find_by_id.assert_called_once_with("doc-upd")
    mock_repo.update.assert_called_once_with("doc-upd", doc)
    assert doc.extracted_text == "texto nuevo"


@pytest.mark.asyncio
async def test_document_service_update_not_found():
    """Test que retorna None al actualizar un documento inexistente."""
    from app.application.services.document_service import DocumentService

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value=True)

    service = DocumentService(repository=mock_repo)
    result = await service.update("non-existent", "texto")

    assert result is None
    mock_repo.find_by_id.assert_called_once_with("non-existent")
    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_document_service_update_not_modified():
    """Test que retorna None cuando el repositorio no logra actualizar."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document

    doc = Document(
        checksum="cs-fail",
        extracted_text="texto",
        created_at=datetime.now(),
        id="doc-fail"
    )

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=doc)
    mock_repo.update = AsyncMock(return_value=False)

    service = DocumentService(repository=mock_repo)
    result = await service.update("doc-fail", "texto nuevo")

    assert result is None
    mock_repo.update.assert_called_once_with("doc-fail", doc)


@pytest.mark.asyncio
async def test_document_service_error_on_processing_failure():
    """Test que DocumentServiceError se eleva ante fallas del extractor."""
    from app.application.services.document_ingestion_service import (
        DocumentIngestionService,
        DocumentServiceError,
    )

    mock_repo = MagicMock()
    mock_extractor = MagicMock()
    mock_extractor.process_pdf.side_effect = ValueError("pdf corrupto")

    service = DocumentIngestionService(
        repository=mock_repo,
        pdf_extractor=mock_extractor
    )

    with pytest.raises(DocumentServiceError) as exc_info:
        await service.process_and_save(b"bytes", "doc.pdf")

    assert "Error processing document" in str(exc_info.value)
    assert "pdf corrupto" in str(exc_info.value)


@pytest.mark.asyncio
async def test_document_service_error_on_repository_failure():
    """Test que DocumentServiceError se eleva ante fallas del repositorio."""
    from app.application.services.document_ingestion_service import (
        DocumentIngestionService,
        DocumentServiceError,
    )
    from app.application.pdf.pdf_extractor import PdfProcessingResult

    mock_repo = MagicMock()
    mock_repo.insert = AsyncMock(side_effect=RuntimeError("mongo caido"))

    mock_extractor = MagicMock()
    mock_extractor.process_pdf.return_value = PdfProcessingResult(
        extracted_text="texto",
        checksum="cs-err"
    )

    mock_checksum = MagicMock()
    validation = MagicMock(is_valid=True, checksum="cs-err")
    mock_checksum.validate = AsyncMock(return_value=validation)

    service = DocumentIngestionService(
        repository=mock_repo,
        pdf_extractor=mock_extractor,
        checksum_service=mock_checksum
    )

    with pytest.raises(DocumentServiceError) as exc_info:
        await service.process_and_save(b"bytes", "doc.pdf")

    assert "Error processing document" in str(exc_info.value)
    assert "mongo caido" in str(exc_info.value)