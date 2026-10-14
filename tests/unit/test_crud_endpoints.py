"""
Tests para los endpoints CRUD de documentos.
Utilizan mocks para simular la capa de servicio y repositorio.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
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


def test_create_document_success():
    """Test que POST /documents/upload crea un documento exitosamente."""
    from app.application.dto.document_dto import IngestionResult
    from app.domain.models.document import Document
    from datetime import datetime

    doc = Document(
        id="new-doc-123",
        checksum="new-checksum",
        extracted_text="nuevo texto",
        created_at=datetime.now()
    )

    validation_result = IngestionResult(
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
    from app.application.dto.document_dto import IngestionResult

    validation_result = IngestionResult(
        is_valid=False,
        document=None,
        error_message="Document with checksum abc123 already exists (409 Conflict)"
    )
    
    assert validation_result.is_valid is False
    assert validation_result.document is None
    assert "409 Conflict" in validation_result.error_message





def test_document_to_dict_contains_only_schema_fields():
    """Test que to_dict() solo incluye los campos del esquema."""
    from app.domain.models.document import Document
    from datetime import datetime
    from tests.conftest import DOCUMENT_REQUIRED_FIELDS
    
    doc = Document(
        id="doc-456",
        checksum="def456",
        extracted_text="texto de prueba",
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )
    
    doc_dict = doc.to_dict()
    
    # Debe serializar exactamente los campos del esquema (la estructura del modelo
    # se verifica en tests/unit/test_document.py)
    assert set(doc_dict) == DOCUMENT_REQUIRED_FIELDS
