"""
Adaptadores de API - Endpoints HTTP.
Arquitectura Limpia: Esta capa es el adaptador primario que recibe
peticiones externas y las convierte en llamadas al dominio.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import List

from app.services.pdf_service import PdfProcessingError
from app.application.services.document_service import DocumentService
from app.application.dto.document_dto import DocumentResponseDTO, DocumentListDTO
from app.api.dependencies import get_document_service


router = APIRouter(prefix="/api/v1", tags=["documents"])


def validate_pdf_file(file: UploadFile) -> None:
    """
    Valida que el archivo sea un PDF.
    
    Args:
        file: Archivo subido
        
    Raises:
        HTTPException: 400 si el archivo no es PDF
    """
    # Validar por content_type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"El archivo debe ser PDF. Tipo recibido: {file.content_type}"
        )
    
    # Validar por extension
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe tener extension .pdf"
        )


# ==================== ENDPOINTS CRUD ====================

@router.get("/documents/", response_model=List[DocumentListDTO])
async def list_documents(
    service: DocumentService = Depends(get_document_service)
):
    """
    Lista todos los documentos almacenados.
    
    Returns:
        Lista de documentos con id, checksum y fecha de creación
    """
    documents = await service.get_all()
    return documents


@router.get("/documents/{document_id}", response_model=DocumentResponseDTO)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """
    Obtiene un documento específico por su ID.
    
    Args:
        document_id: ID del documento
        
    Returns:
        Documento completo con id, checksum, contenido y fecha
        
    Raises:
        HTTPException: 404 si el documento no existe
    """
    document = await service.get_by_id(document_id)
    
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Documento con ID {document_id} no encontrado"
        )
    
    return document


@router.post("/documents/upload", response_model=DocumentResponseDTO)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    Endpoint para subir y procesar un documento PDF.
    
    - Valida que sea PDF
    - Procesa 100% en memoria (sin guardar en disco)
    - Extrae texto del contenido
    - Calcula checksum SHA-256
    - Verifica unicidad (409 Conflict si ya existe)
    - Persiste en MongoDB: checksum, contenido, fecha
    
    Args:
        file: Archivo PDF a procesar
        
    Returns:
        Documento creado con id, checksum, contenido y fecha
        
    Raises:
        HTTPException: 400 si no es PDF, 409 si ya existe, 422 si está corrupto
    """
    # 1. Validacion de tipo de archivo
    validate_pdf_file(file)
    
    # 2. Leer archivo completamente en memoria (bytes)
    file_bytes = await file.read()
    
    try:
        # 3. Procesar y guardar con validación de checksum
        result = await service.process_and_save(file_bytes, file.filename)
        
        if not result.is_valid:
            raise HTTPException(
                status_code=409,
                detail=result.error_message
            )
        
        return DocumentResponseDTO.from_entity(result.document)
        
    except PdfProcessingError as e:
        # Convertir error de dominio a HTTP 422
        raise HTTPException(
            status_code=422,
            detail=f"No se pudo procesar el PDF: {str(e)}"
        )


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """
    Elimina un documento por su ID.
    
    Args:
        document_id: ID del documento a eliminar
        
    Raises:
        HTTPException: 404 si el documento no existe
    """
    deleted = await service.delete(document_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Documento con ID {document_id} no encontrado"
        )
    
    return None


# Endpoint legacy mantenido para compatibilidad (ahora redirige al nuevo)
@router.post("/documents/")
async def upload_document_legacy(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    [LEGACY] Endpoint anterior para subir documentos.
    
    Ahora redirige al nuevo endpoint /documents/upload.
    Retorna archivo de texto con el contenido extraído.
    """
    validate_pdf_file(file)
    file_bytes = await file.read()
    
    try:
        result = await service.process_and_save(file_bytes, file.filename)
        
        if not result.is_valid:
            raise HTTPException(
                status_code=409,
                detail=result.error_message
            )
        
        # Generar nombre del archivo de salida
        base_name = file.filename.rsplit('.', 1)[0] if file.filename else "documento"
        output_filename = f"{base_name}.txt"
        
        # Retornar archivo de texto plano (compatibilidad legacy)
        return PlainTextResponse(
            content=result.document.extracted_text,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=\"{output_filename}\""
            }
        )
        
    except PdfProcessingError as e:
        raise HTTPException(
            status_code=422,
            detail=f"No se pudo procesar el PDF: {str(e)}"
        )
