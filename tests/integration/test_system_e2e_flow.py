"""
Prueba de Sistema y Flujo Completo E2E (Subida -> Ver texto -> Duplicado 409 -> Eliminar).

Verifica el ciclo de vida completo de documentos a través de la API y la coherencia
con los contratos consumidos por la interfaz web del microservicio de front-end.
"""

import io
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.dependencies import get_document_service, get_ingestion_service
from app.application.dto.document_dto import DocumentResponseDTO, IngestionResult

VALID_PDF_BYTES = b"%PDF-1.4 minimal-test-bytes-content"


class InMemoryDocumentStore:
    """Almacén en memoria para simular el comportamiento de MongoDB durante la prueba de sistema."""
    def __init__(self):
        self.documents = {}

    def insert(self, doc_id: str, checksum: str, text: str):
        self.documents[doc_id] = {
            "id": doc_id,
            "checksum": checksum,
            "extracted_text": text,
            "created_at": datetime.utcnow()
        }

    def find_by_checksum(self, checksum: str):
        for doc in self.documents.values():
            if doc["checksum"] == checksum:
                return doc
        return None

    def find_by_id(self, doc_id: str):
        return self.documents.get(doc_id)

    def delete(self, doc_id: str):
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False


@pytest.fixture
def system_client():
    store = InMemoryDocumentStore()
    app = create_app()

    class MockIngestionService:
        async def process_and_save(self, file_bytes: bytes, filename: str):
            checksum = "sha256-mock-checksum-12345"
            existing = store.find_by_checksum(checksum)
            if existing:
                return IngestionResult(
                    is_valid=False,
                    document=None,
                    error_message="Ya existe un documento con el mismo checksum"
                )
            
            doc_id = "doc-test-system-001"
            extracted_text = "Texto extraido correctamente en el flujo del sistema"
            store.insert(doc_id, checksum, extracted_text)

            from types import SimpleNamespace
            entity = SimpleNamespace(
                id=doc_id,
                checksum=checksum,
                extracted_text=extracted_text,
                created_at=datetime.utcnow()
            )

            return IngestionResult(
                is_valid=True,
                document=entity,
                error_message=None
            )

    class MockDocumentService:
        async def get_by_id(self, document_id: str):
            doc = store.find_by_id(document_id)
            if not doc:
                return None
            return DocumentResponseDTO(
                id=doc["id"],
                checksum=doc["checksum"],
                extracted_text=doc["extracted_text"],
                created_at=doc["created_at"]
            )

        async def delete(self, document_id: str):
            return store.delete(document_id)

    app.dependency_overrides[get_ingestion_service] = lambda: MockIngestionService()
    app.dependency_overrides[get_document_service] = lambda: MockDocumentService()

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestSystemFlow:
    """Verifica el flujo del sistema: Subida -> Ver -> Duplicado (409) -> Eliminar."""

    def test_complete_flow_upload_duplicate_delete(self, system_client: TestClient):
        # 1. Subida exitosa inicial (POST /api/v1/documents/upload)
        upload_resp = system_client.post(
            "/api/v1/documents/upload",
            files={"file": ("informe.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
        )
        assert upload_resp.status_code == 200
        data = upload_resp.json()
        doc_id = data["id"]
        assert doc_id == "doc-test-system-001"
        assert data["checksum"] == "sha256-mock-checksum-12345"
        assert "Texto extraido" in data["extracted_text"]

        # 2. Ver documento por ID (GET /api/v1/documents/{id})
        get_resp = system_client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == doc_id

        # 3. Reintento de subida del mismo documento -> Duplicado 409
        dup_resp = system_client.post(
            "/api/v1/documents/upload",
            files={"file": ("informe.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
        )
        assert dup_resp.status_code == 409
        assert "mismo checksum" in dup_resp.json()["detail"]

        # 4. Eliminación del documento (DELETE /api/v1/documents/{id})
        delete_resp = system_client.delete(f"/api/v1/documents/{doc_id}")
        assert delete_resp.status_code == 204

        # 5. Comprobar que ya no existe (404)
        get_deleted_resp = system_client.get(f"/api/v1/documents/{doc_id}")
        assert get_deleted_resp.status_code == 404

        # 6. Re-subida posterior a la eliminación -> Debe tener éxito nuevamente
        reupload_resp = system_client.post(
            "/api/v1/documents/upload",
            files={"file": ("informe.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
        )
        assert reupload_resp.status_code == 200
        assert reupload_resp.json()["id"] == doc_id
