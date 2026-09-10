from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import List

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ...application.pdf.pdf_extractor import PdfExtractor


class PdfProcessingError(Exception):
    """Excepción de infraestructura para errores de procesamiento de PDF."""
    pass


@dataclass
class PdfMetadata:
    """Metadata extracted from a PDF file."""
    page_dimensions: List[dict]


class PypdfPdfExtractor:
    """Adaptador real de pypdf que implementa el port PdfExtractor.

    Responsabilidad: extraer texto y metadatos de archivos PDF usando pypdf.
    Esta clase pertenece a la capa de infraestructura.
    """

    def extract_text(self, file_bytes: bytes) -> str:
        """Extract text from PDF bytes using pypdf.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            Extracted text content

        Raises:
            PdfProcessingError: Si el PDF está corrupto o encriptado
        """
        try:
            reader = PdfReader(BytesIO(file_bytes))
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            return "\n".join(text_parts)
        except PdfReadError as e:
            raise PdfProcessingError(f"PDF corrupto o no legible: {str(e)}")
        except Exception as e:
            raise PdfProcessingError(f"Error al extraer texto del PDF: {str(e)}")

    def extract_metadata(self, file_bytes: bytes) -> PdfMetadata:
        """Extract metadata (page dimensions) from PDF bytes using pypdf.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            PdfMetadata con las dimensiones de las páginas
        """
        reader = PdfReader(BytesIO(file_bytes))
        dimensions = []

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            dimensions.append({"ancho": width, "alto": height})

        return PdfMetadata(page_dimensions=dimensions)