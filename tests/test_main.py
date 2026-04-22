"""
Tests de integración para el endpoint de documentos.
Siguiendo TDD: tests que verifican comportamiento, no implementación.
"""

import io
import pytest
from fastapi.testclient import TestClient


class TestDocumentEndpoint:
    """Tests para el endpoint POST /api/v1/documents/"""

    def test_reject_non_pdf_files(self, client: TestClient):
        """
        RED: El sistema debe rechazar archivos que no son PDF con HTTP 400.
        """
        # Arrange: Crear un archivo de texto que NO es PDF
        fake_file = io.BytesIO(b"Este no es un PDF, es texto plano")

        # Act: Intentar subir el archivo
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("documento.txt", fake_file, "text/plain")}
        )

        # Assert: Verificar que se rechazo el archivo
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_process_valid_pdf(self, client: TestClient):
        """
        RED: El sistema debe procesar un PDF valido y retornar un archivo .txt
        con el texto extraido descargable.
        """
        # Arrange: Crear un PDF minimo en memoria
        # Este es un PDF valido de 1 pagina con texto "Hola Mundo"
        pdf_content = self._create_minimal_pdf()
        pdf_file = io.BytesIO(pdf_content)

        # Act: Subir el PDF
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test_document.pdf", pdf_file, "application/pdf")}
        )

        # Assert: Verificar respuesta exitosa
        assert response.status_code == 200
        # La respuesta ahora es texto plano (archivo .txt)
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        # Verificar que el header indica que es un archivo descargable
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "test_document.txt" in response.headers.get("content-disposition", "")

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
