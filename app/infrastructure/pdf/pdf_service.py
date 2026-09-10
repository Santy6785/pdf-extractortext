"""
Servicio de infraestructura para procesamiento de PDFs usando pypdf.
Implementa el port PdfExtractor desde la capa de aplicación.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ...application.pdf.pdf_extractor import PdfExtractor
from ...application.pdf.pypdf_extractor import PypdfPdfExtractor, PdfMetadata


class PdfService:
    """Adaptador de infraestructura que implementa PdfExtractor usando pypdf."""

    def __init__(self) -> None:
        self._extractor = PypdfPdfExtractor()

    def extract_text(self, file_bytes: bytes) -> str:
        """Extraer texto del PDF usando el adaptador pypdf."""
        return self._extractor.extract_text(file_bytes)

    def extract_metadata(self, file_bytes: bytes) -> PdfMetadata:
        """Extraer metadatos (dimensiones) del PDF usando el adaptador pypdf."""
        return self._extractor.extract_metadata(file_bytes)