"""
Tests unitarios para el servicio de validación de checksum.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import hashlib


def test_calculate_checksum_sha256():
    """Test que calcula correctamente el checksum SHA-256."""
    from app.application.services.checksum_service import ChecksumService
    
    service = ChecksumService()
    test_bytes = b"test content for checksum"
    
    expected_checksum = hashlib.sha256(test_bytes).hexdigest()
    result = service.calculate_checksum(test_bytes)
    
    assert result == expected_checksum
    assert len(result) == 64  # SHA-256 produce 64 caracteres hex


@pytest.mark.asyncio
async def test_validate_checksum_new_file():
    """Test que acepta archivos con checksum nuevo."""
    from app.application.services.checksum_service import ChecksumService
    from app.application.dto.document_dto import DocumentCreateDTO
    
    # Mock del repositorio que retorna None (checksum no existe)
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    
    service = ChecksumService(repository=mock_repo)
    
    dto = DocumentCreateDTO(
        file_bytes=b"new content",
        extracted_text="texto extraído"
    )
    
    result = await service.validate_and_create_document(dto)
    
    assert result.is_valid is True
    assert result.document is not None
    assert result.error_message is None
    assert result.document.extracted_text == "texto extraído"


@pytest.mark.asyncio
async def test_validate_checksum_duplicate():
    """Test que rechaza archivos con checksum duplicado."""
    from app.application.services.checksum_service import ChecksumService
    from app.application.dto.document_dto import DocumentCreateDTO
    from app.domain.models.document import Document
    
    # Documento existente con mismo checksum (solo campos requeridos)
    existing_doc = Document(
        id="existing-id",
        checksum="duplicate-checksum",
        extracted_text="old text",
        created_at=datetime.now()
    )
    
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=existing_doc)
    
    service = ChecksumService(repository=mock_repo)
    
    dto = DocumentCreateDTO(
        file_bytes=b"content",
        extracted_text="new text"
    )
    
    result = await service.validate_and_create_document(dto)
    
    assert result.is_valid is False
    assert result.document is None
    assert "already exists" in result.error_message or "existente" in result.error_message


@pytest.mark.asyncio
async def test_check_duplicate_with_real_checksum():
    """Test que verifica duplicado con checksum real calculado."""
    from app.application.services.checksum_service import ChecksumService
    from app.application.dto.document_dto import DocumentCreateDTO
    from app.domain.models.document import Document
    
    file_content = b"identical content"
    checksum = hashlib.sha256(file_content).hexdigest()
    
    existing_doc = Document(
        id="existing-456",
        checksum=checksum,
        extracted_text="texto original",
        created_at=datetime.now()
    )
    
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=existing_doc)
    
    service = ChecksumService(repository=mock_repo)
    
    dto = DocumentCreateDTO(
        file_bytes=file_content,  # Mismo contenido = mismo checksum
        extracted_text="texto copia"
    )
    
    result = await service.validate_and_create_document(dto)
    
    assert result.is_valid is False


def test_checksum_uniqueness():
    """Test que contenidos diferentes producen checksums diferentes."""
    from app.application.services.checksum_service import ChecksumService
    
    service = ChecksumService()
    
    content1 = b"content A"
    content2 = b"content B"
    
    checksum1 = service.calculate_checksum(content1)
    checksum2 = service.calculate_checksum(content2)
    
    assert checksum1 != checksum2
    assert len(checksum1) == len(checksum2) == 64


def test_checksum_consistency():
    """Test que el mismo contenido siempre produce el mismo checksum."""
    from app.application.services.checksum_service import ChecksumService
    
    service = ChecksumService()
    content = b"consistent content"
    
    checksum1 = service.calculate_checksum(content)
    checksum2 = service.calculate_checksum(content)
    checksum3 = service.calculate_checksum(b"consistent content")
    
    assert checksum1 == checksum2 == checksum3


@pytest.mark.asyncio
async def test_created_document_has_minimal_fields():
    """Test que el documento creado tiene solo los campos requeridos."""
    from app.application.services.checksum_service import ChecksumService
    from app.application.dto.document_dto import DocumentCreateDTO
    from dataclasses import fields
    
    mock_repo = MagicMock()
    mock_repo.find_by_checksum = AsyncMock(return_value=None)
    
    service = ChecksumService(repository=mock_repo)
    
    dto = DocumentCreateDTO(
        file_bytes=b"content",
        extracted_text="texto extraído"
    )
    
    result = await service.validate_and_create_document(dto)
    
    assert result.is_valid is True
    document = result.document
    
    # Verificar campos del documento
    document_fields = {f.name for f in fields(document)}
    assert document_fields == {"id", "checksum", "extracted_text", "created_at"}
    
    # Verificar que no tiene campos no deseados
    assert not hasattr(document, 'filename') or document.filename is None
    assert not hasattr(document, 'page_dimensions') or document.page_dimensions is None
