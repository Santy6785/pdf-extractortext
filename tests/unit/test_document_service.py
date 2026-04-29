"""
Tests unitarios para el servicio de aplicación DocumentService.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_document_service_process_and_save_success():
    """Test que procesa y guarda un documento nuevo exitosamente."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document
    from app.services.pdf_service import PdfProcessingResult
    
    # Mocks
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    mock_repo.save = AsyncMock(return_value="new-doc-id")
    
    mock_pdf_service = MagicMock()
    mock_pdf_service.process_pdf = MagicMock(return_value=PdfProcessingResult(
        nombre_archivo="test.pdf",
        checksum="abc123",
        dimensiones_paginas=[{"ancho": 595.0, "alto": 842.0}],
        texto_extraido="texto extraido"
    ))
    
    service = DocumentService(
        repository=mock_repo,
        pdf_service=mock_pdf_service
    )
    
    file_bytes = b"test pdf content"
    result = await service.process_and_save(file_bytes, "test.pdf")
    
    assert result.is_valid is True
    assert result.document is not None
    assert result.document.id == "new-doc-id"
    assert result.document.checksum is not None
    assert result.document.extracted_text == "texto extraido"


@pytest.mark.asyncio
async def test_document_service_process_duplicate_checksum():
    """Test que rechaza documento con checksum duplicado."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document
    from app.services.pdf_service import PdfProcessingResult
    
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
    
    mock_pdf_service = MagicMock()
    mock_pdf_service.process_pdf = MagicMock(return_value=PdfProcessingResult(
        nombre_archivo="new.pdf",
        checksum="duplicate-checksum",
        dimensiones_paginas=[],
        texto_extraido="new text"
    ))
    
    service = DocumentService(
        repository=mock_repo,
        pdf_service=mock_pdf_service
    )
    
    file_bytes = b"content"
    result = await service.process_and_save(file_bytes, "new.pdf")
    
    assert result.is_valid is False
    assert result.document is None
    assert "409 Conflict" in result.error_message or "already exists" in result.error_message


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
    result = await service.get_all()

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
async def test_document_service_check_exists_by_checksum():
    """Test que verifica existencia por checksum."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document
    
    existing_doc = Document(
        checksum="existing-checksum",
        extracted_text="text",
        created_at=datetime.now(),
        id="doc-1"
    )
    
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=existing_doc)
    
    service = DocumentService(repository=mock_repo)
    result = await service.check_exists_by_checksum("existing-checksum")
    
    assert result is True


@pytest.mark.asyncio
async def test_document_service_document_has_only_required_fields():
    """Test que el documento creado tiene solo los 4 campos requeridos."""
    from app.application.services.document_service import DocumentService
    from app.domain.models.document import Document
    from app.services.pdf_service import PdfProcessingResult
    from dataclasses import fields
    
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    mock_repo.save = AsyncMock(return_value="doc-id")
    
    mock_pdf_service = MagicMock()
    mock_pdf_service.process_pdf = MagicMock(return_value=PdfProcessingResult(
        nombre_archivo="test.pdf",
        checksum="abc123",
        dimensiones_paginas=[{"ancho": 595.0, "alto": 842.0}],
        texto_extraido="texto extraido"
    ))
    
    service = DocumentService(
        repository=mock_repo,
        pdf_service=mock_pdf_service
    )
    
    file_bytes = b"content"
    result = await service.process_and_save(file_bytes, "test.pdf")
    
    assert result.is_valid is True
    document = result.document
    
    # Verificar que tiene exactamente 4 campos
    document_fields = {f.name for f in fields(document)}
    assert document_fields == {"id", "checksum", "extracted_text", "created_at"}
    
    # Verificar valores
    assert document.checksum is not None
    assert document.extracted_text == "texto extraido"
    assert isinstance(document.created_at, datetime)
