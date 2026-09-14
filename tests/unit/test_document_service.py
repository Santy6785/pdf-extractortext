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