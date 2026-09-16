"""
Tests directos (sin mocks) para el adaptador PypdfPdfExtractor / PdfService

Se usan PDFs mínimos reales generados sintéticamente en memoria con pymupdf,
para validar extracción de texto, metadatos y manejo de errores reales.
"""

import hashlib

import pytest
import pymupdf

from app.infrastructure.pdf.pypdf_extractor import (
    PypdfPdfExtractor,
    PdfProcessingError,
    PdfMetadata,
)
from app.infrastructure.pdf.pdf_service import PdfService


def _build_pdf_bytes(text: str = "") -> bytes:
    """Genera un PDF mínimo real con una página opcionalmente con texto."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    if text:
        page.insert_text((72, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def extractor() -> PypdfPdfExtractor:
    return PypdfPdfExtractor()


@pytest.fixture
def service() -> PdfService:
    return PdfService()


@pytest.fixture
def simple_pdf_bytes() -> bytes:
    return _build_pdf_bytes("Hola mundo PDF")


@pytest.fixture
def empty_pdf_bytes() -> bytes:
    return _build_pdf_bytes("")


class TestExtractText:
    def test_extrae_texto_de_pdf_simple(self, extractor, simple_pdf_bytes):
        text = extractor.extract_text(simple_pdf_bytes)
        assert "Hola mundo PDF" in text

    def test_pdf_sin_texto_retorna_cadena_vacia(self, extractor, empty_pdf_bytes):
        text = extractor.extract_text(empty_pdf_bytes)
        assert text == ""

    def test_bytes_no_pdf_eleva_pdf_processing_error(self, extractor):
        with pytest.raises(PdfProcessingError):
            extractor.extract_text(b"esto no es un pdf")

    def test_pdf_truncado_eleva_pdf_processing_error(self, extractor, simple_pdf_bytes):
        truncated = simple_pdf_bytes[: len(simple_pdf_bytes) // 3]
        with pytest.raises(PdfProcessingError):
            extractor.extract_text(truncated)

    def test_bytes_vacios_elevan_pdf_processing_error(self, extractor):
        with pytest.raises(PdfProcessingError):
            extractor.extract_text(b"")


class TestExtractMetadata:
    def test_metadatos_dimensiones_correctas(self, extractor, simple_pdf_bytes):
        metadata = extractor.extract_metadata(simple_pdf_bytes)
        assert isinstance(metadata, PdfMetadata)
        assert len(metadata.page_dimensions) == 1
        dims = metadata.page_dimensions[0]
        assert dims["width"] == pytest.approx(612.0)
        assert dims["height"] == pytest.approx(792.0)

    def test_metadatos_pdf_sin_texto(self, extractor, empty_pdf_bytes):
        metadata = extractor.extract_metadata(empty_pdf_bytes)
        assert len(metadata.page_dimensions) == 1


class TestProcessPdf:
    def test_process_pdf_retorna_checksum_y_texto(self, extractor, simple_pdf_bytes):
        result = extractor.process_pdf(simple_pdf_bytes)
        assert result.checksum == hashlib.sha256(simple_pdf_bytes).hexdigest()
        assert "Hola mundo PDF" in result.extracted_text

    def test_process_pdf_con_bytes_invalidos_eleva_error(self, extractor):
        with pytest.raises(PdfProcessingError):
            extractor.process_pdf(b"esto no es un pdf")


class TestPdfServiceAdapter:
    """PdfService delega en el adaptador real: se valida end-to-end sin mocks."""

    def test_extract_text_via_service(self, service, simple_pdf_bytes):
        text = service.extract_text(simple_pdf_bytes)
        assert "Hola mundo PDF" in text

    def test_extract_metadata_via_service(self, service, simple_pdf_bytes):
        metadata = service.extract_metadata(simple_pdf_bytes)
        assert metadata.page_dimensions[0]["width"] == pytest.approx(612.0)

    def test_service_eleva_pdf_processing_error_con_bytes_invalidos(self, service):
        with pytest.raises(PdfProcessingError):
            service.extract_text(b"no es un pdf")
