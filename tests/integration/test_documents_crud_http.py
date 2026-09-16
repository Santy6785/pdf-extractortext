"""
Tests HTTP reales (integración) para los endpoints CRUD de documentos.

Usan TestClient de FastAPI para golpear las rutas HTTP reales y
app.dependency_overrides para desacoplar la capa de persistencia
(no se requiere una instancia viva de MongoDB).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.dependencies import get_document_service
from app.application.dto.document_dto import DocumentResponseDTO
from app.domain.exceptions import DocumentNotFoundError

BASE_URL = "/api/v1/documents"


def _make_document_dto(document_id: str = "doc-123",
                       checksum: str = "checksum-abc",
                       extracted_text: str = "texto original") -> DocumentResponseDTO:
    return DocumentResponseDTO(
        id=document_id,
        checksum=checksum,
        extracted_text=extracted_text,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def mock_document_service() -> MagicMock:
    """Servicio de documentos mockeado (sin base de datos)."""
    service = MagicMock()
    service.get_all = AsyncMock()
    service.get_by_id = AsyncMock()
    service.update = AsyncMock()
    service.delete = AsyncMock()
    return service


@pytest.fixture
def client(mock_document_service: MagicMock):
    """TestClient con la dependencia de servicio sobreescrita."""
    app = create_app()
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestGetDocumentById:
    """Tests para GET /documents/{id}."""

    def test_get_document_returns_200_with_document(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        doc = _make_document_dto()
        mock_document_service.get_by_id.return_value = doc

        response = client.get(f"{BASE_URL}/doc-123")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "doc-123"
        assert body["checksum"] == "checksum-abc"
        assert body["extracted_text"] == "texto original"
        assert "created_at" in body
        mock_document_service.get_by_id.assert_awaited_once_with("doc-123")

    def test_get_document_returns_404_when_not_found(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        mock_document_service.get_by_id.return_value = None

        response = client.get(f"{BASE_URL}/inexistente")

        assert response.status_code == 404
        assert str(DocumentNotFoundError("inexistente")) == response.json()["detail"]


class TestUpdateDocument:
    """Tests para PUT /documents/{id}."""

    def test_update_document_returns_200_with_updated_document(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        updated = _make_document_dto(extracted_text="texto actualizado")
        mock_document_service.update.return_value = updated

        response = client.put(
            f"{BASE_URL}/doc-123",
            json={"extracted_text": "texto actualizado"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "doc-123"
        assert body["extracted_text"] == "texto actualizado"
        mock_document_service.update.assert_awaited_once_with(
            "doc-123", extracted_text="texto actualizado"
        )

    def test_update_document_returns_404_when_not_found(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        mock_document_service.update.return_value = None

        response = client.put(
            f"{BASE_URL}/inexistente",
            json={"extracted_text": "nuevo texto"},
        )

        assert response.status_code == 404
        assert str(DocumentNotFoundError("inexistente")) == response.json()["detail"]

    def test_update_document_returns_422_when_body_is_invalid(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        # Falta el campo requerido "extracted_text"
        response = client.put(f"{BASE_URL}/doc-123", json={})

        assert response.status_code == 422
        mock_document_service.update.assert_not_awaited()


class TestDeleteDocument:
    """Tests para DELETE /documents/{id}."""

    def test_delete_document_returns_204_on_success(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        mock_document_service.delete.return_value = True

        response = client.delete(f"{BASE_URL}/doc-123")

        assert response.status_code == 204
        assert response.content == b""
        mock_document_service.delete.assert_awaited_once_with("doc-123")

    def test_delete_document_returns_404_when_not_found(
        self, client: TestClient, mock_document_service: MagicMock
    ):
        mock_document_service.delete.return_value = False

        response = client.delete(f"{BASE_URL}/inexistente")

        assert response.status_code == 404
        assert str(DocumentNotFoundError("inexistente")) == response.json()["detail"]
