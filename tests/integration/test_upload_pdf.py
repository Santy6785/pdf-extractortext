import io
import pytest
from fastapi.testclient import TestClient

class TestUploadPdfEndpoint:

    def test_reject_non_pdf_files(self, client: TestClient):
        # Arrange: Crear un archivo de texto que NO es PDF
        fake_file = io.BytesIO(b"Este no es un PDF, es texto plano")

        # Act: Intentar subir el archivo
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("documento.txt", fake_file, "text/plain")}
        )

        # Assert: Verificar que se rechazó el archivo
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"] or "pdf" in response.json()["detail"]
