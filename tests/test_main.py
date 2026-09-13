"""
Tests de integración para el endpoint de documentos.
Siguiendo TDD: tests que verifican comportamiento, no implementación.
"""

import io
import pytest
from fastapi.testclient import TestClient


class TestDocumentUploadEndpoint:
    """Tests para el endpoint POST /api/v1/documents/upload"""

    def test_reject_non_pdf_files(self, client: TestClient):
        """
        RED: El sistema debe rechazar archivos que no son PDF con HTTP 400.
        """
        # Arrange: Crear un archivo de texto que NO es PDF
        fake_file = io.BytesIO(b"Este no es un PDF, es texto plano")

        # Act: Intentar subir el archivo
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("documento.txt", fake_file, "text/plain")}
        )

        # Assert: Verificar que se rechazo el archivo
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_process_valid_pdf(self, client: TestClient):
        """
        RED: El sistema debe procesar un PDF valido y retornar JSON estructurado
        con el texto extraído, checksum y metadatos.
        """
        # Arrange: Crear un PDF minimo en memoria
        pdf_content = self._create_minimal_pdf()
        pdf_file = io.BytesIO(pdf_content)

        # Act: Subir el PDF
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test_document.pdf", pdf_file, "application/pdf")}
        )

        # Assert: Verificar respuesta exitosa
        assert response.status_code == 200
        # La respuesta ahora es JSON estructurado
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        # Verificar campos requeridos en la respuesta
        assert "id" in data
        assert "checksum" in data
        assert "extracted_text" in data
        assert "created_at" in data

    def _create_minimal_pdf(self) -> bytes:
        """
        Crea un PDF minimo valido en memoria para testing.
        Usa pypdf para generar un PDF simple.
        """
        from pypdf import PdfWriter
        from pypdf.generic import RectangleObject
        from io import BytesIO

        writer = PdfWriter()

        # Crear una pagina con tamaño A4 (en puntos: 595.27 x 841.89)
        page = writer.add_blank_page(width=595.27, height=841.89)

        # Guardar en memoria
        output = BytesIO()
        writer.write(output)
        output.seek(0)

        return output.read()
