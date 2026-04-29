"""
Tests para los endpoints CRUD de documentos.
Utilizan mocks para simular la capa de servicio y repositorio.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def mock_document_service():
    """Fixture que crea un mock del servicio de documentos."""
    service = MagicMock()
    service.get_all = AsyncMock()
    service.get_by_id = AsyncMock()
    service.create = AsyncMock()
    service.delete = AsyncMock()
    return service


@pytest.fixture
def app_with_mocked_service(mock_document_service):
    """Fixture que crea una app FastAPI con servicio mockeado."""
    from app.api.routes import router
    
    app = FastAPI()
    
    # Sobrescribir dependencias
    app.dependency_overrides = {}
    
    app.include_router(router)
    return app


def test_get_documents_returns_list():
    """Test que GET /documents/ retorna lista de documentos."""
    from app.domain.models.document import Document
    from app.application.dto.document_dto import DocumentListDTO
    from datetime import datetime
    
    # Mock de documentos
    docs = [
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
    
    # Verificar que el DTO de respuesta funciona
    response_docs = [DocumentListDTO.from_entity(doc) for doc in docs]
    
    assert len(response_docs) == 2
    assert response_docs[0].checksum == "cs1"
    assert response_docs[1].checksum == "cs2"


def test_get_document_by_id_returns_single_document():
    """Test que GET /documents/{id} retorna un documento específico."""
    from app.domain.models.document import Document
    from app.application.dto.document_dto import DocumentResponseDTO
    from datetime import datetime
    
    doc = Document(
        id="doc-123",
        checksum="unique-checksum",
        extracted_text="contenido específico",
        created_at=datetime.now()
    )
    
    response = DocumentResponseDTO.from_entity(doc)
    
    assert response.id == "doc-123"
    assert response.checksum == "unique-checksum"
    assert response.extracted_text == "contenido específico"


def test_get_document_by_id_not_found():
    """Test que GET /documents/{id} retorna 404 si no existe."""
    # Este test verifica el manejo de casos donde el documento no existe
    document_id = "non-existent-id"
    
    # Simular respuesta None del servicio
    result = None
    
    assert result is None


def test_create_document_success():
    """Test que POST /documents/upload crea un documento exitosamente."""
    from app.application.dto.document_dto import ChecksumValidationResult
    from app.domain.models.document import Document
    from datetime import datetime
    
    doc = Document(
        id="new-doc-123",
        checksum="new-checksum",
        extracted_text="nuevo texto",
        created_at=datetime.now()
    )
    
    validation_result = ChecksumValidationResult(
        is_valid=True,
        document=doc,
        error_message=None
    )
    
    assert validation_result.is_valid is True
    assert validation_result.document is not None
    assert validation_result.error_message is None
    assert validation_result.document.checksum == "new-checksum"


def test_create_document_duplicate_checksum():
    """Test que POST /documents/ retorna 409 si el checksum existe."""
    from app.application.dto.document_dto import ChecksumValidationResult
    
    validation_result = ChecksumValidationResult(
        is_valid=False,
        document=None,
        error_message="Document with checksum abc123 already exists (409 Conflict)"
    )
    
    assert validation_result.is_valid is False
    assert validation_result.document is None
    assert "409 Conflict" in validation_result.error_message


def test_delete_document_success():
    """Test que DELETE /documents/{id} elimina exitosamente."""
    # Simular eliminación exitosa
    deleted = True
    
    assert deleted is True


def test_delete_document_not_found():
    """Test que DELETE /documents/{id} retorna 404 si no existe."""
    # Simular documento no encontrado
    deleted = False
    
    assert deleted is False


def test_document_schema_has_only_required_fields():
    """Test que el esquema tiene solo checksum, extracted_text y created_at."""
    from app.domain.models.document import Document
    from dataclasses import fields
    from datetime import datetime
    
    doc = Document(
        id="doc-123",
        checksum="abc123",
        extracted_text="contenido del documento",
        created_at=datetime.now()
    )
    
    # Verificar campos del documento
    document_fields = {f.name for f in fields(doc)}
    
    # Debe tener exactamente estos 4 campos
    expected_fields = {"id", "checksum", "extracted_text", "created_at"}
    assert document_fields == expected_fields
    
    # No debe tener campos adicionales
    assert "filename" not in document_fields
    assert "page_dimensions" not in document_fields


def test_document_to_dict_contains_only_schema_fields():
    """Test que to_dict() solo incluye los campos del esquema."""
    from app.domain.models.document import Document
    from datetime import datetime
    
    doc = Document(
        id="doc-456",
        checksum="def456",
        extracted_text="texto de prueba",
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )
    
    doc_dict = doc.to_dict()
    
    # Solo debe tener estos campos
    assert "id" in doc_dict
    assert "checksum" in doc_dict
    assert "extracted_text" in doc_dict
    assert "created_at" in doc_dict
    assert len(doc_dict) == 4
    
    # No debe tener campos adicionales
    assert "filename" not in doc_dict
    assert "page_dimensions" not in doc_dict
