from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol


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