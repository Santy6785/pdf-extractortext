"""
Tests unitarios para la entidad Document del dominio.
"""

import pytest
from datetime import datetime


def test_document_creation():
    """Test que un documento se crea con todos sus atributos."""
    from app.domain.models.document import Document

    document = Document(
        checksum="aabbccdd1234567890",
        extracted_text="Este es el texto extraído del documento",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        id="doc-123"
    )

    assert document.id == "doc-123"
    assert document.checksum == "aabbccdd1234567890"
    assert document.extracted_text == "Este es el texto extraído del documento"
    assert document.created_at == datetime(2024, 1, 15, 10, 30, 0)


def test_document_creation_without_id():
    """Test que un documento puede crearse sin ID (para nuevos documentos)."""
    from app.domain.models.document import Document

    document = Document(
        checksum="aabbccdd1234567890",
        extracted_text="Este es el texto extraído del documento",
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )

    assert document.id is None
    assert document.checksum == "aabbccdd1234567890"


def test_document_to_dict():
    """Test que el documento puede serializarse a diccionario."""
    from app.domain.models.document import Document

    document = Document(
        checksum="1234567890abcdef",
        extracted_text="Contenido de prueba",
        created_at=datetime(2024, 6, 10, 14, 0, 0),
        id="doc-456"
    )

    doc_dict = document.to_dict()

    assert doc_dict["id"] == "doc-456"
    assert doc_dict["checksum"] == "1234567890abcdef"
    assert doc_dict["extracted_text"] == "Contenido de prueba"
    assert doc_dict["created_at"] == "2024-06-10T14:00:00"


def test_document_to_dict_without_id():
    """Test que el documento sin ID se serializa correctamente."""
    from app.domain.models.document import Document

    document = Document(
        checksum="1234567890abcdef",
        extracted_text="Contenido de prueba",
        created_at=datetime(2024, 6, 10, 14, 0, 0)
    )

    doc_dict = document.to_dict()

    assert doc_dict["id"] is None
    assert doc_dict["checksum"] == "1234567890abcdef"


def test_document_from_dict():
    """Test que el documento puede deserializarse desde diccionario."""
    from app.domain.models.document import Document
    
    data = {
        "_id": "doc-789",
        "checksum": "fedcba0987654321",
        "extracted_text": "Texto de muestra",
        "created_at": "2024-03-20T09:00:00"
    }
    
    document = Document.from_dict(data)
    
    assert document.id == "doc-789"
    assert document.checksum == "fedcba0987654321"
    assert document.extracted_text == "Texto de muestra"


def test_document_equality_by_checksum():
    """Test que dos documentos con mismo checksum son considerados duplicados."""
    from app.domain.models.document import Document

    doc1 = Document(
        checksum="same-checksum-123",
        extracted_text="Texto A",
        created_at=datetime.now(),
        id="doc-1"
    )

    doc2 = Document(
        checksum="same-checksum-123",
        extracted_text="Texto B",
        created_at=datetime.now(),
        id="doc-2"
    )

    assert doc1.checksum == doc2.checksum


def test_document_minimal_fields():
    """Test que el documento tiene solo los 4 campos requeridos."""
    from app.domain.models.document import Document
    from dataclasses import fields
    
    document_fields = fields(Document)
    field_names = {f.name for f in document_fields}
    
    assert field_names == {"id", "checksum", "extracted_text", "created_at"}
