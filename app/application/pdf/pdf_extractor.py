from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol


@dataclass
class PdfProcessingResult:
    """Result of PDF processing containing extracted text and checksum."""
    checksum: str
    extracted_text: str


class PdfExtractor(Protocol):
    """Port/interface for PDF extraction.

    Define the contract for extracting text and metadata from PDF files.
    Implementations belong in the infrastructure layer.
    """

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        """Extract text from PDF bytes.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            Extracted text content
        """
        ...

    @abstractmethod
    def extract_metadata(self, file_bytes: bytes) -> dict:
        """Extract metadata from PDF bytes.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            Dictionary with metadata (e.g., page dimensions)
        """
        ...

    @abstractmethod
    def process_pdf(self, file_bytes: bytes) -> PdfProcessingResult:
        """Process PDF bytes to extract text and calculate checksum.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            PdfProcessingResult with checksum and extracted text
        """
        ...