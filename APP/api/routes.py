"""
Adaptadores de API - Endpoints HTTP.
Arquitectura Limpia: Esta capa es el adaptador primario que recibe
peticiones externas y las convierte en llamadas al dominio.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import List, Optional

from app.services.pdf_service import PdfProcessingError
from app.application.services.document_service import DocumentService
from app.application.dto.document_dto import DocumentResponseDTO, DocumentListDTO, DocumentUpdateDTO
from app.api.dependencies import get_document_service
from app.config.settings import get_settings
from app.infrastructure.persistence.database import database


router = APIRouter(prefix="/api/v1", tags=["documents"])


def validate_pdf_file(file: UploadFile) -> None:
    """
    Valida que el archivo sea un PDF y cumpla con el tamaño máximo.

    Args:
        file: Archivo subido

    Raises:
        HTTPException: 400 si el archivo no es PDF o excede el tamaño máximo
    """
    settings = get_settings()
    max_size_bytes = settings.max_pdf_size_mb * 1024 * 1024

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

    # Validar tamaño máximo
    # Nota: SpooledTemporaryFile no tiene un método directo para obtener tamaño
    # hasta que se leen los bytes, por lo que validamos después de leer


# ==================== ENDPOINTS CRUD ====================

@router.get("/documents/", response_model=List[DocumentListDTO])
async def list_documents(
    skip: int = Query(0, ge=0, description="Número de documentos a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de documentos a retornar"),
    service: DocumentService = Depends(get_document_service)
):
    """
    Lista todos los documentos almacenados con paginación.

    Args:
        skip: Número de documentos a saltar (offset)
        limit: Número máximo de documentos a retornar (máx 100)

    Returns:
        Lista de documentos con id, checksum y fecha de creación
    """
    documents = await service.get_all(skip=skip, limit=limit)
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


@router.put("/documents/{document_id}", response_model=DocumentResponseDTO)
async def update_document(
    document_id: str,
    update_data: DocumentUpdateDTO,
    service: DocumentService = Depends(get_document_service)
):
    """
    Actualiza el texto extraído de un documento existente.

    Args:
        document_id: ID del documento a actualizar
        update_data: DTO con los datos a actualizar (extracted_text)

    Returns:
        Documento actualizado

    Raises:
        HTTPException: 404 si el documento no existe
    """
    updated_document = await service.update(
        document_id,
        extracted_text=update_data.extracted_text
    )

    if updated_document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Documento con ID {document_id} no encontrado"
        )

    return updated_document


@router.post("/documents/upload", response_model=DocumentResponseDTO)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    Endpoint para subir y procesar un documento PDF.

    - Valida que sea PDF
    - Valida tamaño máximo permitido
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
        HTTPException: 400 si no es PDF o excede tamaño, 409 si ya existe, 422 si está corrupto
    """
    # 1. Validacion de tipo de archivo
    validate_pdf_file(file)

    # 2. Leer archivo completamente en memoria (bytes)
    file_bytes = await file.read()

    # 3. Validar tamaño máximo después de leer
    settings = get_settings()
    max_size_bytes = settings.max_pdf_size_mb * 1024 * 1024
    if len(file_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el tamaño máximo permitido de {settings.max_pdf_size_mb}MB"
        )

    try:
        # 4. Procesar y guardar con validación de checksum
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


# ==================== ENDPOINTS DE SALUD ====================

@router.get("/health", status_code=200)
async def health_check():
    """
    Endpoint de health check para verificar el estado del sistema.

    Verifica:
    - Conexión a MongoDB
    - Estado general de la aplicación

    Returns:
        Estado del sistema con información de salud
    """
    try:
        # Verificar conexión a MongoDB
        is_db_connected = database.is_connected()

        if is_db_connected:
            return {
                "status": "healthy",
                "database": "connected",
                "version": "0.2.0"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "version": "0.2.0"
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": "0.2.0"
            }
        )
