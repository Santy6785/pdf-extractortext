"""
Implementación del patrón Repository para MongoDB usando motor (async).
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.domain.models.document import Document
from app.domain.repositories.document_repository import DocumentRepository


class MongoDocumentRepository(DocumentRepository):
    """
    Implementación asíncrona del repositorio de documentos con MongoDB.
    
    Schema:
    {
        "_id": ObjectId,
        "checksum": str,           // Hash SHA-256 para unicidad
        "extracted_text": str,     // Contenido del documento
        "created_at": datetime     // Fecha de subida
    }
    """
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Inicializa el repositorio con una colección de motor.
        
        Args:
            collection: Colección de MongoDB de motor
        """
        self._collection = collection
    
    def _document_to_dict(self, document: Document) -> dict:
        """
        Convierte una entidad de dominio a diccionario para MongoDB.
        
        Args:
            document: Entidad Document
            
        Returns:
            Diccionario compatible con MongoDB
        """
        doc_dict = {
            "checksum": document.checksum,
            "extracted_text": document.extracted_text,
            "created_at": document.created_at
        }
        
        # Solo incluir _id si el documento ya tiene uno
        if document.id:
            doc_dict["_id"] = ObjectId(document.id)
            
        return doc_dict
    
    def _dict_to_document(self, data: dict) -> Optional[Document]:
        """
        Convierte un documento de MongoDB a entidad de dominio.
        
        Args:
            data: Documento de MongoDB
            
        Returns:
            Entidad Document o None
        """
        if data is None:
            return None
            
        return Document.from_dict(data)
    
    async def save(self, document: Document) -> str:
        """
        Guarda un documento en MongoDB.
        
        Args:
            document: Documento a guardar
            
        Returns:
            ID del documento guardado
        """
        doc_dict = self._document_to_dict(document)
        
        # Si ya tiene ID, es actualización; si no, es inserción
        if document.id and ObjectId.is_valid(document.id):
            await self._collection.update_one(
                {"_id": ObjectId(document.id)},
                {"$set": doc_dict},
                upsert=True
            )
            return document.id
        else:
            result = await self._collection.insert_one(doc_dict)
            return str(result.inserted_id)
    
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """
        Busca un documento por su ID.
        
        Args:
            document_id: ID del documento
            
        Returns:
            Documento encontrado o None
        """
        try:
            data = await self._collection.find_one({"_id": ObjectId(document_id)})
            return self._dict_to_document(data)
        except Exception:
            return None
    
    async def find_by_checksum(self, checksum: str) -> Optional[Document]:
        """
        Busca un documento por su checksum.
        Útil para verificar unicidad.
        
        Args:
            checksum: Hash SHA-256 del archivo
            
        Returns:
            Documento encontrado o None
        """
        data = await self._collection.find_one({"checksum": checksum})
        return self._dict_to_document(data)
    
    async def find_all(self) -> List[Document]:
        """
        Obtiene todos los documentos almacenados.
        
        Returns:
            Lista de documentos
        """
        cursor = self._collection.find()
        documents = await cursor.to_list(length=None)
        return [self._dict_to_document(doc) for doc in documents if doc]
    
    async def delete(self, document_id: str) -> bool:
        """
        Elimina un documento por su ID.
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            result = await self._collection.delete_one({"_id": ObjectId(document_id)})
            return result.deleted_count > 0
        except Exception:
            return False
