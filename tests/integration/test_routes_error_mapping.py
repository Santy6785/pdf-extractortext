"""
Tests del mapeo de errores HTTP en app/api/routes.py.

Cubre los códigos 400, 404, 409 y 422 usando TestClient con
dependency_overrides para forzar los escenarios de error sin servicios
externos reales.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app import api as api_package  # noqa: F401  (asegura carga del paquete)
import app.api.routes as routes_module
from app.api.dependencies import get_document_service, get_ingestion_service
from app.services.pdf_service import PdfProcessingError
from app.domain.exceptions import DocumentNotFoundError
from app.application.dto.document_dto import IngestionResult


VALID_PDF_BYTES = b"%PDF-1.4 minimal-test-bytes"
UPLOAD_URL = "/api/v1/documents/upload"


class FakeDocumentService:
    """Stub configurable de DocumentService para forzar escenarios."""

    def __init__(self, *, get_by_id_result=None, update_result=None, delete_result=True):
        self._get_by_id_result = get_by_id_result
        self._update_result = update_result
        self._delete_result = delete_result

    async def get_all(self, skip=0, limit=10):
        return []

    async def get_by_id(self, document_id):
        return self._get_by_id_result

    async def update(self, document_id, extracted_text=None):
        return self._update_result

    async def delete(self, document_id):
        return self._delete_result


class FakeIngestionService:
    """Stub de DocumentIngestionService: puede retornar un resultado o lanzar error."""

    def __init__(self, *, result=None, error: Exception | None = None):
        self._result = result
        self._error = error

    async def process_and_save(self, file_bytes: bytes, filename: str):
        if self._error is not None:
            raise self._error
        return self._result


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def override_document_service(app, service: FakeDocumentService):
    app.dependency_overrides[get_document_service] = lambda: service


def override_ingestion_service(app, service: FakeIngestionService):
    app.dependency_overrides[get_ingestion_service] = lambda: service


class TestErrors400:
    def test_upload_con_content_type_invalido_retorna_400(self, app, client):
        override_ingestion_service(app, FakeIngestionService())
        response = client.post(
            UPLOAD_URL,
            files={"file": ("documento.pdf", b"contenido", "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "El archivo debe ser PDF" in detail
        assert "text/plain" in detail

    def test_upload_con_extension_invalida_retorna_400(self, app, client):
        override_ingestion_service(app, FakeIngestionService())
        response = client.post(
            UPLOAD_URL,
            files={"file": ("documento.txt", VALID_PDF_BYTES, "application/pdf")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "El archivo debe tener extension .pdf"

    def test_upload_que_excede_tamano_maximo_retorna_400(self, app, client, monkeypatch):
        override_ingestion_service(app, FakeIngestionService())
        class TinyConfig:
            def get_max_pdf_size_bytes(self):
                return 1

            def get_max_pdf_size_mb(self):
                return 0

        monkeypatch.setattr(routes_module, "get_config_service", lambda: TinyConfig())

        response = client.post(
            UPLOAD_URL,
            files={"file": ("grande.pdf", b"x" * 100, "application/pdf")},
        )
        assert response.status_code == 400
        assert "excede el tamaño máximo permitido" in response.json()["detail"]


class TestErrors404:
    def test_get_documento_inexistente_retorna_404(self, app, client):
        override_document_service(app, FakeDocumentService(get_by_id_result=None))

        response = client.get("/api/v1/documents/id-inexistente")

        assert response.status_code == 404
        assert response.json()["detail"] == str(DocumentNotFoundError("id-inexistente"))

    def test_update_documento_inexistente_retorna_404(self, app, client):
        override_document_service(app, FakeDocumentService(update_result=None))

        response = client.put(
            "/api/v1/documents/id-inexistente",
            json={"extracted_text": "nuevo texto"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == str(DocumentNotFoundError("id-inexistente"))

    def test_delete_documento_inexistente_retorna_404(self, app, client):
        override_document_service(app, FakeDocumentService(delete_result=False))

        response = client.delete("/api/v1/documents/id-inexistente")

        assert response.status_code == 404
        assert response.json()["detail"] == str(DocumentNotFoundError("id-inexistente"))


class TestErrors409:
    def test_upload_documento_duplicado_retorna_409(self, app, client):
        resultado = IngestionResult(
            is_valid=False,
            document=None,
            error_message="Ya existe un documento con el mismo checksum",
        )
        override_ingestion_service(app, FakeIngestionService(result=resultado))

        response = client.post(
            UPLOAD_URL,
            files={"file": ("documento.pdf", VALID_PDF_BYTES, "application/pdf")},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Ya existe un documento con el mismo checksum"


class TestErrors422:
    def test_pdf_corrupto_retorna_422(self, app, client):
        error = PdfProcessingError("PDF corrupto o no legible: EOF marker not found")
        override_ingestion_service(app, FakeIngestionService(error=error))

        response = client.post(
            UPLOAD_URL,
            files={"file": ("corrupto.pdf", VALID_PDF_BYTES, "application/pdf")},
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail.startswith("No se pudo procesar el PDF:")
        assert "PDF corrupto o no legible" in detail

    def test_parametro_query_invalido_retorna_422_schema_pydantic(self, app, client):
        override_document_service(app, FakeDocumentService())
        """limit=0 viola la restricción ge=1 del Query param → 422 de validación."""
        response = client.get("/api/v1/documents/?limit=0")

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any(error["loc"][-1] == "limit" for error in detail)

    def test_body_invalido_en_update_retorna_422_schema_pydantic(self, app, client):
        """extracted_text con tipo inválido → 422 de validación Pydantic."""
        override_document_service(app, FakeDocumentService())

        response = client.put(
            "/api/v1/documents/cualquier-id",
            json={"extracted_text": {"no": "es un string"}},
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("extracted_text" in error["loc"] for error in detail)
