"""
Servicio de dominio para procesamiento de PDFs.
Arquitectura Limpia: Esta capa contiene la lógica de negocio pura,
sin dependencias de frameworks ni infraestructura.
"""

import hashlib
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass
class PdfProcessingResult:
    """DTO para el resultado del procesamiento de PDF."""
    checksum: str
    texto_extraido: str


class PdfProcessingError(Exception):
    """Excepción de dominio para errores de procesamiento de PDF."""
    pass


class PdfService:
    """
    Servicio puro para procesar archivos PDF en memoria.
    
    Responsabilidades:
    - Calcular checksum SHA-256 de los bytes
    - Extraer texto de todas las páginas
    - Ignorar imágenes y elementos visuales
    """

    def process_pdf(self, file_bytes: bytes, filename: str) -> PdfProcessingResult:
        """
        Procesa un PDF en memoria y retorna los datos extraídos.
        
        Args:
            file_bytes: Bytes del archivo PDF en memoria
            filename: Nombre original del archivo
            
        Returns:
            PdfProcessingResult con los datos extraídos
            
        Raises:
            PdfProcessingError: Si el PDF está corrupto, encriptado o no se puede leer
        """
        try:
            # 1. Calcular checksum SHA-256
            checksum = self._calculate_checksum(file_bytes)
            
            # 2. Extraer texto del PDF
            texto = self._extract_text(file_bytes)
            
            return PdfProcessingResult(
                checksum=checksum,
                texto_extraido=texto
            )
            
        except PdfReadError as e:
            raise PdfProcessingError(f"PDF corrupto o no legible: {str(e)}")
        except Exception as e:
            raise PdfProcessingError(f"Error al procesar PDF: {str(e)}")

    def _calculate_checksum(self, data: bytes) -> str:
        """Calcula el hash SHA-256 de los bytes."""
        return hashlib.sha256(data).hexdigest()

    def _extract_text(self, file_bytes: bytes) -> str:
        """Extrae texto del PDF usando pypdf."""
        reader = PdfReader(BytesIO(file_bytes))
        text_parts = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n".join(text_parts)