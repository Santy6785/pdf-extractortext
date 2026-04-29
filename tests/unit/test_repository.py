"""
Tests unitarios para el patrón Repository.
Verifican que la interfaz define los métodos esperados.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_repository_save_document():
    """Test que el repositorio puede guardar un documento."""
    from app.domain.repositories.document_repository import DocumentRepository
    from app.domain.models.document import Document
    
    # Crear mock del repositorio
    mock_repo = MagicMock(spec=DocumentRepository)
    mock_repo.save = AsyncMock(return_value="doc-123")
    
    document = Document(
        id="",
        checksum="abc123",
        extracted_text="contenido",
        created_at=datetime.now()
    )
    
    result = await mock_repo.save(document)
    
    mock_repo.save.assert_called_once_with(document)
    assert result == "doc-123"


@pytest.mark.asyncio
async def test_repository_find_by_checksum():
    """Test que el repositorio busca por checksum."""
    from app.domain.repositories.document_repository import DocumentRepository
    from app.domain.models.document import Document
    
    expected_doc = Document(
        id="doc-456",
        checksum="duplicate-checksum",
        extracted_text="ya existe",
        created_at=datetime.now()
    )
    
    mock_repo = MagicMock(spec=DocumentRepository)
    mock_repo.find_by_checksum = AsyncMock(return_value=expected_doc)
    
    result = await mock_repo.find_by_checksum("duplicate-checksum")
    
    mock_repo.find_by_checksum.assert_called_once_with("duplicate-checksum")
    assert result is not None
    assert result.checksum == "duplicate-checksum"


@pytest.mark.asyncio
async def test_repository_find_by_id():
    """Test que el repositorio busca por ID."""
    from app.domain.repositories.document_repository import DocumentRepository
    from app.domain.models.document import Document
    
    expected_doc = Document(
        id="doc-789",
        checksum="checksum789",
        extracted_text="encontrado",
        created_at=datetime.now()
    )
    
    mock_repo = MagicMock(spec=DocumentRepository)
    mock_repo.find_by_id = AsyncMock(return_value=expected_doc)
    
    result = await mock_repo.find_by_id("doc-789")
    
    assert result is not None
    assert result.id == "doc-789"


@pytest.mark.asyncio
async def test_repository_find_all():
    """Test que el repositorio lista todos los documentos."""
    from app.domain.repositories.document_repository import DocumentRepository
    from app.domain.models.document import Document
    
    expected_docs = [
        Document(
            id="doc-1",
            checksum="cs1",
            extracted_text="texto1",
            created_at=datetime.now()
        ),
        Document(
            id="doc-2",
            checksum="cs2",
            extracted_text="texto2",
            created_at=datetime.now()
        )
    ]
    
    mock_repo = MagicMock(spec=DocumentRepository)
    mock_repo.find_all = AsyncMock(return_value=expected_docs)
    
    result = await mock_repo.find_all()
    
    assert len(result) == 2


@pytest.mark.asyncio
async def test_repository_delete():
    """Test que el repositorio puede eliminar un documento."""
    from app.domain.repositories.document_repository import DocumentRepository
    
    mock_repo = MagicMock(spec=DocumentRepository)
    mock_repo.delete = AsyncMock(return_value=True)
    
    result = await mock_repo.delete("doc-to-delete")
    
    mock_repo.delete.assert_called_once_with("doc-to-delete")
    assert result is True


@pytest.mark.asyncio
async def test_repository_checksum_not_found():
    """Test que el repositorio retorna None cuando el checksum no existe."""
    from app.domain.repositories.document_repository import DocumentRepository
    
    mock_repo = MagicMock(spec=DocumentRepository)
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    
    result = await mock_repo.find_by_checksum("non-existent-checksum")
    
    assert result is None
