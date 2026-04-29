"""
Entidad de dominio Document.
Representa un documento PDF procesado y almacenado en el sistema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class Document:
    """
    Entidad de dominio que representa un documento PDF procesado.

    Schema MongoDB:
    - _id: Identificador único (generado automáticamente)
    - checksum: Hash SHA-256 del archivo original (para unicidad)
    - extracted_text: Texto extraído del PDF (contenido del documento)
    - created_at: Fecha de subida/carga del documento
    """
    checksum: str
    extracted_text: str
    created_at: datetime
    id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el documento a un diccionario."""
        return {
            "id": self.id,
            "checksum": self.checksum,
            "extracted_text": self.extracted_text,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Deserializa un documento desde un diccionario."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        # Handle _id from MongoDB or id from serialization
        doc_id = data.get("_id") or data.get("id")
        if doc_id is not None:
            doc_id = str(doc_id)

        return cls(
            checksum=data.get("checksum", ""),
            extracted_text=data.get("extracted_text", ""),
            created_at=created_at,
            id=doc_id
        )
