"""
Servicio de dominio para procesamiento de PDFs.
Arquitectura Limpia: Esta capa contiene la lógica de negocio pura,
sin dependencias de frameworks ni infraestructura.
"""

import hashlib
from dataclasses import dataclass
from typing import List, Tuple
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass
class PdfProcessingResult:
    """DTO para el resultado del procesamiento de PDF."""
    nombre_archivo: str
    checksum: str
    dimensiones_paginas: List[dict]
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
    - Medir dimensiones de las páginas
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
            
            # 2. Extraer texto y dimensiones del PDF
            texto, dimensiones = self._extract_pdf_data(file_bytes)
            
            return PdfProcessingResult(
                nombre_archivo=filename,
                checksum=checksum,
                dimensiones_paginas=dimensiones,
                texto_extraido=texto
            )
            
        except PdfReadError as e:
            raise PdfProcessingError(f"PDF corrupto o no legible: {str(e)}")
        except Exception as e:
            raise PdfProcessingError(f"Error al procesar PDF: {str(e)}")

    def _calculate_checksum(self, data: bytes) -> str:
        """Calcula el hash SHA-256 de los bytes."""
        return hashlib.sha256(data).hexdigest()

    def _extract_pdf_data(self, file_bytes: bytes) -> Tuple[str, List[dict]]:
        """
        Extrae texto y dimensiones de todas las páginas del PDF.
        
        Args:
            file_bytes: Bytes del PDF en memoria
            
        Returns:
            Tupla de (texto_extraido, lista_de_dimensiones)
        """
        reader = PdfReader(BytesIO(file_bytes))
        
        text_parts = []
        dimensions = []
        
        for page in reader.pages:
            # Extraer texto (ignora imágenes automáticamente)
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            
            # Capturar dimensiones de la página en puntos
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            dimensions.append({
                "ancho": width,
                "alto": height
            })
        
        full_text = "\n".join(text_parts)
        return full_text, dimensions
