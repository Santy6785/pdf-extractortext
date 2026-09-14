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
from app.application.config_service import get_config_service, ConfigService
from app.infrastructure.persistence.database import Database
from app.api.dependencies import get_document_service, get_database
from app.config.settings import get_settings
from app.domain.exceptions import DocumentNotFoundError


router = APIRouter(prefix="/api/v1", tags=["documents"])


def validate_pdf_file(file: UploadFile) -> None:
    """
    Valida que el archivo sea un PDF (tipo MIME y extensión).

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


def validate_pdf_size(file_bytes: bytes, config: ConfigService) -> None:
    """
    Valida que el archivo PDF no exceda el tamaño máximo configurado.

    Args:
        file_bytes: Contenido del archivo en bytes
        config: Servicio de configuración

    Raises:
        HTTPException: 400 si el archivo excede el tamaño máximo
    """
    max_size_bytes = config.get_max_pdf_size_bytes()
    if len(file_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el tamaño máximo permitido de {config.get_max_pdf_size_mb()}MB"
        )


async def _read_and_validate_upload(file: UploadFile) -> bytes:
    """
    Valida y lee completamente un archivo PDF subido.

    Pasos:
    1. Valida que sea un PDF (tipo MIME y extensión)
    2. Lee el contenido completo en memoria
    3. Valida que no exceda el tamaño máximo configurado

    Args:
        file: Archivo subido

    Returns:
        Contenido del archivo en bytes

    Raises:
        HTTPException: 400 si no es PDF o excede el tamaño máximo
    """
    validate_pdf_file(file)
    file_bytes = await file.read()
    validate_pdf_size(file_bytes, get_config_service())
    return file_bytes


def _raise_conflict_if_invalid(result) -> None:
    """
    Lanza HTTP 409 si el resultado de validación de checksum no es válido.

    Args:
        result: ChecksumValidationResult del servicio de documentos

    Raises:
        HTTPException: 409 si el documento ya existe
    """
    if not result.is_valid:
        raise HTTPException(
            status_code=409,
            detail=result.error_message
        )


def _raise_pdf_processing_error(error: PdfProcessingError) -> None:
    """
    Convierte un error de procesamiento de PDF en HTTP 422.

    Args:
        error: Excepción de procesamiento de PDF

    Raises:
        HTTPException: 422 con el detalle del error
    """
    raise HTTPException(
        status_code=422,
        detail=f"No se pudo procesar el PDF: {str(error)}"
    )


def raise_document_not_found(document_id: str) -> None:
    """
    Lanza una excepción HTTP 404 para documento no encontrado.
    
    Centraliza el mensaje de error para evitar duplicación (DRY).
    
    Args:
        document_id: ID del documento que no se encontró
        
    Raises:
        HTTPException: 404 con mensaje estandarizado
    """
    raise HTTPException(
        status_code=404,
        detail=str(DocumentNotFoundError(document_id))
    )


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
        raise_document_not_found(document_id)

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
        raise_document_not_found(document_id)

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
    # 1. Leer y validar el archivo subido (tipo y tamaño)
    file_bytes = await _read_and_validate_upload(file)

    try:
        # 2. Procesar y guardar con validación de checksum
        result = await service.process_and_save(file_bytes, file.filename)
        _raise_conflict_if_invalid(result)
        return DocumentResponseDTO.from_entity(result.document)

    except PdfProcessingError as e:
        # Convertir error de dominio a HTTP 422
        _raise_pdf_processing_error(e)


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
        raise_document_not_found(document_id)
    
    return None


# Endpoint legacy mantenido para compatibilidad (deprecated)
@router.post(
    "/documents/",
    deprecated=True,
    include_in_schema=True,
    summary="[DEPRECATED] Subir documento PDF (retorna .txt)",
    description=(
        "**Obsoleto**: Use POST /api/v1/documents/upload en su lugar.\n\n"
        "Este endpoint se mantiene solo para retrocompatibilidad con el frontend legacy. "
        "Consumidor actual: frontend web (frontend/index.html).\n\n"
        "Retorna un archivo de texto plano (.txt) con el contenido extraído, "
        "en lugar de una respuesta JSON estructurada."
    ),
    response_class=PlainTextResponse,
)
async def upload_document_legacy(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    [LEGACY/DEPRECATED] Endpoint anterior para subir documentos.
    
    **Consumidor**: Frontend web (frontend/index.html) - pendiente migración.
    
    Use POST /api/v1/documents/upload para nuevas integraciones.
    Retorna archivo de texto plano (.txt) con el contenido extraído.
    
    Returns:
        PlainTextResponse: Archivo .txt descargable con texto extraído
    
    Raises:
        HTTPException: 400 si no es PDF o excede tamaño, 409 si ya existe, 422 si está corrupto
    """
    file_bytes = await _read_and_validate_upload(file)
    
    try:
        result = await service.process_and_save(file_bytes, file.filename)
        _raise_conflict_if_invalid(result)
        
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
        _raise_pdf_processing_error(e)


# ==================== ENDPOINTS DE SALUD ====================

@router.get("/health", status_code=200)
async def health_check(
    database: Database = Depends(get_database)
):
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
        is_db_connected = await database.is_connected()
        settings = get_settings()

        if is_db_connected:
            return {
                "status": "healthy",
                "database": "connected",
                "version": settings.app_version
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "version": settings.app_version
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": settings.app_version
            }
        )
