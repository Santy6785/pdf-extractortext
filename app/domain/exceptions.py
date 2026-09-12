"""
Excepciones de dominio.
Definen errores que pueden ocurrir en la capa de dominio.
"""


class DocumentNotFoundError(Exception):
    """
    Excepción lanzada cuando un documento no se encuentra en el repositorio.
    
    Attributes:
        document_id: ID del documento que no se encontró
    """
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        super().__init__(f"Documento con ID {document_id} no encontrado")


class DomainError(Exception):
    """Excepción base para errores de dominio."""
    pass